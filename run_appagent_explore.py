from AppAgent import AutoExploration
from pathlib import Path
from infra import AndroidEnv
import argparse
import json


def benchmark_run(idx, app, llm_name, port, task_dir, docs_dir, reinstall=True):
    output_dir = task_dir / str(idx) / app
    meta_path = output_dir / "meta.json"
    try:
        env = AndroidEnv(port=port, observation_mode="text",
                         action_mode="id", trace_dir=task_dir, reinstall=reinstall)
        _ = env.reset(idx, app)
        instruction = env.get_instruction()
        agent = AutoExploration(llm_name, port, app, instruction, docs_dir, task_dir, idx)
        agent.run()
        with open(meta_path, 'w') as f:
            json.dump({"error": None}, f)
    except Exception as e:
        with open(meta_path, 'w') as f:
            json.dump({"error": str(e)}, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run benchmark')
    parser.add_argument('--id', type=int, default=901, help='id of the task')
    parser.add_argument('--app', type=str, default='a51', help='app name')
    parser.add_argument('--llm', type=str,
                        default='gpt4omini_vlm', help='llm name')
    parser.add_argument('--port', type=str,
                        default='emulator-5554', help='port')
    parser.add_argument('--task_dir', type=str,
                        default="./appagent_exploration/round1/gpt4omini_vlm", help='task directory')
    parser.add_argument('--docs_dir', type=str,
                        default="./docs/gpt4omini_vlm", help='docs directory')
    args = parser.parse_args()
    benchmark_run(args.id, args.app, args.llm, args.port, Path(args.task_dir), Path(args.docs_dir))
    # model = "gpt4omini_vlm"
    # task_id = 906
    # task_desc = "Add a new todo named 'Sample Todo' in default list"
    # app = "a21"
    # port = "emulator-5554"

    # agent = AppAgentExec(model, port)
    # agent.run(app, Path("trace_appagent") / model / str(task_id), task_desc)
