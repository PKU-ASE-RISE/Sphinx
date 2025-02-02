import json
from Agents.utils import get_llm
from pathlib import Path
from infra import UIHierarchy, Element
import xml.etree.ElementTree as ET
import cv2
from LLMs import vlm_base, qwen_vl_max, qwen_vl_max_latest
from infra import Action, swipe_action, click_action, longclick_action, text_action, back_action, restart_action, none_action, stop_action, enter_action, parse_bound, get_description, Element
from infra.hierarchy import ACTION_MAP, ActionType
from copy import deepcopy
from typing import List
import re
import numpy as np
import matplotlib.pyplot as plt
import traceback
import time

FINISH_SYSTEM_MESSAGE = "You are an Android UI testing expert helping me write a UI test case.\n" \
        "In our conversation, I will provide you with a list of widgets with texts on the last screen and the testcase you have generated.\n" \
        "Your task is to determine whether the test objective has been completed."
        
GOAL_FINISHED_MESSAGE = "This is a test case description of a particular APP: {target}.\n"\
        "You are trying to perform the task on an APP.\n" \
        "These are the actions we already performed in sequential order: \n{history}\n" \
        "Here is the current screen: \n{screen}\n" \
        "Do you think that we have finished this particular goal: {goal}?\n" \
        "The UI element in current screen maybe not touched. If an necessary element is not touched, the goal is not finished.\n"\
        "If we have finished, say YES, else say NO."

FINISH_SYSTEM_MESSAGE_ACTION = "You are an Android UI testing expert helping me write a UI test case.\n" \
        "In our conversation, I will provide you with the testcase you have generated.\n" \
        "Your task is to determine whether the test objective has been completed."

GOAL_FINISHED_MESSAGE_ACTION = "This is a test case description of a particular APP: {target}.\n"\
        "You are trying to perform the task on an APP.\n" \
        "These are the actions we already performed in sequential order: \n{history}\n" \
        "Do you think that we have finished this particular goal: {goal}?\n" \
        "If we have finished, say YES, else say NO."
        
FINISH_SYSTEM_MESSAGE_IMAGE = "You are an Android UI testing expert helping me write a UI test case.\n" \
        "In our conversation, I will provide you with the last UI screen and the testcase you have generated.\n" \
        "Your task is to determine whether the test objective has been completed."
        
GOAL_FINISHED_MESSAGE_IMAGE = "This is a test case description of a particular APP: {target}.\n"\
        "You are trying to perform the task on an APP.\n" \
        "These are the actions we already performed in sequential order: \n{history}\n" \
        "The observation of the current app screen is the image provided below.\n" \
        "Do you think that we have finished this particular goal: {goal}?\n" \
        "The UI element in current screen maybe not touched. If an necessary element is not touched, the goal is not finished.\n"\
        "If we have finished, say YES, else say NO."
        


def translate_to_action(raw) -> Action:
    if raw["type"] == "back":
        return back_action()
    elif raw["type"] == "stop":
        return stop_action()
    elif raw["type"] == "enter":
        return enter_action()
    else:
        element = Element(raw["element"])
        if raw["type"] == "click":
            return click_action(element=element)
        elif raw["type"] == "longclick":
            return longclick_action(element=element)
        elif raw["type"] == "input":
            return text_action(element=element, message=raw["message"])
        elif raw["type"] == "swipe":
            return swipe_action(element=element)
        else:
            print(raw)
            exit(0)

def history_to_desc(history: List[Action]) -> str:
    descs = ['- ' + get_description(x) for x in history]
    return "\n".join(descs)

def hierarchy_to_desc(hierarchy: UIHierarchy) -> str:
    return str(hierarchy)

