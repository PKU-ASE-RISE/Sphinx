import json
from pathlib import Path
import cv2
import numpy as np
import matplotlib.pyplot as plt


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
    
    # all_pair = []
    
    for config in configs:
        mode = config["mode"]
        observation_mode = config["observation_mode"]
        trace_dir = Path(f"complete_trace_{mode}") / config["llm"] / observation_mode 
        success_last = 0
        total_last = 0
        success_pre = 0
        total_pre = 0
        success_overall = 0
        total_overall = 0
        for i, task in enumerate(task_info):
            id = task["id"]
            if id > 1000:
                continue
            for app in task["apps"]:
                json_path = trace_dir / f"{id}_{app}.json"
                if not json_path.exists():
                    continue
                with open(json_path, encoding="utf-8") as f:
                    result = json.load(f)
                # for i, x in enumerate(result[:-1]):
                #     all_pair.append(((i + 0.5) / (len(result) - 1), x))
                # total_last += 1
                # success_last += result[-1]
                # total_pre += max(len(result) - 5, 0)
                # success_pre += sum(result[:-5])
                total_last += 1
                success_last += result[-1]
                total_pre += max(len(result) - 1, 0)
                success_pre += sum(result[:-1])
                success_overall += all(result)
                total_overall +=1
            # if i % 20 == 0:
                # print("LLM: ", config["llm"], "Task: ", id, "Success rate: ", success_last, "/", total_last, "=", success_last/total_last if total_last > 0 else 0, "Pre: ", success_pre, "/", total_pre, "=", success_pre/total_pre if total_pre > 0 else 0)
        def format_ratio(label, success, total, num_width, float_format):
            if total > 0:
                ratio = success / total
            else:
                ratio = 0
            return f"{label} {success:>{num_width}}/{total:>{num_width}} = {ratio:{float_format}}"

        str_width = 25
        num_width = 4
        float_format = f":>{num_width}.4f"

        # 使用辅助函数构建 Overall, Last, Pre 字段
        overall_str = format_ratio('Overall:', success_overall, total_overall, num_width, float_format)
        last_str = format_ratio('Last:', success_last, total_last, num_width, float_format)
        pre_str = format_ratio('Pre:', success_pre, total_pre, num_width, float_format)

        output = (
            f"LLM: {config['llm']:<{str_width}}"
            f"Task: {id:<{str_width - 10}}"
            f"Observation mode: {observation_mode:<{str_width - 8}}"
            f"Mode: {mode:<{str_width - 10}}"
            f"{last_str:<{str_width + 5}}"        # 对整体字符串进行对齐
            f"{pre_str:<{str_width + 5}}"           # 对整体字符串进行对齐
            f"{overall_str:<{str_width + 5}}"  # 对整体字符串进行对齐
        )

        print(output)
        # print("LLM: ", config["llm"], "Task: ", id, "Observation mode: ", observation_mode, "Mode: ", mode, 
        #       "Overall: ", success_overall, "/", total_overall, "=", success_overall/total_overall if total_overall > 0 else 0,
        #       "Last: ", success_last, "/", total_last, "=", success_last/total_last if total_last > 0 else 0,
        #       "Pre: ", success_pre, "/", total_pre, "=", success_pre/total_pre if total_pre > 0 else 0)
    
    # # Data preparation for plotting
    # x_vals = [pair[0] for pair in all_pair]
    # y_vals = [pair[1] for pair in all_pair]

    # # Define bins for histogram
    # bins = np.linspace(0, 1, 11)

    # # Calculate success rate for each bin
    # success_rate = []
    # for i in range(len(bins) - 1):
    #     bin_mask = (x_vals >= bins[i]) & (x_vals < bins[i+1])
    #     successes = np.sum(np.array(y_vals)[bin_mask])
    #     total = np.sum(bin_mask)
    #     success_rate.append(successes / total if total > 0 else 0)