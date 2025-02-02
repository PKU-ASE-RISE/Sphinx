import json
from Agents.utils import get_llm
from pathlib import Path
from infra import UIHierarchy, Element
import xml.etree.ElementTree as ET
import cv2
from LLMs import vlm_base, qwen_vl_max, qwen_vl_max_latest
from infra import Action, swipe_action, click_action, longclick_action, text_action, back_action, restart_action, none_action, stop_action, enter_action, parse_bound
from infra.hierarchy import ACTION_MAP, ActionType
from copy import deepcopy
import re
import time


class ActionParseError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def parse_action_by_id(widgets, action_str: str) -> Action:
    def find_widget_by_id(id: int) -> Element:
        if id >= 0 and id < len(widgets):
            return widgets[id]
        raise ActionParseError(f"Cannot find widget with id {id}")

    action = action_str.split("[")[0].strip()
    match action:
        case "click":
            pattern = r'click \[(\d+)\]'
            elements = re.match(pattern, action_str)
            if elements is None:
                raise ActionParseError(
                    f"Invalid click action. {action_str}")
            elements = elements.groups()
            if len(elements) != 1:
                raise ActionParseError(
                    f"click action must have one interger. {action_str}")
            return click_action(element=find_widget_by_id(int(elements[0])))
        case "longclick":
            pattern = r'longclick \[(\d+)\]'
            elements = re.match(pattern, action_str)
            if elements is None:
                raise ActionParseError(
                    f"Invalid longclick action. {action_str}")
            elements = elements.groups()
            if len(elements) != 1:
                raise ActionParseError(
                    f"longclick action must have one interger. {action_str}")
            return longclick_action(element=find_widget_by_id(int(elements[0])))
        case "text":
            pattern = r'text \[(\d+)\] \[(.*)\]'
            elements = re.match(pattern, action_str)
            if elements is None:
                raise ActionParseError(
                    f"Invalid text action. {action_str}")
            elements = elements.groups()
            if len(elements) != 2:
                raise ActionParseError(
                    f"text action must have one interger and one string. {action_str}")
            return text_action(message=elements[1], element=find_widget_by_id(int(elements[0])))
        case "swipe":
            pattern = r'swipe \[(\d+)\] \[(.*)\]'
            elements = re.match(pattern, action_str)
            if elements is None:
                raise ActionParseError(
                    f"Invalid swipe action. {action_str}")
            elements = elements.groups()
            if len(elements) != 2:
                raise ActionParseError(
                    f"swipe action must have one interger and one string. {action_str}")
            direction = elements[1]
            if direction.startswith("direction="):
                direction = direction.split("=")[1]
            element = find_widget_by_id(int(elements[0]))
            if direction not in ["up", "down", "left", "right"]:
                raise ActionParseError(
                    f"Invalid swipe direction: {direction}. Original action: {action_str}")
            return swipe_action(element=element, direction=direction)
        case "press":
            pattern = r'press \[(.*)\]'
            elements = re.match(pattern, action_str)
            if elements is None:
                raise ActionParseError(
                    f"Invalid press action. {action_str}")
            elements = elements.groups()
            if len(elements) != 1:
                raise ActionParseError(
                    f"press action must have one string. {action_str}")
            action = elements[0]
            match action:
                case "back":
                    return back_action()
                case "restart":
                    return restart_action()
                case "home":
                    return restart_action()
                case "none":
                    return none_action()
                case "stop":
                    return stop_action()
                case "enter":
                    return enter_action()
    raise ActionParseError(f"Invalid action: {action_str}")


def test(action, groundtruth):
    if ACTION_MAP[groundtruth["type"].upper()] != action["action_type"]:
        return False
    if action["action_type"] not in [ActionType.CLICK, ActionType.LONGCLICK, ActionType.SWIPE, ActionType.TEXT]:
        return True
    xmid = (action["element"]._bounds[0] +
            action["element"]._bounds[2]) // 2
    ymid = (action["element"]._bounds[1] +
            action["element"]._bounds[3]) // 2
    gt_bounds = parse_bound(groundtruth["element"]["bounds"])
    if not (xmid >= gt_bounds[0] and xmid <= gt_bounds[2] and ymid >= gt_bounds[1] and ymid <= gt_bounds[3]):
        return False
    if action["action_type"] == ActionType.TEXT and action["message"] != groundtruth["message"]:
        return False
    return True


