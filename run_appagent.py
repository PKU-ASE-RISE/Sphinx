from AppAgent import AppAgentExec
from pathlib import Path
from infra import AndroidEnv
import argparse
import json


def benchmark_run(idx, app, llm_name, port, trace_dir, docs_dir, reinstall=True):
    output_dir = trace_dir / str(idx) / app
    meta_path = output_dir / "meta.json"
    try:
        env = AndroidEnv(port=port, observation_mode="text",
                         action_mode="id", trace_dir=trace_dir, reinstall=reinstall)
        _ = env.reset(idx, app)
        instruction = env.get_instruction()
        agent = AppAgentExec(llm_name, port)
        agent.run(app, trace_dir / str(idx) / app, instruction, docs_dir, False if docs_dir != None else True)
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
    parser.add_argument('--trace_dir', type=str,
                        default="./trace_appagent_round1", help='trace directory')
    parser.add_argument('--docs_dir', type=str,
                        default="None", help='trace directory')
    args = parser.parse_args()
    benchmark_run(args.id, args.app, args.llm, args.port, Path(args.trace_dir), Path(args.docs_dir) if args.docs_dir != "None" else None)
    # model = "gpt4omini_vlm"
    # task_id = 906
    # task_desc = "Add a new todo named 'Sample Todo' in default list"
    # app = "a21"
    # port = "emulator-5554"

    # agent = AppAgentExec(model, port)
    # agent.run(app, Path("trace_appagent") / model / str(task_id), task_desc)
