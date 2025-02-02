
from typing import List, Dict, Union, Any
from pathlib import Path
from .Base import OpenAIFormatLLM, OpenAIFormatVLM


class gpt(OpenAIFormatLLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_key_path=Path('./openai_api.key').absolute())

    def __call__(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        return super().call_proxy(prompt)


class gpt3(gpt):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, model="gpt-3.5-turbo")


class gpt4(gpt):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, model="gpt-4-turbo")


class gpt4o(gpt):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, model="gpt-4o")


class gpt4omini(gpt):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, model="gpt-4o-mini")


class gpt_vlm(OpenAIFormatVLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_key_path=Path('./openai_api.key').absolute())

    def __call__(self, prompt: List[Dict[str, Any]]) -> Dict[str, Union[str, int, Any]]:
        return super().call_proxy(prompt)


class gpt4o_vlm(gpt_vlm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, model="gpt-4o")


class gpt4omini_vlm(gpt_vlm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, model="gpt-4o-mini")


class gpt4_vlm(gpt_vlm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, model="gpt-4-turbo")
