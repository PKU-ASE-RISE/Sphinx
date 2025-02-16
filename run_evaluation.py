from infra import AndroidController, UIHierarchy, Element, center, parse_bound, MainEvaluator
from infra import ActionType, Action, click_action, longclick_action, text_action, swipe_action, enter_action, back_action, stop_action, none_action, restart_action
from config import apk_info
from pathlib import Path
import subprocess
import json
import cv2
import time
import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict


def TranslateToAction(raw: dict) -> Action:
    match raw["action_type"].lower():
        case "click":
            return click_action(coord=center(parse_bound(raw["element"]["bounds"])) if "element" in raw else raw["coords"][0])
        case "longclick":
            return longclick_action(coord=center(parse_bound(raw["element"]["bounds"])) if "element" in raw else raw["coords"][0])
        case "input" | "text":
            return text_action(raw["message"], coord=center(parse_bound(raw["element"]["bounds"])) if "element" in raw else raw["coords"][0])
        case "swipe":
            return swipe_action(coord_from=center(parse_bound(raw["element"]["bounds"])) if "element" in raw else raw["coords"][0], coord_to=center(parse_bound(raw["element"]["bounds"])) if "element" in raw else raw["coords"][1])
        case "enter":
            return enter_action()
        case "back":
            return back_action()
        case "stop":
            return stop_action()
        case "none":
            return none_action()
        case "restart":
            return restart_action()
        case _:
            print(raw["action_type"])
            raise ValueError("Invalid action type.")


def evaluate(trace_dir: Path, evaluator_path: Path):
    # print("trace_dir=", trace_dir)
    # print("evaluator_path=", evaluator_path)
    evaluator = MainEvaluator(evaluator_path)
    with open(trace_dir / "actions.json", "r", encoding="utf-8") as f:
        actions = json.load(f)
    with open(trace_dir / "activities.json", "r", encoding="utf-8") as f:
        activities = json.load(f)
    activities = list(map(tuple, activities))
    hierarchies = []
    for i in range(len(actions)):
        with open(trace_dir / f"{i}.xml", "r", encoding="utf-8") as f:
            hierarchies.append(UIHierarchy(ET.fromstring(f.read())))
    actions = list(map(TranslateToAction, actions))
    if len(actions) == len(activities) - 1:
        actions.append(stop_action())
        with open(trace_dir / f"{len(actions) - 1}.xml", "r", encoding="utf-8") as f:
            hierarchies.append(UIHierarchy(ET.fromstring(f.read())))
    if len(actions) != len(activities) or len(actions) != len(hierarchies):
        raise ValueError("Invalid trace.")
    result = evaluator.evaluate(hierarchies, actions, activities)
    return result


def evaluate_acp(trace_dir: Path, evaluator_path: Path):
    with open(trace_dir / "actions.json", "r", encoding="utf-8") as f:
        actions = json.load(f)
    with open(trace_dir / "activities.json", "r", encoding="utf-8") as f:
        activities = json.load(f)
    activities = list(map(tuple, activities))
    hierarchies = []
    for i in range(len(actions)):
        with open(trace_dir / f"{i}.xml", "r", encoding="utf-8") as f:
            hierarchies.append(UIHierarchy(ET.fromstring(f.read())))
    actions = list(map(TranslateToAction, actions))
    if len(actions) == len(activities) - 1:
        actions.append(stop_action())
        with open(trace_dir / f"{len(actions) - 1}.xml", "r", encoding="utf-8") as f:
            hierarchies.append(UIHierarchy(ET.fromstring(f.read())))
    if len(actions) != len(activities) or len(actions) != len(hierarchies):
        raise ValueError("Invalid trace.")
    with open(evaluator_path, "r", encoding="utf-8") as f:
        evaluator_configs = json.load(f)
    if len(actions) == len(activities) - 1:
        actions.append(stop_action())
    if len(actions) != len(activities) or len(actions) != len(hierarchies):
        raise ValueError("Invalid trace.")
    result = []
    for evaluator_config in evaluator_configs:
        evaluator = MainEvaluator(evaluator_config=[evaluator_config])
        result.append(evaluator.evaluate(hierarchies, actions, activities))
    if len(result) == 0:
        raise ValueError(f"evaluator is empty {evaluator_path}")
    return sum(result) / len(result)


if __name__ == "__main__":
    configs = [
        # {
        #     "llm": "qwen_vl_max",
        #     "observation_mode": "tree",
        #     "tell_skill": True
        # },
        # {
        #     "llm": "llama3_70b",
        #     "observation_mode": "tree",
        #     "tell_skill": True
        # },
        # {
        #     "llm": "deepseek",
        #     "observation_mode": "tree",
        #     "tell_skill": True
        # },
        # {
        #     "llm": "gpt4o",
        #     "observation_mode": "tree",
        #     "tell_skill": True
        # },
        # {
        #     "llm": "gpt4omini",
        #     "observation_mode": "tree",
        #     "tell_skill": True
        # },
        # {
        #     "llm": "gpt4o_vlm",
        #     "observation_mode": "annotated_image",
        #     "tell_skill": True
        # },
        # {
        #     "llm": "gpt4omini_vlm",
        #     "observation_mode": "annotated_image",
        #     "tell_skill": True
        # },
        {
            "llm": "gpt4o_vlm",
            "observation_mode": "image"
        },
        {
            "llm": "gpt4omini_vlm",
            "observation_mode": "image"
        },
        # {
        #     "llm": "qwen_vl_max",
        #     "observation_mode": "image"
        # },
        # {
        #     "llm": "gpt4omini",
        #     "observation_mode": "text"
        # },
        # {
        #     "llm": "gpt4o",
        #     "observation_mode": "text"
        # },
        # {
        #     "llm": "deepseek",
        #     "observation_mode": "text"
        # },
        # {
        #     "llm": "qwen_vl_max",
        #     "observation_mode": "text"
        # },
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
            "llm": "qwen_vl_plus",
            "observation_mode": "tree"
        },
        {
            "llm": "qwen_vl_max",
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
            "llm": "qwen_vl_plus",
            "observation_mode": "annotated_image"
        },
        {
            "llm": "qwen_vl_max",
            "observation_mode": "annotated_image"
        }
    ]
    with open("task_info.json", "r") as f:
        task_info = json.load(f)
    print("task num", len(task_info))
    for config in configs:
        llm = config["llm"]
        observation_mode = config["observation_mode"]
        tell_skill = config["tell_skill"] if "tell_skill" in config else False
        sr_result = []
        acp_result = []
        token_usage = 0
        for task in task_info:
            id = task["id"]
            apps = task["apps"]
            if id > 1000:
                continue
            for app in apps:
                # try:
                trace_dir = Path(".") / "trace" / llm / \
                    (observation_mode+("_skill" if tell_skill else "")) / \
                    str(id) / app
                evaluator_path = Path(".") / "groundtruth" / \
                    str(id) / app / "evaluator.json"
                success = evaluate(trace_dir, evaluator_path)
                # if success:
                #     print(id, app, "success")
                sr_result.append(success)
                acp_result.append(evaluate_acp(trace_dir, evaluator_path))
                token_path = trace_dir / "token_usage.json"
                with open(token_path, "r") as f:
                    token_usage += json.load(f)["total"]
                # except:
                #     sr_result.append(0)
                #     acp_result.append(0)
        print("=" * 10)
        print("llm:", llm)
        print("observation_mode:", observation_mode +
              ("_skill" if tell_skill else ""))
        print("sr:", sum(sr_result) / len(sr_result))
        print("acp:", sum(acp_result) / len(acp_result))
        print("token_usage:", token_usage)
