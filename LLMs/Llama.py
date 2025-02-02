
from typing import List, Dict, Union, Any
from pathlib import Path
from .Base import OpenAIFormatLLM, OpenAIFormatVLM
from copy import deepcopy
# class llama3(OpenAIFormatLLM):

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs, api_base = "http://10.129.165.103:8001/v1", api_key = "EMPTY", model = "llama3")

#     def __call__(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
#         return super().call(prompt)


class llama3(OpenAIFormatLLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="https://api.deepinfra.com/v1/openai",
                         api_key_path=Path('./deepinfra_api.key').absolute(), model="meta-llama/Meta-Llama-3-8B-Instruct")

    def __call__(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        new_prompt = deepcopy(prompt)
        for p in new_prompt:
            p["content"] = p["content"][:30000]
        return super().call(new_prompt)


class llama3_70b(OpenAIFormatLLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="https://api.deepinfra.com/v1/openai",
                         api_key_path=Path('./deepinfra_api.key').absolute(), model="meta-llama/Meta-Llama-3-70B-Instruct")

    def __call__(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        new_prompt = deepcopy(prompt)
        for p in new_prompt:
            p["content"] = p["content"][:30000]
        return super().call(new_prompt)


class llama31_8b(OpenAIFormatLLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="http://10.129.165.103:8009/v1",
                         api_key="EMPTY", model="llama31-8B")

    def __call__(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        return super().call(prompt)


class llama31_70b(OpenAIFormatLLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="https://api.deepinfra.com/v1/openai",
                         api_key_path=Path('./deepinfra_api.key').absolute(), model="meta-llama/Meta-Llama-3.1-70B-Instruct")

    def __call__(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        return super().call(prompt)


class llama31_405b(OpenAIFormatLLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="https://api.deepinfra.com/v1/openai",
                         api_key_path=Path('./deepinfra_api.key').absolute(), model="meta-llama/Meta-Llama-3.1-405B-Instruct")

    def __call__(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        return super().call(prompt)


class llama32_1b(OpenAIFormatLLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="http://10.129.165.103:8008/v1",
                         api_key="EMPTY", model="llama32-1B")

    def __call__(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        return super().call(prompt)


class llama32_3b(OpenAIFormatLLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="http://10.129.165.103:8007/v1",
                         api_key="EMPTY", model="llama32-3B")

    def __call__(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        return super().call(prompt)


class llama32_11b_vision(OpenAIFormatVLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="http://10.129.165.103:8010/v1",
                         api_key="EMPTY", model="llama3-11B-Vision")

    def __call__(self, prompt: List[Dict[str, Any]]) -> Dict[str, Union[str, int, Any]]:
        new_prompt = deepcopy(prompt)
        for p in new_prompt:
            if p["role"] == "system":
                p["role"] = "user"
        for p in new_prompt:
            for i, c in enumerate(p["content"]):
                if isinstance(c, Path):
                    continue
                else:
                    p["content"][i] = p["content"][i][:20000]
        return super().call(new_prompt)


class llama32_90b_vision(OpenAIFormatVLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="https://api.deepinfra.com/v1/openai",
                         api_key_path=Path('./deepinfra_api.key').absolute(), model="meta-llama/Llama-3.2-90B-Vision-Instruct")

    def __call__(self, prompt: List[Dict[str, Any]]) -> Dict[str, Union[str, int, Any]]:
        new_prompt = deepcopy(prompt)
        for p in new_prompt:
            if p["role"] == "system":
                p["role"] = "user"
        return super().call(new_prompt)
