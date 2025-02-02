from typing import List, Tuple, Union, Any, cast
import xml.etree.ElementTree as ET
import numpy as np
import time
import cv2
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
from dominate import document, tags
import re
import copy

from .observation import ObservationHandler
from .hierarchy import Action, ActionType, parse_from_dict, none_action, back_action, enter_action, restart_action, stop_action, click_action, swipe_action, text_action, longclick_action
from .controller import AndroidController
from .hierarchy import Element, UIHierarchy, is_equal_action
from .util import parse_bound
from .evaluator import MainEvaluator

from .config import apk_info


class ActionParseError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EnvRuntimeError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AndroidEnv():

    def __init__(self, port: str = "emulator-5554", observation_mode: str = 'text', action_mode: str = 'id', max_steps: int = 20, wait_time: float = 2.0, trace_dir: Path = Path("./trace"), reinstall=True):
        self.port = port
        self.observation_mode = observation_mode
        self.action_mode = action_mode
        if self.observation_mode not in ['text', 'tree', 'image', 'annotated_image']:
            raise EnvRuntimeError("Invalid observation mode")
        if self.action_mode not in ['id', 'coordination']:
            raise EnvRuntimeError("Invalid action mode")
        self.reset_finished = False
        self.pkg = None
        self.controller = None
        self.max_steps = max_steps
        self.steps = 0
        self.reinstall = reinstall
        self.observation_handler = ObservationHandler()
        self.last_obs = None
        self.wait_time = wait_time
        self.trace_dir = trace_dir
        self.actions = []
        self.activities = []
        self.hierarchies = []
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        with open("task_info.json", "r", encoding="utf-8") as f:
            self.task_info = json.load(f)

    def _record(self) -> None:
        screenshot = self.last_obs["screen"]
        hierarchy = self.last_obs["hierarchy_str"]
        with open(self.trace_path / f"{self.steps}.xml", "w", encoding="utf-8") as f:
            f.write(hierarchy)
        screenshot.save(self.trace_path / f"{self.steps}.png")
        image = cv2.imread(str(self.trace_path / f"{self.steps}.png"))
        image = self.last_obs["hierarchy"].dump_annotated_image(image)
        cv2.imwrite(
            str(self.trace_path / f"annotated_{self.steps}.png"), image)

    def reset(self, task_id: int, app: str) -> Any:
        if self.controller is not None:
            self.controller.stop_app(self.pkg)
        self.actions = []
        self.activities = []
        self.task_id = task_id
        self.app = app
        self.apk_path = apk_info[self.app]["path"]
        self.pkg = apk_info[self.app]["package"]
        self.username = apk_info[self.app]["username"]
        self.password = apk_info[self.app]["password"]
        self.instruction = next(x["description"]
                                for x in self.task_info if x["id"] == self.task_id)
        self.trace_path = self.trace_dir / str(task_id) / app

        if (self.trace_path / "meta.json").exists():
            raise EnvRuntimeError("This task has already been executed.")

        self.gt_path = Path("./groundtruth") / str(task_id) / app
        self.trace_path.mkdir(parents=True, exist_ok=True)
        self.evaluator = MainEvaluator(self.gt_path / "evaluator.json")
        self.controller = AndroidController(self.port, self.pkg)
        self.controller.device.shell(
            "ime enable com.wparam.nullkeyboard/.NullKeyboard")
        self.controller.device.shell(
            "ime set com.wparam.nullkeyboard/.NullKeyboard")
        if not self.login(self.app):
            raise EnvRuntimeError("Login failed.")
        self.reset_finished = True
        self.last_obs, _ = self.observation_handler.get_observation(
            self.controller)
        self.hierarchies.append(UIHierarchy(
            ET.fromstring(self.last_obs["hierarchy_str"])))
        self.activities.append(self.controller.activity().info())
        self.steps = 0
        self._record()
        return self.observe()

    def login(self, app: str) -> bool:
        if not self.reinstall:
            self.controller.stop_app(self.pkg)
            self.controller.start_app(self.pkg)
            return True

        login_script_path = Path("./login_script") / f"{app}.json"
        login_check_path = Path("./login_check") / f"{app}.json"

        if not login_script_path.exists():
            self.controller.reinstall_app(self.pkg, self.apk_path)
            time.sleep(5)
            # self.controller.device.app_auto_grant_permissions(self.pkg)
            return True

        with open(login_script_path, "r", encoding="utf-8") as f:
            login_script = json.load(f)
        login_actions = [parse_from_dict(action) for action in login_script]
        login_checker = MainEvaluator(login_check_path)

        for _ in range(3):
            self.controller.reinstall_app(self.pkg, self.apk_path)
            time.sleep(5)
            # self.controller.device.app_auto_grant_permissions(self.pkg)
            for action in login_actions:
                self.act(action)
                if action["action_type"] == ActionType.NONE:
                    time.sleep(5)

            activity = self.controller.activity()
            activity = activity.info()
            ui_hierarchy = self.controller.dumpstr()
            ui_hierarchy = UIHierarchy(ET.fromstring(ui_hierarchy))
            if login_checker.evaluate([ui_hierarchy], [None], [activity]):
                return True

        return False

    def get_instruction(self) -> str:
        if not self.reset_finished:
            raise EnvRuntimeError("You need to reset the environment first.")
        return self.instruction

    def act(self, action: Action) -> bool:
        terminated = False
        match action['action_type']:
            case ActionType.NONE:
                pass
            case ActionType.CLICK:
                if "element" in action:
                    if not isinstance(action['element'], Element):
                        raise EnvRuntimeError(
                            "click action element must be an instance of Element.")
                    element = action['element']
                    x, y = element.get_mid_point()
                elif "coords" in action:
                    if len(action['coords']) != 1:
                        raise EnvRuntimeError(
                            "click action must have only one coordinate.")
                    x, y = action['coords'][0]
                else:
                    raise EnvRuntimeError(
                        "click action must have either an element or one coordinate.")
                self.controller.click(x, y)
            case ActionType.SWIPE:
                if "coords" in action:
                    if len(action['coords']) != 2:
                        raise EnvRuntimeError(
                            "swipe action must have two coordinates.")
                    x1, y1 = action['coords'][0]
                    x2, y2 = action['coords'][1]
                    self.controller.swipe(x1, y1, x2, y2)
                elif "element" in action:
                    if not isinstance(action['element'], Element):
                        raise EnvRuntimeError(
                            "swipe action element must be an instance of Element.")
                    element = action['element']
                    direction = action["direction"]
                    x1, y1, x2, y2 = element._bounds
                    if direction == "down":
                        coord_from = ((x1 + x2) // 2, (y1 * 2 + y2) // 3)
                        coord_to = ((x1 + x2) // 2, (y1 + y2 * 2) // 3)
                    elif direction == "up":
                        coord_from = ((x1 + x2) // 2, (y1 + y2 * 2) // 3)
                        coord_to = ((x1 + x2) // 2, (y1 * 2 + y2) // 3)
                    elif direction == "left":
                        coord_from = ((x1 + x2 * 2) // 3, (y1 + y2) // 2)
                        coord_to = ((x1 * 2 + x2) // 3, (y1 + y2) // 2)
                    elif direction == "right":
                        coord_from = ((x1 * 2 + x2) // 3, (y1 + y2) // 2)
                        coord_to = ((x1 + x2 * 2) // 3, (y1 + y2) // 2)
                    self.controller.swipe(*coord_from, *coord_to)
                else:
                    raise EnvRuntimeError(
                        "swipe action must have either an element or two coordinates.")
            case ActionType.TEXT:
                if "message" not in action:
                    raise EnvRuntimeError(
                        "text action must have a message field.")
                if "element" in action:
                    if not isinstance(action['element'], Element):
                        raise EnvRuntimeError(
                            "text action element must be an instance of Element.")
                    element = action['element']
                    x, y = element.get_mid_point()
                elif "coords" in action:
                    if len(action['coords']) != 1:
                        raise EnvRuntimeError(
                            "text action must have only one coordinate.")
                    x, y = action['coords'][0]
                else:
                    raise EnvRuntimeError(
                        "text action must have either an element or one coordinate.")
                self.controller.click(x, y)
                time.sleep(self.wait_time)
                clear = "clear" not in action or action['clear']
                if action["message"] == "{username}":
                    message = self.username
                elif action["message"] == "{password}":
                    message = self.password
                else:
                    message = action["message"]
                self.controller.input(message, clear=clear)
            case ActionType.LONGCLICK:
                if "element" in action:
                    if not isinstance(action['element'], Element):
                        raise EnvRuntimeError(
                            "longclick action element must be an instance of Element.")
                    element = action['element']
                    x, y = element.get_mid_point()
                elif "coords" in action:
                    if len(action['coords']) != 1:
                        raise EnvRuntimeError(
                            "longclick action must have only one coordinate.")
                    x, y = action['coords'][0]
                else:
                    raise EnvRuntimeError(
                        "longclick action must have either an element or one coordinate.")
                self.controller.tap_hold(x, y, 2)
            case ActionType.BACK:
                self.controller.back()
            case ActionType.ENTER:
                self.controller.enter()
            case ActionType.RESTART:
                self.controller.stop_app(self.pkg)
                time.sleep(self.wait_time)
                self.controller.start_app()
            case ActionType.STOP:
                self.controller.stop_app(self.pkg)
                terminated = True
            case _:
                raise EnvRuntimeError("Invalid action type.")
        time.sleep(self.wait_time)
        return terminated

    def observe(self) -> Any:
        if not self.reset_finished:
            raise EnvRuntimeError("You need to reset the environment first.")
        if self.observation_mode == 'text':
            numbered_widgets = self.last_obs["numbered_widgets"]
            numbered_widgets = [
                f"[{i}] {str(widget)}" for i, widget in numbered_widgets.items()]
            return "\n".join(numbered_widgets)
        elif self.observation_mode == 'tree':
            return self.last_obs["hierarchy"].dump_widget_tree()
        elif self.observation_mode == 'image':
            return self.trace_path / f"{self.steps}.png"
        elif self.observation_mode == 'annotated_image':
            return self.trace_path / f"annotated_{self.steps}.png"
        raise NotImplementedError("Only text observation mode is supported.")

    def parse_action_by_id(self, action_str: str) -> Action:
        """_summary_

        Args:
            action_str (str): _description_
            The actions you can perform fall into several categories:

        Touch Screen Actions:
        `click [id]`: This action clicks on an element with a specific id.
        `longclick [id]`: This action long clicks on an element with a specific id.
        `text [id] [content]`: Use this to type the content into the field with id.
        `swipe [id] [direction=down|up|left|right]`: swipe an element with a specific id in a specific direction.

        Global Navigation Actions:
        `press [back]`: Press back button.
        `press [restart]`: Press to restart the app.
        `press [home]`:  Press to return to the desktop.
        `press [none]`: Do nothing but wait for the UI page completely loaded.
        `press [stop]`: Issue this action when you believe the task is complete.
        `press [enter]`: Press the "Enter" key.

        Returns:
            Action:Action

        Exception:
            raise ActionParseError
        """

        def find_widget_by_id(id: int) -> Element:
            for uid, widget in self.last_obs["numbered_widgets"].items():
                if uid == id:
                    return widget
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

    def parse_action_by_coords(self, action_str: str) -> Action:
        """_summary_

        Args:
            action_str (str): _description_
            The actions you can perform fall into several categories:

        Touch Screen Actions:
        `click [x,y]`: This action clicks on a coordination (x,y) on the screen.
        `longclick [x,y]`: This action long clicks on a coordination (x,y) on the screen.
        `text [x,y] [content] [press_enter_after=0|1]`: Use this to type the content into the field with coordination (x,y). By default, the "Enter" key is pressed after typing unless press_enter_after is set to 0.
        `swipe [start_x,start_y] [end_x,end_y]`: swipe from coordination (start_x, start_y) to coordination (end_x, end_y).

        Global Navigation Actions:
        `press [back]`: Press back button.
        `press [restart]`: Press to restart the app.
        `press [home]`:  Press to return to the desktop.
        `press [none]`: Do nothing but wait for the UI page completely loaded.
        `press [stop]`: Issue this action when you believe the task is complete.
        `press [enter]`: Press the "Enter" key.

        Returns:
            Action:Action

        Exception:
            raise ActionParseError
        """

        action_str = action_str.strip()
        action = action_str.split("[")[0].strip()
        match action:
            case "click":
                pattern = r'click \[(\d+),(\d+)\]'
                elements = re.match(pattern, action_str)
                if elements is None:
                    raise ActionParseError(
                        f"Invalid click action. {action_str}")
                elements = elements.groups()
                if len(elements) != 2:
                    raise ActionParseError(
                        f"click action must have two interger. {action_str}")
                return click_action(coord=(int(elements[0]), int(elements[1])))
            case "longclick":
                pattern = r'longclick \[(\d+),(\d+)\]'
                elements = re.match(pattern, action_str)
                if elements is None:
                    raise ActionParseError(
                        f"Invalid longclick action. {action_str}")
                elements = elements.groups()
                if len(elements) != 2:
                    raise ActionParseError(
                        f"longclick action must have two interger. {action_str}")
                return longclick_action(coord=(int(elements[0]), int(elements[1])))
            case "text":
                pattern = r'text \[(\d+),(\d+)\] \[(.*)\]'
                elements = re.match(pattern, action_str)
                if elements is None:
                    raise ActionParseError(
                        f"Invalid text action. {action_str}")
                elements = elements.groups()
                if len(elements) != 3:
                    raise ActionParseError(
                        f"text action must have two interger and one string. {action_str}")
                return text_action(message=elements[2], coord=(int(elements[0]), int(elements[1])))
            case "swipe":
                pattern = r'swipe \[(\d+),(\d+)\] \[(\d+),(\d+)\]'
                elements = re.match(pattern, action_str)
                if elements is None:
                    raise ActionParseError(
                        f"Invalid swipe action. {action_str}")
                elements = elements.groups()
                if len(elements) != 4:
                    raise ActionParseError(
                        f"swipe action must have four interger. {action_str}")
                return swipe_action(coord_from=(int(elements[0]), int(elements[1])), coord_to=(int(elements[2]), int(elements[3])))
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

    def step(self, action_str: str) -> Tuple[Any, float, bool, bool, Any]:
        """
        Executes a step in the environment.

        Args:
            action (Action): The action to be performed in the environment.

        Returns:
            Tuple[Any, float, bool, bool, Any]: A tuple containing the following:
                - The observation after the step.
                - The reward obtained from the step.
                - A boolean indicating whether the environment has terminated.
                - A boolean indicating whether the step was truncated.
                - Any additional information related to the step.
        """

        if not self.reset_finished:
            raise EnvRuntimeError("You need to reset the environment first.")
        if self.action_mode == 'id':
            action = self.parse_action_by_id(action_str)
        elif self.action_mode == 'coordination':
            action = self.parse_action_by_coords(action_str)
        else:
            raise EnvRuntimeError("Invalid action mode.")

        self.actions.append(action)

        terminated = self.act(action)

        self.steps += 1

        if action['action_type'] != ActionType.STOP:
            self.last_obs, terminated_by_observation = self.observation_handler.get_observation(
                self.controller)
            self.hierarchies.append(UIHierarchy(
                ET.fromstring(self.last_obs["hierarchy_str"])))
            self.activities.append(self.controller.activity().info())
            self._record()

        terminated_by_action = len(
            self.actions) >= 3 and is_equal_action(self.actions[-1], self.actions[-2]) and is_equal_action(self.actions[-2], self.actions[-3])
        truncated = self.steps >= self.max_steps
        terminated = terminated or terminated_by_observation or terminated_by_action or truncated

        if terminated:
            reward = self.evaluator.evaluate(self.hierarchies, self.actions + ([stop_action(
            )] if self.actions[-1]["action_type"] != ActionType.STOP else []), self.activities)
            self.dump_meta(reward, "none")
        else:
            reward = 0.0

        return self.observe(), float(reward), terminated, truncated, None

    def dump_meta(self, reward, error_message: str) -> None:
        dump_actions = copy.deepcopy(self.actions)
        for action in dump_actions:
            if "element" in action:
                action['element'] = action['element']._attrib
            action["action_type"] = action["action_type"].name
        with open(self.trace_path / "meta.json", "w", encoding="utf-8") as f:
            json.dump({"success": bool(reward), "length": len(
                self.actions), "error_message": error_message}, f, indent=4)
        with open(self.trace_path / "actions.json", "w", encoding="utf-8") as f:
            json.dump(dump_actions, f, indent=4)
        with open(self.trace_path / "activities.json", "w", encoding="utf-8") as f:
            json.dump(self.activities, f, indent=4)

    def visualize(self, annotate=True) -> None:
        if not self.reset_finished:
            raise EnvRuntimeError("You need to reset the environment first.")
        font_size = 20
        font_name = "arial.ttf"
        font = ImageFont.truetype(font_name, font_size)
        pairs = [(Image.open(self.trace_path / f"{i}.png"), event)
                 for (i, event) in enumerate(self.actions)]
        for i, (img, event) in enumerate(pairs):
            draw = ImageDraw.Draw(img)
            if "element" in event:
                element = event["element"]
                x1, y1, x2, y2 = parse_bound(element["bounds"])
                draw.rectangle([x1, y1, x2, y2], outline="red")
            elif "coords" in event:
                if len(event["coords"]) == 1:
                    x, y = event["coords"][0]
                    draw.line([(x-10, y), (x+10, y)], fill="red", width=2)
                    draw.line([(x, y-10), (x, y+10)], fill="red", width=2)
                else:
                    x1, y1 = event["coords"][0]
                    x2, y2 = event["coords"][1]
                    draw.line([x1, y1, x2, y2], fill="red", width=2)
                    draw.text((x1, y1), "from", fill="red", font=font)
                    draw.text((x2, y2), "to", fill="red", font=font)
            else:
                pass
            if annotate:
                draw.text((10, 10), str(event), fill="red", font=font)
            img.save(self.trace_path / f"visualize_{i}.png")
        doc = document(title="Visualize")
        with doc:
            for i, (_, event) in enumerate(pairs):
                tags.h2(f"Event {i}:")
                tags.img(src=f"visualize_{i}.png")
                tags.p(event.__str__())
        with open(self.trace_path / "visualize.html", "w", encoding="utf-8") as f:
            f.write(doc.render())

    def close(self) -> None:
        if self.controller is not None:
            self.controller.stop_app(self.pkg)
            self.controller = None
            self.reset_finished = False