def test_lowlevel(id, app, llm, observation_mode, instruction, groundtruth, json_path, log_path, fig_path = "tmp.jpg"):
    if json_path.exists():
        with open(json_path) as f:
            action = json.load(f)
        if "action" not in action:
            error_message = action["error"]
            if "invalid" in error_message.lower() or error_message == "list index out of range" or "cannot find widget" in error_message.lower():
                return 0, 1
            else:
                print(f"Error: {error_message}")
                print(id, llm, observation_mode)
                if "ratelimiterror" in error_message.lower() or "retryerror" in error_message.lower() or "not defined" in error_message.lower():
                    json_path.unlink()
                return 0, 0
        action = action["action"]
        if "element" in action:
            action["element"] = Element(action["element"])
        # if test(action, groundtruth) == 0:
        #     print(id)
        return test(action, groundtruth), 1
    # raise NotImplementedError("Not implemented")
    system_prompt = "You are an autonomous intelligent agent tasked with navigating a mobile app. You will be given app-based tasks. These tasks will be accomplished through the use of specific actions you can issue."
    user_prompt = '''
Here's the information you'll have:
The TASK: This is the task you're trying to complete.
The OBSERVATION: This is a simplified representation of the UI screen, providing key information.
The PREVIOUS ACTION: This is the action you just performed. It may be helpful to track your progress.

The actions you can perform fall into several categories:

Touch Screen Actions:
`click [index]`: This action clicks on an element with a specific index.
`longclick [index]`: This action long clicks on an element with a specific index.
`text [index] [content]`: Use this to type the content into the field with index.
`swipe [index] [direction=down|up|left|right]`: swipe an element with a specific index in a specific direction.


Global Navigation Actions:
`press [back]`: Press back button.
`press [restart]`: Press to restart the app.
`press [home]`:  Press to return to the desktop.
`press [none]`: Do nothing but wait for the UI page completely loaded.
`press [stop]`: Issue this action when you believe the task is complete.
`press [enter]`: Press the "Enter" key.

To be successful, it is very important to follow the following rules:
1. You should only issue an action that is valid given the current observation
2. You should only issue one action at a time.
3. You should reason step by step and then issue the next action.
4. Generate the action in the correct format. After step-by-step reasoning, summary with a "In summary, the next action I will perform is" phrase, followed by action inside ``````. For example, "In summary, the next action I will perform is ```text [12] [some text]```".
5. Issue stop action when you think you have achieved the task. Don't generate anything after stop.

'''
    hierarchy_path = Path("lowlevel_tasks") / f"{id}.xml"
    with open(hierarchy_path, "r", encoding="utf-8") as f:
        hierarchy = UIHierarchy(ET.fromstring(f.read()))
    if observation_mode == "tree":
        user_prompt += f"Observation: {hierarchy.dump_widget_tree()}\n"
        user_prompt += f"Task: {instruction}\n"
        if isinstance(llm, vlm_base):
            system_prompt = [system_prompt]
            user_prompt = [user_prompt]
    elif observation_mode == "annotated_image":
        user_prompt += "Observation: The observation of the current app screen is the image provided below, with each actionable element annotated with a bounding box and an index inside the bounding box. The color of the bounding box and the color of the background of the index indicates its action type. red indicates click action, purple indicates longclick action, blue indicates text action, green indicates swipe action.\n"
        user_prompt += f"Task: {instruction}\n"
        image_path = Path("lowlevel_tasks") / f"{id}.png"
        image = cv2.imread(str(image_path))
        annotated_image = hierarchy.dump_annotated_image(image)
        cv2.imwrite(str(fig_path), annotated_image)
        system_prompt = [system_prompt]
        user_prompt = [user_prompt, Path(fig_path)]
    else:
        raise ValueError(f"Invalid observation mode: {observation_mode}")
    # print(system_prompt)
    # print(user_prompt)
    parsed_output = llm([{"role": "system", "content": system_prompt}, {
                        "role": "user", "content": user_prompt}])["parsed_output"]
    if isinstance(llm, qwen_vl_max) or isinstance(llm, qwen_vl_max_latest):
        time.sleep(4)
    
    if isinstance(llm, vlm_base):
        system_prompt = system_prompt[0]
        user_prompt = user_prompt[0]
    
    g = open(log_path, "w", encoding="utf-8")
    g.write("\n".join([str(system_prompt), "=" * 20, str(user_prompt), "=" * 20, parsed_output, "=" * 20]) + "\n")
    print(parsed_output)
    # try:
    action_output = parsed_output.split('```')[-2]
    g.write("\n".join([str(action_output), "=" * 20, str(groundtruth), "=" * 5]) + "\n")
    # except:
    #     action_output = parsed_output.split('`')[-2]
    
    action = parse_action_by_id(hierarchy.widgets(), action_output)
    # print(f"Action: {action}, {action['element']._bounds}")
    if groundtruth["type"] == "input":
        groundtruth["type"] = "text"
    with open(json_path, "w", encoding="utf-8") as f:
        dump_action = deepcopy(action)
        if "element" in dump_action:
            dump_action["element"] = dump_action["element"]._attrib
        json.dump({"action": dump_action}, f, indent=4)
        g.write("\n".join([str(dump_action), "=" * 5, str(test(action, groundtruth))]) + "\n")
        # input()
    return test(action, groundtruth), 1

