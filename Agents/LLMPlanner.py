from Agents.Base import AgentBase
from Agents.utils import PlanParsingError, get_llm, update_token_usage, load_llm_planner_prompt, pack_prompt
import re

class AgentLLMPlanner_Text(AgentBase):
    def __init__(self, *args, **kwargs):
        super().__init__()
        if 'llm_name' in kwargs and 'prompt_file' in kwargs and 'instruction' in kwargs \
                and 'action_generation_prompt_file' in kwargs:
            llm_name = kwargs['llm_name']
            instruction = kwargs['instruction']
            invalid_observations = kwargs.get('invalid_observations', None)
            useless_observations = kwargs.get('useless_observations', None)
        else:
            raise ValueError("Both 'llm_name' ,'prompt_file' and 'action_generation_prompt_file' "
                             "must be provided in kwargs")

        self.llm = get_llm(llm_name)
        self.init_prompt, self.action_generation_prompt = load_llm_planner_prompt('text',False)
        self.init_prompt = self.init_prompt.format(instruction=instruction)
        self.action_generation_prompt = self.action_generation_prompt.format(instruction=instruction)
        self.instructions = instruction
        self.observation_history = []
        self.action_history = []
        self.token_usage = {'input': 0, 'output': 0, 'total': 0}

        self.invalid_observations = invalid_observations
        self.useless_observations = useless_observations
        self.high_level_plans = None
        self.now_step = 0
        self.empty_action = 'press [none]'
        self.replan_action = 'press [replan]'

    def act(self, observation):
        
        # high-level planning phase
        if self.high_level_plans is None or self.now_step >= len(self.high_level_plans):
            if self.high_level_plans is None:
                self.observation_history.append(observation)

            prompt = self.init_prompt.format(observation=observation)
            if len(self.action_history) > 0:
                prompt = prompt.format(previous_action=self.action_history[-1])
            else:
                prompt = prompt.format(previous_action="None")
            llm_response = self.llm(pack_prompt(prompt))
            update_token_usage(self.token_usage, llm_response['token_usage'])

            self.high_level_plans = self.parse_high_level_plan(llm_response['parsed_output'])
            for plan in self.high_level_plans:
                print(plan)
            self.now_step = 0
        else:
            add_observation = True
            if add_observation:
                self.observation_history.append(observation)
            else:
                self.observation_history[-1] = self.observation_history[-1] + '\n' + observation

        
        # low-level grounding phase
        print("Next Plan:" + self.high_level_plans[self.now_step])
        prompt = self.action_generation_prompt.format(current_plan=self.high_level_plans[self.now_step])
        llm_response = self.llm(pack_prompt(prompt))
        action = self.parse_action(llm_response['parsed_output'])
        if action == self.replan_action:
            self.high_level_plans = None
            self.now_step = 0
            action = self.empty_action
        self.action_history.append(action)
        update_token_usage(self.token_usage, llm_response['token_usage'])
        self.now_step += 1

        return action

    @staticmethod
    def combine_histories(observation_history, action_history):
        combined_history = []
        min_length = min(len(observation_history),  len(action_history))

        for i in range(min_length):
            combined_history.append(
                f"Observation: {observation_history[i]}\nAction: {action_history[i]}\n")

        if len(observation_history) > min_length:
            combined_history.append(f"Observation: {observation_history[min_length]}\n")

        return ''.join(combined_history)

    def parse_high_level_plan(self, llm_response:str):
        llm_response = llm_response.strip('plan_phrase').strip().split('\n')
        plan_splitter = self.meta_data["plan_splitter"]
        plans = []
        pattern = rf"{plan_splitter[0]}((.|\n)*?){plan_splitter[1]}"
        for line in llm_response:
            match = re.search(pattern, line)
            if match:
                plans.append(match.group(1).strip())
        return plans

class AgentLLMPlanner_IMG(AgentBase):
    def __init__(self, *args, **kwargs):
        super().__init__()
        if 'llm_name' in kwargs and 'prompt_file' in kwargs and 'instruction' in kwargs \
                and 'action_generation_prompt_file' in kwargs:
            llm_name = kwargs['llm_name']
            instruction = kwargs['instruction']
            invalid_observations = kwargs.get('invalid_observations', None)
            useless_observations = kwargs.get('useless_observations', None)
        else:
            raise ValueError("Both 'llm_name' ,'prompt_file' and 'action_generation_prompt_file' "
                             "must be provided in kwargs")

        self.llm = get_llm(llm_name)
        self.init_prompt, self.action_generation_prompt = load_llm_planner_prompt('image',False)
        self.init_prompt = self.init_prompt.format(instruction=instruction)
        self.action_generation_prompt = self.action_generation_prompt.format(instruction=instruction)
        self.instructions = instruction
        self.observation_history = []
        self.action_history = []
        self.token_usage = {'input': 0, 'output': 0, 'total': 0}

        self.invalid_observations = invalid_observations
        self.useless_observations = useless_observations
        self.high_level_plans = None
        self.now_step = 0
        self.empty_action = 'press [none]'
        self.replan_action = 'press [replan]'

    def act(self, observation):
        
        # high-level planning phase
        if self.high_level_plans is None or self.now_step >= len(self.high_level_plans):
            if self.high_level_plans is None:
                self.observation_history.append(observation)

            prompt = self.init_prompt.format(observation=observation)
            if len(self.action_history) > 0:
                prompt = prompt.format(previous_action=self.action_history[-1])
            else:
                prompt = prompt.format(previous_action="None")
            llm_response = self.llm(pack_prompt(prompt))
            update_token_usage(self.token_usage, llm_response['token_usage'])

            self.high_level_plans = self.parse_high_level_plan(llm_response['parsed_output'])
            for plan in self.high_level_plans:
                print(plan)
            self.now_step = 0
        else:
            add_observation = True
            if add_observation:
                self.observation_history.append(observation)
            else:
                self.observation_history[-1] = self.observation_history[-1] + '\n' + observation
            