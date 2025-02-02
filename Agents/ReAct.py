import re
from LLMs import vlm_base
from Agents.Base import AgentBase
from Agents.utils import get_llm, update_token_usage, load_react_prompt, pack_prompt
from typing import List, Dict, Any
from pathlib import Path


class AgentReAct_Text(AgentBase):
    def __init__(self, *args, **kwargs):
        super().__init__()
        if 'llm_name' in kwargs and 'instruction' in kwargs:
            llm_name = kwargs['llm_name']
            instruction = kwargs['instruction']
        else:
            raise ValueError(
                "'llm_name' and 'instruction' must be provided in kwargs")

        self.llm = get_llm(llm_name)
        self.use_skill = kwargs['use_skill']
        self.init_prompt, self.meta_data = load_react_prompt(
            modality='text', use_demonstrations=False, use_skill=self.use_skill)
        self.instruction = instruction
        self.observation_history = []
        self.action_history = []
        self.token_usage = {'input': 0, 'output': 0, 'total': 0}
        print("Agent Initialized Done.")

    def update_history(self, action: str):
        self.action_history.append(action)

    def act(self, observation: str) -> str:
        self.observation_history.append(observation)

        combined_histories = self.combine_histories(
            self.observation_history, self.action_history)
        # prompt = self.init_prompt + combined_histories[-(6400-len(self.init_prompt)):]
        previous_action = "None" if len(
            self.action_history) == 0 else self.action_history[-1]
        prompt = self.init_prompt.format(
            instruction=self.instruction, observation=observation, previous_action=previous_action)
        if len(self.use_skill) > 0:
            prompt += '\nSKILL:\n' + self.use_skill
        print("=" * 20, "llm input begin", "=" * 20)
        print(prompt)
        print("=" * 20, "llm output begin", "=" * 20)
        if isinstance(self.llm, vlm_base):
            llm_response = self.llm(pack_prompt([prompt]))
        else:
            llm_response = self.llm(pack_prompt(prompt))
        print(llm_response["parsed_output"])
        print("=" * 20, "llm end", "=" * 20)
        update_token_usage(self.token_usage, llm_response['token_usage'])
        action = self.parse_action(llm_response['parsed_output'])
        # action = llm_response['parsed_output'].split('\n')[0].strip(self.meta_data['answer_phrase']).strip()
        return action

    @staticmethod
    def combine_histories(observation_history, action_history):
        combined_history = []
        min_length = min(len(observation_history), len(action_history))

        for i in range(min_length):
            combined_history.append(
                f"Observation: {observation_history[i]}\nAction: {action_history[i]}\n")

        if len(observation_history) > len(action_history):
            combined_history.append(
                f"Observation: {observation_history[-1]}\n")

        return ''.join(combined_history)


class AgentReAct_AnnotatedImage(AgentBase):
    def __init__(self, *args, **kwargs):
        super().__init__()
        if 'llm_name' in kwargs and 'instruction' in kwargs:
            llm_name = kwargs['llm_name']
            instruction = kwargs['instruction']
        else:
            raise ValueError(
                "'llm_name' and 'instruction' must be provided in kwargs")
        self.llm = get_llm(llm_name)
        self.use_skill = kwargs['use_skill']
        self.init_prompt, self.meta_data = load_react_prompt(
            modality='annotated_image', use_demonstrations=False, use_skill=self.use_skill)
        self.instruction = instruction
        self.observation_history = []
        self.action_history = []
        self.token_usage = {'input': 0, 'output': 0, 'total': 0}
        print("Agent Initialized Done.")

    def update_history(self, action: str):
        self.action_history.append(action)

    def act(self, observation: Path) -> str:
        self.observation_history.append(observation)
        combined_histories = self.combine_histories(
            self.observation_history, self.action_history)
        # prompt = self.init_prompt + combined_histories[-(6400-len(self.init_prompt)):]
        previous_action = "None" if len(
            self.action_history) == 0 else self.action_history[-1]
        text_prompt = self.init_prompt.format(
            instruction=self.instruction, previous_action=previous_action)
        if len(self.use_skill) > 0:
            text_prompt += '\nSKILL:\n' + self.use_skill
        print("=" * 20, "llm input begin", "=" * 20)
        print(text_prompt)
        print(observation)
        print("=" * 20, "llm output begin", "=" * 20)
        llm_response = self.llm(pack_prompt([text_prompt, observation]))
        print(llm_response["parsed_output"])
        print("=" * 20, "llm end", "=" * 20)
        update_token_usage(self.token_usage, llm_response['token_usage'])
        action = self.parse_action(llm_response['parsed_output'])
        # action = llm_response['parsed_output'].split('\n')[0].strip(self.meta_data['answer_phrase']).strip()
        # self.action_history.append(action)
        return action

    @staticmethod
    def combine_histories(observation_history, action_history):
        combined_history = []
        min_length = min(len(observation_history), len(action_history))

        for i in range(min_length):
            combined_history.append(
                f"Observation: {observation_history[i]}\nAction: {action_history[i]}\n")

        if len(observation_history) > len(action_history):
            combined_history.append(
                f"Observation: {observation_history[-1]}\n")

        return ''.join(combined_history)


