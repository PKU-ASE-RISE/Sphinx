from Agents.Base import AgentBase
from Agents.utils import get_llm, update_token_usage, load_reflexion_prompt, pack_prompt
from pathlib import Path

class AgentReflexion_Text(AgentBase):
    def __init__(self, *args, **kwargs):
        super().__init__()
        if 'llm_name' in kwargs and 'prompt_file' in kwargs and 'instruction' in kwargs:
            llm_name = kwargs['llm_name']
            instruction = kwargs['instruction']
        else:
            raise ValueError("Both 'llm_name' and 'prompt_file' must be provided in kwargs")

        self.llm = get_llm(llm_name)
        self.init_prompt,self.reflection_prompt, self.meta_data = load_reflexion_prompt(modality='image', use_demonstrations=False)
        self.init_prompt = self.init_prompt.format(instruction=instruction)
        self.reflection_prompt = self.reflection_prompt.format(instruction=instruction)
        self.observation_history = []
        self.action_history = []
        self.thought_history = []
        self.token_usage = {'input': 0, 'output': 0, 'total': 0}
        self.replan_action = 'press [replan]'
        self.replanned = False

    def act(self, observation:str):
        self.observation_history.append(observation)
        if len(self.action_history) > 0 and not self.replanned:
            # reflection phase
            reflection = self.reflection_prompt.format(observation=self.observation_history[-1],
                                                        previous_action=self.action_history[-1],
                                                        next_observation=observation)
            reflection_response = self.llm(pack_prompt(reflection))
            reflection_result = self.parse_action(reflection_response['parsed_output']).lower()
            if 'yes' not in reflection_result:
                self.replanned = True
                return self.replan_action
            
        # action phase
        self.replanned = False
        prompt = self.init_prompt.format(observation=observation)
        if len(self.action_history) > 0:
            prompt = prompt.format(previous_action=self.action_history[-1])
        else:
            prompt = prompt.format(previous_action="None")
        llm_response = self.llm(pack_prompt(prompt))
        action = self.parse_action(llm_response['parsed_output'])
        self.action_history.append(action)
        update_token_usage(self.token_usage, llm_response['token_usage'])
        return action
    @staticmethod
    def combine_histories(observation_history, action_history, thought_history):
        combined_history = []
        min_length = min(len(observation_history), len(thought_history), len(action_history))

        for i in range(min_length):
            combined_history.append(
                f"Observation: {observation_history[i]}\nThought: {thought_history[i]}\nAction: {action_history[i]}\n")

        if len(observation_history) > min_length:
            combined_history.append(f"Observation: {observation_history[min_length]}\n")

        return ''.join(combined_history)



class AgentReflexion_IMG(AgentBase):
    def __init__(self, *args, **kwargs):
        super().__init__()
        if 'llm_name' in kwargs and 'prompt_file' in kwargs and 'instruction' in kwargs:
            llm_name = kwargs['llm_name']
            instruction = kwargs['instruction']
        else:
            raise ValueError("'llm_name' must be provided in kwargs")

        self.llm = get_llm(llm_name)
        self.init_prompt,self.reflection_prompt, self.meta_data = load_reflexion_prompt(modality='image', use_demonstrations=False)
        self.init_prompt = self.init_prompt.format(instruction=instruction)
        self.reflection_prompt = self.reflection_prompt.format(instruction=instruction)
        self.observation_history = []
        self.action_history = []
        self.thought_history = []
        self.token_usage = {'input': 0, 'output': 0, 'total': 0}
        self.replan_action = 'press [replan]'
        self.replanned = False

    def act(self, observation:Path):
        self.observation_history.append(observation)
        if len(self.action_history) > 0 and not self.replanned:
            # reflection phase
            reflection = self.reflection_prompt.format(previous_action=self.action_history[-1])
            reflection_response = self.llm(pack_prompt([reflection, self.observation_history[-1], observation]))
            reflection_result = self.parse_action(reflection_response['parsed_output']).lower()
            if 'yes' not in reflection_result:
                self.replanned = True
                return self.replan_action
            
        # action phase
        self.replanned = False
        prompt = self.init_prompt
        if len(self.action_history) > 0:
            prompt = prompt.format(previous_action=self.action_history[-1])
        else:
            prompt = prompt.format(previous_action="None")
        llm_response = self.llm(pack_prompt([prompt,observation]))
        action = self.parse_action(llm_response['parsed_output'])
        self.action_history.append(action)
        update_token_usage(self.token_usage, llm_response['token_usage'])
        return action
    
    @staticmethod
    def combine_histories(observation_history, action_history, thought_history):
        combined_history = []
        min_length = min(len(observation_history), len(thought_history), len(action_history))

        for i in range(min_length):
            combined_history.append(
                f"Observation: {observation_history[i]}\nThought: {thought_history[i]}\nAction: {action_history[i]}\n")

        if len(observation_history) > min_length:
            combined_history.append(f"Observation: {observation_history[min_length]}\n")

        return ''.join(combined_history)



class AgentReflexion_MultiModal(AgentBase):
    def __init__(self, *args, **kwargs):
        super().__init__()
        if 'llm_name' in kwargs and 'prompt_file' in kwargs and 'instruction' in kwargs:
            llm_name = kwargs['llm_name']
            instruction = kwargs['instruction']
        else:
            raise ValueError("'llm_name' must be provided in kwargs")

        self.llm = get_llm(llm_name)
        self.init_prompt,self.reflection_prompt, self.meta_data = load_reflexion_prompt(modality='multimodal', use_demonstrations=False)
        self.init_prompt = self.init_prompt.format(instruction=instruction)
        self.reflection_prompt = self.reflection_prompt.format(instruction=instruction)
        self.observation_history = []
        self.action_history = []
        self.thought_history = []
        self.token_usage = {'input': 0, 'output': 0, 'total': 0}
        self.replan_action = 'press [replan]'
        self.replanned = False

    def act(self, observation:Path):
        self.observation_history.append(observation)
        if len(self.action_history) > 0 and not self.replanned:
            # reflection phase
            reflection = self.reflection_prompt.format(previous_action=self.action_history[-1])
            reflection_response = self.llm(pack_prompt([reflection, self.observation_history[-1], observation]))
            reflection_result = self.parse_action(reflection_response['parsed_output']).lower()
            if 'yes' not in reflection_result:
                self.replanned = True
                return self.replan_action
            
        # action phase
        self.replanned = False
        prompt = self.init_prompt
        if len(self.action_history) > 0:
            prompt = prompt.format(previous_action=self.action_history[-1])
        else:
            prompt = prompt.format(previous_action="None")
        llm_response = self.llm(pack_prompt([prompt,observation]))
        action = self.parse_action(llm_response['parsed_output'])
        self.action_history.append(action)
        update_token_usage(self.token_usage, llm_response['token_usage'])
        return action
    
    @staticmethod
    def combine_histories(observation_history, action_history, thought_history):
        combined_history = []
        min_length = min(len(observation_history), len(thought_history), len(action_history))

        for i in range(min_length):
            combined_history.append(
                f"Observation: {observation_history[i]}\nThought: {thought_history[i]}\nAction: {action_history[i]}\n")

        if len(observation_history) > min_length:
            combined_history.append(f"Observation: {observation_history[min_length]}\n")

        return ''.join(combined_history)