if __name__ == "__main__":

    configs = [
        {
            "llm": "deepseek",
            "observation_mode": "tree"
        },
        {
            "llm": "gpt4o",
            "observation_mode": "tree"
        },
        {
            "llm": "gpt4",
            "observation_mode": "tree"
        },
        {
            "llm": "gpt4omini",
            "observation_mode": "tree"
        },
        {
            "llm": "llama3",
            "observation_mode": "tree"
        },
        {
            "llm": "llama3_70b",
            "observation_mode": "tree"
        },
        {
            "llm": "qwen_vl_max_latest",
            "observation_mode": "tree"
        },
        {
            "llm": "qwen_vl_plus_latest",
            "observation_mode": "tree"
        },
        {
            "llm": "qwen_vl_max",
            "observation_mode": "tree"
        },
        # {
        #     "llm": "qwen_vl_max_0809",
        #     "observation_mode": "tree"
        # },
        {
            "llm": "qwen_vl_plus",
            "observation_mode": "tree"
        },
        {
            "llm": "llama32_11b",
            "observation_mode": "tree"
        },
        {
            "llm": "gpt4o_vlm",
            "observation_mode": "annotated_image"
        },
        {
            "llm": "gpt4_vlm",
            "observation_mode": "annotated_image"
        },
        { 
            "llm": "gpt4omini_vlm",
            "observation_mode": "annotated_image"
        },
        {
            "llm": "qwen_vl_max_latest",
            "observation_mode": "annotated_image"
        },
        {
            "llm": "qwen_vl_plus_latest",
            "observation_mode": "annotated_image"
        },
        {
            "llm": "qwen_vl_max",
            "observation_mode": "annotated_image"
        },
        {
            "llm": "qwen_vl_plus",
            "observation_mode": "annotated_image"
        },
        {
            "llm": "llama32_11b",
            "observation_mode": "annotated_image"
        }
    ]

    with open("lowlevel_tasks.json", "r", encoding="utf-8") as f:
        lowlevel_tasks = json.load(f)

    for config in configs:
        llm = get_llm(config["llm"])
        observation_mode = config["observation_mode"]
        success = 0
        total = 0
        trace_dir = Path("lowlevel_trace") / config["llm"] / \
            observation_mode
        trace_dir.mkdir(parents=True, exist_ok=True)
        for task in lowlevel_tasks:
            id = task["id"]
            app = task["app"]
            instruction = task["instruction"]
            groundtruth = task["groundtruth"]
            json_path = trace_dir / f"{id}.json"
            log_path = trace_dir / f"{id}.log"
            fig_path = trace_dir / f"{id}.jpg"
            # with open(json_path, encoding="utf-8") as f:
            #     res = json.load(f)
            try:
                a, b = test_lowlevel(id, app, llm,
                                    observation_mode, instruction, groundtruth, json_path, log_path, fig_path)
                success += a
                total += b
                if b == 0:
                    print(id)
            except Exception as e:
                if json_path.exists():
                    continue
                else:
                    file_json = {}
                    file_json["error"] = str(e)
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(file_json, f, indent=4)
            # print(
            #     f"LLM: {config['llm']}, Success rate: {success} / {total} = {success/total if total > 0 else 0}")
            # print(
            #     f"LLM: {config['llm']}, observation_mode: {observation_mode}, Success rate: {success} / {total} = {success/total if total > 0 else 0}")
        print(
            f"LLM: {config['llm']}, observation_mode: {observation_mode}, Success rate: {success} / {total} = {success/total if total > 0 else 0}")
