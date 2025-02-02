import json
from pathlib import Path
import os
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


for config in configs:
    llm = config["llm"]
    observation_mode = config["observation_mode"]
    cnt = 0
    total = 0
    for task in task_info:
        id = task["id"]
        apps = task["apps"]
        if id > 1000:
            continue
        for app in apps:
            trace_dir = Path(".") / "trace" / llm / \
                observation_mode / str(id) / app
            meta_path = trace_dir / "meta.json"
            if not meta_path.exists():
                continue
            with open(meta_path) as f:
                meta = json.load(f)
            message = meta["error_message"]
            if message.startswith("ActionParseError") or message.startswith("ActionParsingError"):
                cnt += 1
                total += 1
            total += meta["length"]
    print(
        f"LLM {llm} observation_mode {observation_mode} format error: {cnt} / {total} = {cnt / total}")

print("=" * 20)


def is_equal_action(action1, action2):
    if action1["action_type"] != action2["action_type"]:
        return False
    if action1["action_type"] in ["NONE", "RESTART", "STOP", "BACK", "ENTER"]:
        return True
    if action1["action_type"] == "TEXT" and action1["message"] != action2["message"]:
        return False
    # print(action1)
    element1 = action1["element"]
    element2 = action2["element"]
    check_attribs = ["resource-id", "class", "text", "content-desc", "bounds"]
    for attrib in check_attribs:
        if element1[attrib] != element2[attrib]:
            return False
    return True


for config in configs:
    llm = config["llm"]
    observation_mode = config["observation_mode"]
    cnt = 0
    total = 0
    for task in task_info:
        id = task["id"]
        apps = task["apps"]
        if id > 1000:
            continue
        for app in apps:
            trace_dir = Path(".") / "trace" / llm / \
                observation_mode / str(id) / app
            action_path = trace_dir / "actions.json"
            meta_path = trace_dir / "meta.json"
            if not meta_path.exists():
                continue
            if not action_path.exists():
                continue
            with open(action_path) as f:
                actions = json.load(f)
            for i in range(1, len(actions)):
                total += 1
                for j in range(0, i):
                    if is_equal_action(actions[j], actions[i]):
                        cnt += 1
                        break
                if i >= 2 and is_equal_action(actions[i], actions[i - 1]) and is_equal_action(actions[i], actions[i - 2]):
                    break
    print(
        f"LLM {llm} observation_mode {observation_mode} action repetition error: {cnt} / {total} = {cnt / total if total > 0 else 0}")
