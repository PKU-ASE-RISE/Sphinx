import re
from .utils import ActionParsingError
class AgentBase():
    def __init__(self):
        self.meta_data = None

    def act(self, observation):
        raise NotImplementedError
    
    def parse_action(self,llm_response:str)->str:
        # parse action from the response
        action_splitter = self.meta_data["action_splitter"]
        pattern = rf"{action_splitter}((.|\n)*?){action_splitter}"
        llm_response = llm_response.split(self.meta_data['answer_phrase'])[-1].strip()
        print(f'Parsed Action: {llm_response}\n')
        match = re.search(pattern, llm_response)
        if match:
            return match.group(1).strip()
        else:
            raise ActionParsingError(
                f'Cannot find the answer phrase "{self.meta_data["answer_phrase"]}" in "{llm_response}"'
            )
       