def test_complete(hierarchy, actions, image_path, instruction, llm, log_path, mode, observation_mode):
    if observation_mode == "image":
        if mode == "all":
            system_prompt = FINISH_SYSTEM_MESSAGE_IMAGE
            prompt = GOAL_FINISHED_MESSAGE_IMAGE.format(target=instruction, history=history_to_desc(actions), goal=instruction)
            if not isinstance(llm, vlm_base):
                raise ValueError("Invalid LLM to use image observation mode")
            system_prompt = [system_prompt]
            prompt = [prompt, image_path]
    elif observation_mode == "tree":
        if mode == "all":
            system_prompt = FINISH_SYSTEM_MESSAGE
            prompt = GOAL_FINISHED_MESSAGE.format(target=instruction, history=history_to_desc(actions), screen=hierarchy_to_desc(hierarchy), goal=instruction)
            if isinstance(llm, vlm_base):
                system_prompt = [system_prompt]
                prompt = [prompt]
        elif mode == "action":
            system_prompt = FINISH_SYSTEM_MESSAGE_ACTION
            prompt = GOAL_FINISHED_MESSAGE_ACTION.format(target=instruction, history=history_to_desc(actions), goal=instruction)
            if isinstance(llm, vlm_base):
                system_prompt = [system_prompt]
                prompt = [prompt]
        else:
            raise ValueError("Invalid mode")
    else:
        raise ValueError("Invalid observation mode")
    output = llm([{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}])["parsed_output"]
    if isinstance(llm, qwen_vl_max) or isinstance(llm, qwen_vl_max_latest):
        time.sleep(4)
    with open(log_path, "w", encoding="utf-8") as f:
        if isinstance(llm, vlm_base):
            f.write("\n".join([system_prompt[0], "=" * 20, prompt[0], "=" * 20, output]))
        else:
            f.write("\n".join([system_prompt, "=" * 20, prompt, "=" * 20, output]))
    if "yes" in output.lower() and "no" in output.lower():
        if output.lower().rfind("no") > output.lower().rfind("yes"):
            return False
        else:
            return True
    if "yes" in output.lower():
        return True
    if "no" in output.lower():
        return False
    return False
    # raise ValueError("Invalid output")
    
    
def test_complete_testcase(id, app, llm, instruction, trace_dir, mode, observation_mode):
    gt_path = Path("groundtruth") / str(id) / app
    action_path = gt_path / "meta.json"
    json_path = trace_dir / f"{id}_{app}.json"
    (trace_dir / f"{id}_{app}").mkdir(parents=True, exist_ok=True)
    if json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            result = json.load(f)
    else:
        with open(action_path, encoding="utf-8") as f:
            actions = json.load(f)
        actions = [translate_to_action(raw) for raw in actions]
        hierarchies = []
        image_paths = []
        for i in range(len(actions)):
            with open(gt_path / f"{i}.xml", encoding="utf-8") as f:
                hierarchies.append(UIHierarchy(ET.fromstring(f.read())))
            image_paths.append(gt_path / f"{i}.png")
        result = []
        for i in range(len(actions)):
            gt = (i == len(actions) - 1)
            result.append(test_complete(hierarchies[i], actions[:i], image_paths[i], instruction, llm, trace_dir / f"{id}_{app}" / f"{i}.log", mode, observation_mode) == gt)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f)
    return sum(result), len(result)



