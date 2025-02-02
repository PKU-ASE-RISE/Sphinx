from typing import List, Dict, Union, Any
from pathlib import Path
from .Base import OpenAIFormatLLM
class mistral(OpenAIFormatLLM):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        assert len(prompt) > 0, "prompt should not be empty"
        for (i, p) in enumerate(prompt):
            assert "role" in p, "role key not found in prompt"
            assert "content" in p, "content key not found in prompt"
            assert p["role"] in ["assistant",
                                 "user"] or (p["role"] == "system" and i == 0)
        new_prompt = []
        for p in prompt:
            if len(new_prompt) == 0:
                new_prompt.append(p)
                if new_prompt[-1]["role"] == "system":
                    new_prompt[-1]["role"] = "user"
            elif new_prompt[-1]["role"] == p["role"]:
                new_prompt[-1]["content"] += "\n\n" + p["content"]
            else:
                new_prompt.append(p)
        return super().call(new_prompt)

class mistral7b(mistral):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base = "http://10.129.165.103:8002/v1", api_key = "EMPTY", model = "mistral7b")



class mixtral8x7b(mistral):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base = "https://api.deepinfra.com/v1/openai", api_key_path = Path('./deepinfra_api.key').absolute(), model = "mistralai/Mixtral-8x7B-Instruct-v0.1")

