import argparse
import ast
import datetime
import json
import os
import re
import sys
import time

from .prompts import self_explore_reflect_template, self_explore_task_template
from .and_controller import list_all_devices, AndroidController, traverse_tree
from .model import parse_explore_rsp, parse_reflect_rsp, OpenAIModel
from .utils import print_with_color, draw_bbox_multi

class AutoExploration:
    def __init__(self, model, port: str, app: str, task_desc: str, docs_dir: str, task_dir: str, task_id: int):
        # docs_dir must be like: docs/gpt4omini_vlm
        # task_dir must be like: appagent_exploration/round1/gpt4omini_vlm
        self.mllm = OpenAIModel(model)
        self.port = port
        self.app = app
        self.task_desc = task_desc
        self.docs_dir = os.path.join(docs_dir, app)
        self.task_dir = os.path.join(task_dir, str(task_id), app)
        self.explore_log_path = os.path.join(self.task_dir, f"log_explore.txt")
        self.reflect_log_path = os.path.join(self.task_dir, f"log_reflect.txt")
        if not os.path.exists(self.docs_dir):
            os.makedirs(self.docs_dir)
        if not os.path.exists(self.task_dir):
            os.makedirs(self.task_dir)
        
    def run(self):
        controller = AndroidController(self.port)
        width, height = controller.get_device_size()
        if not width and not height:
            print_with_color("ERROR: Invalid device size!", "red")
            sys.exit()
        print_with_color(f"Screen resolution of {self.port}: {width}x{height}", "yellow")
        task_desc = self.task_desc

        round_count = 0
        doc_count = 0
        useless_list = set()
        last_act = "None"
        task_complete = False
        input_tokens = 0
        output_tokens = 0
        while round_count < 20:
            round_count += 1
            print_with_color(f"Round {round_count}", "yellow")
            screenshot_before = controller.get_screenshot(f"{round_count}_before", self.task_dir)
            xml_path = controller.get_xml(f"{round_count}", self.task_dir)
            if screenshot_before == "ERROR" or xml_path == "ERROR":
                break
            clickable_list = []
            focusable_list = []
            traverse_tree(xml_path, clickable_list, "clickable", True)
            traverse_tree(xml_path, focusable_list, "focusable", True)
            elem_list = []
            for elem in clickable_list:
                if elem.uid in useless_list:
                    continue
                elem_list.append(elem)
            for elem in focusable_list:
                if elem.uid in useless_list:
                    continue
                bbox = elem.bbox
                center = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
                close = False
                for e in clickable_list:
                    bbox = e.bbox
                    center_ = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
                    dist = (abs(center[0] - center_[0]) ** 2 + abs(center[1] - center_[1]) ** 2) ** 0.5
                    if dist <= 30:
                        close = True
                        break
                if not close:
                    elem_list.append(elem)
            draw_bbox_multi(screenshot_before, os.path.join(self.task_dir, f"{round_count}_before_labeled.png"), elem_list,
                            dark_mode=False)

            prompt = re.sub(r"<task_description>", task_desc, self_explore_task_template)
            prompt = re.sub(r"<last_act>", last_act, prompt)
            base64_img_before = os.path.join(self.task_dir, f"{round_count}_before_labeled.png")
            print_with_color("Thinking about what to do in the next step...", "yellow")
            status, rsp = self.mllm.get_model_response(prompt, [base64_img_before])

            if status:
                with open(self.explore_log_path, "a") as logfile:
                    log_item = {"step": round_count, "prompt": prompt, "image": f"{round_count}_before_labeled.png",
                                "response": rsp}
                    logfile.write(json.dumps(log_item) + "\n")
                res = parse_explore_rsp(rsp)
                act_name = res[0]
                last_act = res[-1]
                res = res[:-1]
                if act_name == "FINISH":
                    task_complete = True
                    break
                if act_name == "tap":
                    _, area = res
                    tl, br = elem_list[area - 1].bbox
                    x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
                    ret = controller.tap(x, y)
                    if ret == "ERROR":
                        print_with_color("ERROR: tap execution failed", "red")
                        break
                elif act_name == "text":
                    _, area, input_str = res
                    ret = controller.text(input_str)
                    if ret == "ERROR":
                        print_with_color("ERROR: text execution failed", "red")
                        break
                elif act_name == "long_press":
                    _, area = res
                    tl, br = elem_list[area - 1].bbox
                    x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
                    ret = controller.long_press(x, y)
                    if ret == "ERROR":
                        print_with_color("ERROR: long press execution failed", "red")
                        break
                elif act_name == "swipe":
                    _, area, swipe_dir, dist = res
                    tl, br = elem_list[area - 1].bbox
                    x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
                    ret = controller.swipe(x, y, swipe_dir, dist)
                    if ret == "ERROR":
                        print_with_color("ERROR: swipe execution failed", "red")
                        break
                else:
                    break
                time.sleep(5)
            else:
                print_with_color(rsp, "red")
                break

            screenshot_after = controller.get_screenshot(f"{round_count}_after", self.task_dir)
            if screenshot_after == "ERROR":
                break
            draw_bbox_multi(screenshot_after, os.path.join(self.task_dir, f"{round_count}_after_labeled.png"), elem_list,
                            dark_mode=False)
            base64_img_after = os.path.join(self.task_dir, f"{round_count}_after_labeled.png")

            if act_name == "tap":
                prompt = re.sub(r"<action>", "tapping", self_explore_reflect_template)
            elif act_name == "text":
                continue
            elif act_name == "long_press":
                prompt = re.sub(r"<action>", "long pressing", self_explore_reflect_template)
            elif act_name == "swipe":
                swipe_dir = res[2]
                if swipe_dir == "up" or swipe_dir == "down":
                    act_name = "v_swipe"
                elif swipe_dir == "left" or swipe_dir == "right":
                    act_name = "h_swipe"
                prompt = re.sub(r"<action>", "swiping", self_explore_reflect_template)
            else:
                print_with_color("ERROR: Undefined act!", "red")
                break
            prompt = re.sub(r"<ui_element>", str(area), prompt)
            prompt = re.sub(r"<task_desc>", task_desc, prompt)
            prompt = re.sub(r"<last_act>", last_act, prompt)

            print_with_color("Reflecting on my previous action...", "yellow")
            status, rsp = self.mllm.get_model_response(prompt, [base64_img_before, base64_img_after])
            if status:
                resource_id = elem_list[int(area) - 1].uid
                with open(self.reflect_log_path, "a") as logfile:
                    log_item = {"step": round_count, "prompt": prompt, "image_before": f"{round_count}_before_labeled.png",
                                "image_after": f"{round_count}_after.png", "response": rsp}
                    logfile.write(json.dumps(log_item) + "\n")
                res = parse_reflect_rsp(rsp)
                decision = res[0]
                if decision == "ERROR":
                    break
                if decision == "INEFFECTIVE":
                    useless_list.add(resource_id)
                    last_act = "None"
                elif decision == "BACK" or decision == "CONTINUE" or decision == "SUCCESS":
                    if decision == "BACK" or decision == "CONTINUE":
                        useless_list.add(resource_id)
                        last_act = "None"
                        if decision == "BACK":
                            ret = controller.back()
                            if ret == "ERROR":
                                print_with_color("ERROR: back execution failed", "red")
                                break
                    doc = res[-1]
                    doc_name = resource_id + ".txt"
                    doc_path = os.path.join(self.docs_dir, doc_name)
                    if os.path.exists(doc_path):
                        doc_content = ast.literal_eval(open(doc_path).read())
                        if doc_content[act_name]:
                            print_with_color(f"Documentation for the element {resource_id} already exists.", "yellow")
                            continue
                    else:
                        doc_content = {
                            "tap": "",
                            "text": "",
                            "v_swipe": "",
                            "h_swipe": "",
                            "long_press": ""
                        }
                    doc_content[act_name] = doc
                    with open(doc_path, "w") as outfile:
                        outfile.write(str(doc_content))
                    doc_count += 1
                    print_with_color(f"Documentation generated and saved to {doc_path}", "yellow")
                else:
                    print_with_color(f"ERROR: Undefined decision! {decision}", "red")
                    break
            else:
                print_with_color(rsp["error"]["message"], "red")
                break
            time.sleep(5)
        
        input_tokens, output_tokens = self.mllm.get_token_usage()
        token_usage = {
            "input": input_tokens,
            "output": output_tokens,
            "total": input_tokens + output_tokens
        }
        with open(os.path.join(self.task_dir, "token_usage.json"), "w") as f:
            json.dump(token_usage, f)
        
        if task_complete:
            print_with_color(f"Autonomous exploration completed successfully. {doc_count} docs generated.", "yellow")
        elif round_count == 20:
            print_with_color(f"Autonomous exploration finished due to reaching max rounds. {doc_count} docs generated.",
                            "yellow")
        else:
            print_with_color(f"Autonomous exploration finished unexpectedly. {doc_count} docs generated.", "red")