class AgentReAct_IMG(AgentBase):
    def __init__(self, *args, **kwargs):
        # raise NotImplementedError("AgentReAct_IMG is not implemented yet.")
        super().__init__()
        if 'llm_name' in kwargs and 'instruction' in kwargs:
            llm_name = kwargs['llm_name']
            instruction = kwargs['instruction']
        else:
            raise ValueError(
                "'llm_name' and 'instruction' must be provided in kwargs")

        self.llm = get_llm(llm_name)
        self.use_skill = kwargs['use_skill']
        self.init_prompt, self.meta_data = load_react_prompt(
            modality='image', use_demonstrations=False, use_skill=self.use_skill)
        self.instruction = instruction
        self.observation_history = []
        self.action_history = []
        self.token_usage = {'input': 0, 'output': 0, 'total': 0}
        print("Agent Initialized Done.")

    def act(self, observation: Path) -> str:
        # raise NotImplementedError("AgentReAct_IMG is not implemented yet.")
        self.observation_history.append(observation)

        combined_histories = self.combine_histories(
            self.observation_history, self.action_history)
        previous_action = "None" if len(
            self.action_history) == 0 else self.action_history[-1]
        text_prompt = self.init_prompt.format(
            instruction=self.instruction, previous_action=previous_action)
        if len(self.use_skill) > 0:
            text_prompt += '\nSKILL:\n' + self.use_skill
        print("=" * 20, "llm input begin", "=" * 20)
        print(text_prompt)
        print(observation)
        print("=" * 20, "llm output begin", "=" * 20)
        llm_response = self.llm(pack_prompt([text_prompt, observation]))
        print(llm_response["parsed_output"])
        print("=" * 20, "llm end", "=" * 20)
        update_token_usage(self.token_usage, llm_response['token_usage'])
        action = self.parse_action(llm_response['parsed_output'])
        # action = llm_response['parsed_output'].split('\n')[0].strip(self.meta_data['answer_phrase']).strip()
        self.action_history.append(action)
        return action

    def update_history(self, action: str):
        self.action_history.append(action)

    @staticmethod
    def combine_histories(observation_history, action_history):
        # raise NotImplementedError("AgentReAct_MM is not implemented yet.")
        combined_history = []
        min_length = min(len(observation_history), len(action_history))

        for i in range(min_length):
            combined_history.append(
                f"Observation: {observation_history[i]}\nAction: {action_history[i]}\n")

        if len(observation_history) > len(action_history):
            combined_history.append(
                f"Observation: {observation_history[-1]}\n")

        return ''.join(combined_history)


class AgentReAct_MultiModal(AgentBase):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("AgentReAct_MM is not implemented yet.")
        super().__init__()
        if 'llm_name' in kwargs and 'instruction' in kwargs:
            llm_name = kwargs['llm_name']
            instruction = kwargs['instruction']
        else:
            raise ValueError(
                "'llm_name' and 'instruction' must be provided in kwargs")
        self.llm = get_llm(llm_name)
        self.use_skill = kwargs['use_skill']
        self.init_prompt, self.meta_data = load_react_prompt(
            modality='multimodal', use_demonstrations=False, use_skill=self.use_skill)
        self.instruction = instruction
        self.observation_history = []
        self.action_history = []
        self.token_usage = {'input': 0, 'output': 0, 'total': 0}
        print("Agent Initialized Done.")

    def update_history(self, action: str):
        raise NotImplementedError("AgentReAct_MM is not implemented yet.")
        self.action_history.append(action)

    def act(self, observation: Path) -> str:
        raise NotImplementedError("AgentReAct_MM is not implemented yet.")
        self.observation_history.append(observation)
        combined_histories = self.combine_histories(
            self.observation_history, self.action_history)
        # prompt = self.init_prompt + combined_histories[-(6400-len(self.init_prompt)):]
        previous_action = "None" if len(
            self.action_history) == 0 else self.action_history[-1]
        text_prompt = self.init_prompt.format(
            instruction=self.instruction, previous_action=previous_action)
        if len(self.use_skill) > 0:
            text_prompt += '\nSKILL:\n' + self.use_skill
        llm_response = self.llm(pack_prompt([text_prompt, observation]))
        update_token_usage(self.token_usage, llm_response['token_usage'])
        action = self.parse_action(llm_response['parsed_output'])
        # action = llm_response['parsed_output'].split('\n')[0].strip(self.meta_data['answer_phrase']).strip()
        # self.action_history.append(action)
        return action

    @staticmethod
    def combine_histories(observation_history, action_history):
        raise NotImplementedError("AgentReAct_MM is not implemented yet.")
        combined_history = []
        min_length = min(len(observation_history), len(action_history))

        for i in range(min_length):
            combined_history.append(
                f"Observation: {observation_history[i]}\nAction: {action_history[i]}\n")

        if len(observation_history) > len(action_history):
            combined_history.append(
                f"Observation: {observation_history[-1]}\n")

        return ''.join(combined_history)
