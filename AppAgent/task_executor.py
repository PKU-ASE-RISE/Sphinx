import argparse
import ast
import datetime
import json
import os
import re
import sys
import time
from pathlib import Path
from .prompts import task_template, task_template_grid
from .and_controller import list_all_devices, AndroidController, traverse_tree
from .model import parse_explore_rsp, parse_grid_rsp, OpenAIModel
from .utils import print_with_color, draw_bbox_multi, draw_grid


class AppAgentExec:
    def __init__(self, model, port: str):
        self.mllm = OpenAIModel(model)
        self.port = port

    def run(self, app: str, task_dir: Path, task_desc: str, docs_dir: Path, no_doc: bool):

        if not app:
            print_with_color(
                "What is the name of the app you want me to operate?", "blue")
            app = input()
            app = app.replace(" ", "")

        # root_dir = Path(".")
        # app_dir = root_dir / "appagent_doc" / app
        # auto_docs_dir = app_dir / "auto_docs"
        # demo_docs_dir = app_dir / "demo_docs"
        task_dir.mkdir(parents=True, exist_ok=True)

        log_path = task_dir / "log.txt"

        # no_doc = False
        # if not os.path.exists(auto_docs_dir) and not os.path.exists(demo_docs_dir):
        #     print_with_color(f"No documentations found for the app {app}. Do you want to proceed with no docs? Enter y or n",
        #                      "red")
        #     user_input = ""
        #     while user_input != "y" and user_input != "n":
        #         user_input = input().lower()
        #     if user_input == "y":
        #         no_doc = True
        #     else:
        #         sys.exit()
        # elif os.path.exists(auto_docs_dir) and os.path.exists(demo_docs_dir):
        #     print_with_color(f"The app {app} has documentations generated from both autonomous exploration and human "
        #                      f"demonstration. Which one do you want to use? Type 1 or 2.\n1. Autonomous exploration\n2. Human "
        #                      f"Demonstration",
        #                      "blue")
        #     user_input = ""
        #     while user_input != "1" and user_input != "2":
        #         user_input = input()
        #     if user_input == "1":
        #         docs_dir = auto_docs_dir
        #     else:
        #         docs_dir = demo_docs_dir
        # elif os.path.exists(auto_docs_dir):
        #     print_with_color(f"Documentations generated from autonomous exploration were found for the app {app}. The doc base "
        #                      f"is selected automatically.", "yellow")
        #     docs_dir = auto_docs_dir
        # else:
        #     print_with_color(f"Documentations generated from human demonstration were found for the app {app}. The doc base is "
        #                      f"selected automatically.", "yellow")
        #     docs_dir = demo_docs_dir

        # device_list = list_all_devices()
        # if not device_list:
        #     print_with_color("ERROR: No device found!", "red")
        #     sys.exit()
        # print_with_color(
        #     f"List of devices attached:\n{str(device_list)}", "yellow")
        # if len(device_list) == 1:
        #     device = device_list[0]
        #     print_with_color(f"Device selected: {device}", "yellow")
        # else:
        #     print_with_color(
        #         "Please choose the Android device to start demo by entering its ID:", "blue")
        #     device = input()
        controller = AndroidController(self.port)
        width, height = controller.get_device_size()
        if not width and not height:
            print_with_color("ERROR: Invalid device size!", "red")
            sys.exit()
        print_with_color(
            f"Screen resolution of {self.port}: {width}x{height}", "yellow")

        round_count = 0
        last_act = "None"
        task_complete = False
        grid_on = False
        rows, cols = 0, 0
        actions = []
        activities = []

        def area_to_xy(area, subarea):
            area -= 1
            row, col = area // cols, area % cols
            x_0, y_0 = col * (width // cols), row * (height // rows)
            if subarea == "top-left":
                x, y = x_0 + (width // cols) // 4, y_0 + (height // rows) // 4
            elif subarea == "top":
                x, y = x_0 + (width // cols) // 2, y_0 + (height // rows) // 4
            elif subarea == "top-right":
                x, y = x_0 + (width // cols) * 3 // 4, y_0 + \
                    (height // rows) // 4
            elif subarea == "left":
                x, y = x_0 + (width // cols) // 4, y_0 + (height // rows) // 2
            elif subarea == "right":
                x, y = x_0 + (width // cols) * 3 // 4, y_0 + \
                    (height // rows) // 2
            elif subarea == "bottom-left":
                x, y = x_0 + (width // cols) // 4, y_0 + \
                    (height // rows) * 3 // 4
            elif subarea == "bottom":
                x, y = x_0 + (width // cols) // 2, y_0 + \
                    (height // rows) * 3 // 4
            elif subarea == "bottom-right":
                x, y = x_0 + (width // cols) * 3 // 4, y_0 + \
                    (height // rows) * 3 // 4
            else:
                x, y = x_0 + (width // cols) // 2, y_0 + (height // rows) // 2
            return x, y

        while round_count < 20:
            round_count += 1
            print_with_color(f"Round {round_count}", "yellow")
            screenshot_path = controller.get_screenshot(
                f"{round_count}", task_dir)
            xml_path = controller.get_xml(
                f"{round_count}", task_dir)
            activities.append(controller.get_activity())
            if screenshot_path == "ERROR" or xml_path == "ERROR":
                break
            if grid_on:
                rows, cols = draw_grid(screenshot_path, os.path.join(
                    task_dir, f"{round_count}_grid.png"))
                image = os.path.join(
                    task_dir, f"{round_count}_grid.png")
                prompt = task_template_grid
            else:
                clickable_list = []
                focusable_list = []
                traverse_tree(xml_path, clickable_list, "clickable", True)
                traverse_tree(xml_path, focusable_list, "focusable", True)
                elem_list = clickable_list.copy()
                for elem in focusable_list:
                    bbox = elem.bbox
                    center = (bbox[0][0] + bbox[1][0]
                              ) // 2, (bbox[0][1] + bbox[1][1]) // 2
                    close = False
                    for e in clickable_list:
                        bbox = e.bbox
                        center_ = (bbox[0][0] + bbox[1][0]
                                   ) // 2, (bbox[0][1] + bbox[1][1]) // 2
                        dist = (abs(center[0] - center_[0]) ** 2 +
                                abs(center[1] - center_[1]) ** 2) ** 0.5
                        if dist <= 30:
                            close = True
                            break
                    if not close:
                        elem_list.append(elem)
                draw_bbox_multi(screenshot_path, os.path.join(task_dir, f"{round_count}_labeled.png"), elem_list,
                                dark_mode=False)
                image = os.path.join(
                    task_dir, f"{round_count}_labeled.png")
                if no_doc:
                    prompt = re.sub(r"<ui_document>", "",
                                    task_template)
                else:
                    ui_doc = ""
                    for i, elem in enumerate(elem_list):
                        doc_path = os.path.join(docs_dir, f"{elem.uid}.txt")
                        if not os.path.exists(doc_path):
                            continue
                        ui_doc += f"Documentation of UI element labeled with the numeric tag '{i + 1}':\n"
                        doc_content = ast.literal_eval(
                            open(doc_path, "r").read())
                        if doc_content["tap"]:
                            ui_doc += f"This UI element is clickable. {doc_content['tap']}\n\n"
                        if doc_content["text"]:
                            ui_doc += f"This UI element can receive text input. The text input is used for the following " \
                                f"purposes: {doc_content['text']}\n\n"
                        if doc_content["long_press"]:
                            ui_doc += f"This UI element is long clickable. {doc_content['long_press']}\n\n"
                        if doc_content["v_swipe"]:
                            ui_doc += f"This element can be swiped directly without tapping. You can swipe vertically on " \
                                f"this UI element. {doc_content['v_swipe']}\n\n"
                        if doc_content["h_swipe"]:
                            ui_doc += f"This element can be swiped directly without tapping. You can swipe horizontally on " \
                                f"this UI element. {doc_content['h_swipe']}\n\n"
                    print_with_color(
                        f"Documentations retrieved for the current interface:\n{ui_doc}", "magenta")
                    ui_doc = """
                    You also have access to the following documentations that describes the functionalities of UI
                    elements you can interact on the screen. These docs are crucial for you to determine the target of your
                    next action. You should always prioritize these documented elements for interaction:""" + ui_doc
                    prompt = re.sub(r"<ui_document>", ui_doc,
                                    task_template)
            prompt = re.sub(r"<task_description>", task_desc, prompt)
            prompt = re.sub(r"<last_act>", last_act, prompt)
            print_with_color(
                "Thinking about what to do in the next step...", "yellow")
            status, rsp = self.mllm.get_model_response(prompt, [image])

            if status:
                with open(log_path, "a") as logfile:
                    log_item = {"step": round_count, "prompt": prompt, "image": f"{round_count}_labeled.png",
                                "response": rsp}
                    logfile.write(json.dumps(log_item) + "\n")
                if grid_on:
                    res = parse_grid_rsp(rsp)
                else:
                    res = parse_explore_rsp(rsp)
                act_name = res[0]
                if act_name == "FINISH":
                    task_complete = True
                    break
                if act_name == "ERROR":
                    break
                last_act = res[-1]
                res = res[:-1]
                if act_name == "tap":
                    _, area = res
                    tl, br = elem_list[area - 1].bbox
                    x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
                    ret = controller.tap(x, y)
                    actions.append(
                        {
                            "action_type": "CLICK",
                            "element": elem_list[area - 1].attribs,
                        }
                    )
                    if ret == "ERROR":
                        print_with_color("ERROR: tap execution failed", "red")
                        break
                elif act_name == "text":
                    _, area, input_str = res
                    tl, br = elem_list[area - 1].bbox
                    x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
                    ret = controller.tap(x, y)
                    if ret == "ERROR":
                        print_with_color("ERROR: tap execution failed", "red")
                        break
                    time.sleep(2)
                    ret = controller.text(input_str)
                    actions.append(
                        {
                            "action_type": "TEXT",
                            "message": input_str,
                            "clear": False,
                            "element": elem_list[area - 1].attribs,
                        }
                    )
                    if ret == "ERROR":
                        print_with_color("ERROR: text execution failed", "red")
                        break
                elif act_name == "long_press":
                    _, area = res
                    tl, br = elem_list[area - 1].bbox
                    x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
                    ret = controller.long_press(x, y)
                    actions.append(
                        {
                            "action_type": "LONGCLICK",
                            "element": elem_list[area - 1].attribs,
                        }
                    )
                    if ret == "ERROR":
                        print_with_color(
                            "ERROR: long press execution failed", "red")
                        break
                elif act_name == "swipe":
                    _, area, swipe_dir, dist = res
                    tl, br = elem_list[area - 1].bbox
                    x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
                    ret = controller.swipe(x, y, swipe_dir, dist)
                    actions.append(
                        {
                            "action_type": "SWIPE",
                            "direction": swipe_dir,
                            "element": elem_list[area - 1].attribs,
                        }
                    )
                    if ret == "ERROR":
                        print_with_color(
                            "ERROR: swipe execution failed", "red")
                        break
                elif act_name == "grid":
                    grid_on = True
                    actions.append(
                        {
                            "action_type": "NONE"
                        }
                    )
                elif act_name == "tap_grid" or act_name == "long_press_grid":
                    _, area, subarea = res
                    x, y = area_to_xy(area, subarea)
                    if act_name == "tap_grid":
                        ret = controller.tap(x, y)
                        actions.append(
                            {
                                "action_type": "CLICK",
                                "coords": [[x, y]],
                            }
                        )
                        if ret == "ERROR":
                            print_with_color(
                                "ERROR: tap execution failed", "red")
                            break
                    else:
                        ret = controller.long_press(x, y)
                        actions.append(
                            {
                                "action_type": "LONGCLICK",
                                "coords": [[x, y]],
                            }
                        )
                        if ret == "ERROR":
                            print_with_color(
                                "ERROR: tap execution failed", "red")
                            break
                elif act_name == "swipe_grid":
                    _, start_area, start_subarea, end_area, end_subarea = res
                    start_x, start_y = area_to_xy(start_area, start_subarea)
                    end_x, end_y = area_to_xy(end_area, end_subarea)
                    ret = controller.swipe_precise(
                        (start_x, start_y), (end_x, end_y))
                    actions.append(
                        {
                            "action_type": "SWIPE",
                            "coords": [[start_x, start_y], [end_x, end_y]],
                        }
                    )
                    if ret == "ERROR":
                        print_with_color("ERROR: tap execution failed", "red")
                        break
                if act_name != "grid":
                    grid_on = False
                time.sleep(2)
            else:
                print_with_color(rsp, "red")
                break

        if task_complete:
            print_with_color("Task completed successfully", "yellow")
        elif round_count == 20:
            print_with_color(
                "Task finished due to reaching max rounds", "yellow")
        else:
            print_with_color("Task finished unexpectedly", "red")

        round_count += 1
        print_with_color(f"Round {round_count}", "yellow")
        screenshot_path = controller.get_screenshot(
            f"{round_count}", task_dir)
        xml_path = controller.get_xml(
            f"{round_count}", task_dir)
        activities.append(controller.get_activity())
        with open(task_dir / "activities.json", "w") as f:
            json.dump(activities, f, indent=4)
        with open(task_dir / "actions.json", "w") as f:
            json.dump(actions, f, indent=4)
        input_tokens, output_tokens = self.mllm.get_token_usage()
        token_usage = {
            "input": input_tokens,
            "output": output_tokens,
            "total": input_tokens + output_tokens
        }
        with open(os.path.join(task_dir, "token_usage.json"), "w") as f:
            json.dump(token_usage, f)
