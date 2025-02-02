import anthropic
from typing import List, Dict, Union, Any
from pathlib import Path
from .Base import llm_base
import os
class claude(llm_base):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with open("anthropic_api.key") as f:
            self.api_key = f.read().strip()
        self.http_proxy = None
        self.https_proxy = None
        if 'http_proxy' in kwargs and 'https_proxy' in kwargs:
            self.http_proxy = kwargs['http_proxy']
            self.https_proxy = kwargs['https_proxy']
        if self.http_proxy is not None and self.https_proxy is not None:
            os.environ['http_proxy'] = self.http_proxy
            os.environ['https_proxy'] = self.https_proxy
        self.client = anthropic.Anthropic(api_key=self.api_key)
        if self.http_proxy is not None and self.https_proxy is not None:
            del os.environ['http_proxy']
            del os.environ['https_proxy']
        assert "model" in kwargs, "model should be either claude-3-haiku-20240307, claude-3-sonnet-20240229, or claude-3-opus-20240229"
        self.model = kwargs['model']

    def __call__(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        assert len(prompt) > 0, "prompt should not be empty"
        for (i, p) in enumerate(prompt):
            assert "role" in p, "role key not found in prompt"
            assert "content" in p, "content key not found in prompt"
            assert p["role"] in ["assistant",
                                 "user"] or (p["role"] == "system" and i == 0)
        if prompt[0]["role"] == "system":
            system_message = prompt[0]["content"]
            new_prompt = prompt[1:]
        else:
            system_message = ""
            new_prompt = prompt

        if self.http_proxy is not None and self.https_proxy is not None:
            os.environ['http_proxy'] = self.http_proxy
            os.environ['https_proxy'] = self.https_proxy
        if system_message != "":
            raw_response = self.client.messages.create(
                model=self.model,
                system=system_message,
                messages=new_prompt,
                max_tokens=1024
            )
        else:
            raw_response = self.client.messages.create(
                model=self.model,
                messages=new_prompt,
                max_tokens=1024
            )
        if self.http_proxy is not None and self.https_proxy is not None:
            os.environ['http_proxy'] = self.http_proxy
            os.environ['https_proxy'] = self.https_proxy

        ret = dict()
        ret["raw_response"] = raw_response
        ret["token_usage"] = {
            "input": raw_response.usage.input_tokens,
            "output": raw_response.usage.output_tokens,
            "total": raw_response.usage.input_tokens + raw_response.usage.output_tokens
        }
        ret["parsed_output"] = raw_response.content[0].text
        return ret


class claude3haiku(claude):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, model="claude-3-haiku-20240307")


class claude3sonnet(claude):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, model="claude-3-sonnet-20240229")


class claude3opus(claude):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, model="claude-3-opus-20240229")
