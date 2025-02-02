import sys
import os
import requests
import re
import argparse
import json
import traceback
from pathlib import Path

from Agents.GetAgent import get_agent
from infra import AndroidEnv, get_description


invalid_observations = ['Invalid action!']
useless_observations = ['OK.', 'You have clicked']


total_token_usage = {'input': 0, 'output': 0, 'total': 0}


def benchmark_run(idx, app, agent_name, modality, llm_name, port, observation_mode, action_mode, to_print=True, trace_dir=Path("./trace"), output_to_log=True, catch=True, reinstall=True, use_skill=""):
    global total_token_usage
    # env init
    env = AndroidEnv(port=port, observation_mode=observation_mode,
                     action_mode=action_mode, trace_dir=trace_dir, reinstall=reinstall)
    observation = env.reset(idx, app)
    instruction = env.get_instruction()
    log_path = env.trace_path / "log.txt"
    # print(output_to_log)
    with open(log_path, 'w', encoding="utf-8") as f:
        stdout = sys.stdout
        if output_to_log:
            sys.stdout = f
        print(f"Observation: {observation}\n")

        agent = get_agent(agent_name, modality, llm_name,
                          instruction=instruction, use_skill=use_skill)
        if not catch:
            print("do not catch exception")
            for _ in range(env.max_steps):
                action = agent.act(observation)
                res = env.step(action)
                last_action_desc = get_description(
                    env.actions[-1]) if action_mode == "id" else action
                agent.update_history(last_action_desc)
                observation = res[0]

                if to_print:
                    print(f'Observation: {observation}')
                    sys.stdout.flush()

                if res[2]:
                    break
        else:
            print("catch exception")
            try:
                for _ in range(env.max_steps):
                    action = agent.act(observation)
                    res = env.step(action)
                    last_action_desc = get_description(
                        env.actions[-1]) if action_mode == "id" else action
                    agent.update_history(last_action_desc)
                    observation = res[0]

                    if to_print:
                        print(f'Observation: {observation}')
                        sys.stdout.flush()

                    if res[2]:
                        break
            except Exception as e:
                tb_str = traceback.format_exc()
                env.dump_meta(0, type(e).__name__ + ": " +
                              str(e) + "\n\n" + tb_str)

        total_token_usage['input'] += agent.token_usage['input']
        total_token_usage['output'] += agent.token_usage['output']
        total_token_usage['total'] += agent.token_usage['total']
        print("Total Token Usage: ")
        print(
            f"input: {total_token_usage['input']}, output: {total_token_usage['output']}, total: {total_token_usage['total']}")

        token_path = env.trace_path / "token_usage.json"
        env.controller.device.app_stop_all()
        if reinstall:
            env.controller.device.app_uninstall_all(
                excludes=["com.wparam.nullkeyboard"])
        env.close()
        with open(token_path, 'w') as f:
            json.dump(agent.token_usage, f)
        sys.stdout = stdout

    return 0


def skill_extract_from_gt(id, app):
    path = Path(".") / "groundtruth" / f"{id}" / f"{app}" / "skills.json"
    with open(path, encoding="utf-8") as fp:
        skills = json.load(fp)

    return '\n'.join([f"{i+1}. {x['name']}" for i, x in enumerate(skills)])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run benchmark')
    parser.add_argument('--id', type=int, default=901, help='id of the task')
    parser.add_argument('--app', type=str, default='a51', help='app name')
    parser.add_argument('--agent', type=str,
                        default='ReAct', help='agent name')
    parser.add_argument('--tell_skill',  dest="tell_skill",
                        action="store_true", help='whether to tell agent skill info')
    parser.add_argument('--modality', type=str,
                        default='text', help='modality')
    parser.add_argument('--llm', type=str,
                        default='gpt4omini', help='llm name')
    parser.add_argument('--port', type=str,
                        default='emulator-5554', help='port')
    parser.add_argument('--observation_mode', type=str,
                        default='tree', help='observation mode')
    parser.add_argument('--action_mode', type=str,
                        default='id', help='action mode')
    parser.add_argument('--trace_dir', type=str,
                        default="./trace", help='trace directory')
    parser.add_argument('--print', dest="to_print",
                        action="store_true", help='print observation')
    parser.add_argument('--stdout', dest="log",
                        action="store_false", help='output to stdout')
    parser.add_argument('--notcatch', dest="catch",
                        action="store_false", help='not catch exception')
    parser.add_argument('--notreinstall', dest="reinstall",
                        action="store_false", help="not reinstall but stop and start directly")

    args = parser.parse_args()
    benchmark_run(args.id, args.app, args.agent, args.modality, args.llm, args.port, args.observation_mode,
                  args.action_mode, args.to_print, Path(
                      args.trace_dir), args.log, args.catch, args.reinstall,
                  skill_extract_from_gt(args.id, args.app) if args.tell_skill else "")
