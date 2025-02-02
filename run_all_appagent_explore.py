import json
import time
import random
from pathlib import Path
import subprocess
import multiprocessing


def split_tasks(tasks, emulator_num):
    apps = list(set([task["app"] for task in tasks]))
    split_tasks = [[] for i in range(emulator_num)]
    for app in apps:
        min_index = min(range(len(split_tasks)),
                        key=lambda i: len(split_tasks[i]))
        for task in tasks:
            if task["app"] != app:
                continue
            split_tasks[min_index].append(task)
    return split_tasks


def get_modality_and_action_mode(observation_mode):
    if observation_mode == "text":
        modality = "text"
        action_mode = "id"
    elif observation_mode == "tree":
        modality = "text"
        action_mode = "id"
    elif observation_mode == "annotated_image":
        modality = "annotated_image"
        action_mode = "id"
    elif observation_mode == "image":
        modality = "image"
        action_mode = "coordination"
    else:
        raise ValueError("Invalid observation mode")
    return modality, action_mode


class Device:

    def __init__(self, port: str, task_list):
        self.port = port
        self.tasks = task_list

    def run(self):
        time_to_sleep = (int(self.port[9:]) - 5554) / 2
        time.sleep(time_to_sleep)
        random.shuffle(self.tasks)
        for i, task in enumerate(self.tasks):
            id = task["id"]
            app = task["app"]
            observation_mode = task["observation_mode"]
            llm = task["llm"]
            tell_skill = task["tell_skill"]
            modality, action_mode = get_modality_and_action_mode(
                observation_mode)
            trace_dir = Path("./appagent_exploration/round1") / llm
            docs_dir = Path("./docs") / llm
            print("=" * 20, self.port, "running", str(i)+"-th", "of", len(self.tasks), "tasks", "=" * 20, "\n",
                  "Running task", task["id"], "on app", task["app"], "with llm",
                  task["llm"], "\n",
                  "Save to dir:", trace_dir / str(task["id"]) / task["app"])
            cmdline = ["python", "run_appagent_explore.py", "--id", str(id), "--app", app, "--llm", llm, "--port",
                       self.port, "--task_dir", trace_dir, "--docs_dir", docs_dir]
            if tell_skill:
                cmdline.append("--tell_skill")
            subprocess.run(cmdline)


def run_device(device: Device):
    device.run()


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
        # {
        #     "llm": "gpt4o_vlm",
        #     "observation_mode": "image"
        # },
        # {
        #     "llm": "gpt4omini_vlm",
        #     "observation_mode": "image"
        # },
        # {
        #     "llm": "qwen_vl_max",
        #     "observation_mode": "image"
        # }
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
        # {
        #     "llm": "deepseek",
        #     "observation_mode": "tree"
        # },
        # {
        #     "llm": "gpt4o",
        #     "observation_mode": "tree"
        # },
        # {
        #     "llm": "gpt4",
        #     "observation_mode": "tree"
        # },
        # {
        #     "llm": "gpt4omini",
        #     "observation_mode": "tree"
        # },
        # {
        #     "llm": "llama3",
        #     "observation_mode": "tree"
        # },
        # {
        #     "llm": "llama3_70b",
        #     "observation_mode": "tree"
        # },
        # {
        #     "llm": "qwen_vl_plus",
        #     "observation_mode": "tree"
        # },
        # {
        #     "llm": "qwen_vl_max",
        #     "observation_mode": "tree"
        # },
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
        # {
        #     "llm": "qwen_vl_plus",
        #     "observation_mode": "annotated_image"
        # },
        # {
        #     "llm": "qwen_vl_max",
        #     "observation_mode": "annotated_image"
        # }
    ]
    devices = [
        "emulator-5554",
        "emulator-5556",
        "emulator-5558",
        "emulator-5560",
        # "emulator-5562",
        # "emulator-5564",
        # "emulator-5566",
        # "emulator-5568"
    ]
    tasks = []
    with open("task_info.json", "r") as f:
        task_info = json.load(f)
        
    for task in task_info:
        if task["id"] > 1000:
            continue
        for app in task["apps"]:
            for config in configs:
                observation_mode = config["observation_mode"]
                llm = config["llm"]
                tell_skill = config["tell_skill"] if "tell_skill" in config else False
                id = task["id"]
                trace_dir = Path("./appagent_exploration/round1") / llm
                meta_path = trace_dir / str(id) / app / "meta.json"
                action_path = trace_dir / str(id) / app / "actions.json"
                if action_path.exists():
                    continue
                if meta_path.exists():
                    # print(meta_path)
                    with open(meta_path) as f:
                        meta = json.load(f)
                    if meta["error"] == None:
                        continue
                    if meta["error"].startswith("RetryError"):
                        meta_path.unlink()
                        pass
                    elif meta["error"].startswith("This task"):
                        meta_path.unlink()
                        pass
                    elif meta["error"].startswith("HTTP request failed"):
                        meta_path.unlink()
                        pass
                    elif "Max retries exceeded" in meta["error"]:
                        meta_path.unlink()
                        pass
                    else:
                        print(meta["error"])
                        continue
                tasks.append({
                    "id": id,
                    "app": app,
                    "llm": llm,
                    "observation_mode": observation_mode,
                    "tell_skill": tell_skill
                })
    # print(len(tasks))
    # exit(0)
    split_tasks = split_tasks(tasks, len(devices))
    print(split_tasks)
    print([len(x) for x in split_tasks])
    devices = [Device(x, y) for x, y in zip(devices, split_tasks)]

    with multiprocessing.Pool(processes=len(devices)) as pool:
        pool.map(run_device, devices)