if __name__ == "__main__":
    configs = [
        {
            "llm": "qwen_vl_max_latest",
            "observation_mode": "tree",
            "mode": "action"
        },
        {
            "llm": "qwen_vl_plus_latest",
            "observation_mode": "tree",
            "mode": "action"
        },
        {
            "llm": "qwen_vl_max",
            "observation_mode": "tree",
            "mode": "action"
        },
        {
            "llm": "qwen_vl_plus",
            "observation_mode": "tree",
            "mode": "action"
        },
        {
            "llm": "deepseek",
            "observation_mode": "tree",
            "mode": "action"
        },
        # {
        #     "llm": "gpt4o",
        #     "observation_mode": "tree",
        #     "mode": "action"
        # },
        # {
        #     "llm": "gpt4",
        #     "observation_mode": "tree",
        #     "mode": "action"
        # },
        # {
        #     "llm": "gpt4omini",
        #     "observation_mode": "tree",
        #     "mode": "action"
        # },
        {
            "llm": "llama3",
            "observation_mode": "tree",
            "mode": "action"
        },
        {
            "llm": "llama3_70b",
            "observation_mode": "tree",
            "mode": "action"
        },
        {
            "llm": "llama32_11b",
            "observation_mode": "tree",
            "mode": "action"
        },
        {
            "llm": "qwen_vl_max_latest",
            "observation_mode": "tree",
            "mode": "all"
        },
        {
            "llm": "qwen_vl_plus_latest",
            "observation_mode": "tree",
            "mode": "all"
        },
        {
            "llm": "qwen_vl_max",
            "observation_mode": "tree",
            "mode": "all"
        },
        {
            "llm": "qwen_vl_plus",
            "observation_mode": "tree",
            "mode": "all"
        },
        {
            "llm": "deepseek",
            "observation_mode": "tree",
            "mode": "all"
        },
        {
            "llm": "gpt4o",
            "observation_mode": "tree",
            "mode": "all"
        },
        {
            "llm": "gpt4",
            "observation_mode": "tree",
            "mode": "all"
        },
        {
            "llm": "gpt4omini",
            "observation_mode": "tree",
            "mode": "all"
        },
        {
            "llm": "llama3",
            "observation_mode": "tree",
            "mode": "all"
        },
        {
            "llm": "llama3_70b",
            "observation_mode": "tree",
            "mode": "all"
        },
        {
            "llm": "llama32_11b",
            "observation_mode": "tree",
            "mode": "all"
        },
        {
            "llm": "llama32_11b",
            "observation_mode": "image",
            "mode": "all"
        },
        {
            "llm": "qwen_vl_max_latest",
            "observation_mode": "image",
            "mode": "all"
        },
        {
            "llm": "qwen_vl_plus_latest",
            "observation_mode": "image",
            "mode": "all"
        },
        {
            "llm": "qwen_vl_max",
            "observation_mode": "image",
            "mode": "all"
        },
        {
            "llm": "qwen_vl_plus",
            "observation_mode": "image",
            "mode": "all"
        },
        {
            "llm": "gpt4o_vlm",
            "observation_mode": "image",
            "mode": "all"
        },
        {
            "llm": "gpt4omini_vlm",
            "observation_mode": "image",
            "mode": "all"
        },
        {
            "llm": "gpt4_vlm",
            "observation_mode": "image",
            "mode": "all"
        },
    ]

    with open("task_info_all.json", "r", encoding="utf-8") as f:
        task_info = json.load(f)
    
    for config in configs:
        llm = get_llm(config["llm"])
        mode = config["mode"]
        observation_mode = config["observation_mode"]
        success = 0
        total = 0
        trace_dir = Path(f"complete_trace_{mode}") / config["llm"] / observation_mode 
        trace_dir.mkdir(parents=True, exist_ok=True)
        for i, task in enumerate(task_info):
            id = task["id"]
            if id < 616:
                continue
            if id > 902:
                continue
            desc = task["description"]
            for app in task["apps"]:
                try:
                    now, cnt = test_complete_testcase(id, app, llm, desc, trace_dir, mode, observation_mode)
                    success += now
                    total += cnt
                except Exception as e:
                    print(f"Task {id} {app} error: {e}")
                    traceback.print_exc()
                    continue
            # if i % 20 == 0:
            #     print("LLM: ", config["llm"], "Task: ", id, "Success rate: ", success, "/", total, "=", success/total if total > 0 else 0)
        print(
            f"LLM: {config['llm']}, Observation Mode: {observation_mode}, Success rate: {success} / {total} = {success/total if total > 0 else 0}")