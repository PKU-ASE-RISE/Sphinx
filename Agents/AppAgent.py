import re
from Agents.Base import AgentBase
from Agents.utils import get_llm, update_token_usage, load_react_prompt, pack_prompt
from typing import List, Dict, Any
from pathlib import Path
class AgentAppAgent(AgentBase):
    def __init__(self, *args, **kwargs):
        super().__init__()
        if 'llm_name' in kwargs and 'instruction' in kwargs:
            llm_name = kwargs['llm_name']
            instruction = kwargs['instruction']
        else:
            raise ValueError("'llm_name' and 'instruction' must be provided in kwargs")

        self.llm = get_llm(llm_name)
        self.init_prompt,self.meta_data = load_react_prompt(modality='multi-modal', use_demonstrations=False)
        self.init_prompt = self.init_prompt.format(instruction=instruction)
        self.last_action = None
        self.observation_history = []
        self.action_history = []
        self.token_usage = {'input': 0, 'output': 0, 'total': 0}
        print("Agent Initialized Done.")
    def act(self, observation:Dict[str, Any])->str:
        raise NotImplementedError