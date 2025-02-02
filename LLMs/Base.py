'''
LLM wrapper for different language models.
'''
from typing import Any, Dict, List, Union
import os
import base64
import re
from pathlib import Path
import openai
import cv2
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type
)  # for exponential backoff
from copy import deepcopy


@retry(
    retry=retry_if_exception_type((openai.error.APIError, openai.error.APIConnectionError,
                                  openai.error.RateLimitError, openai.error.ServiceUnavailableError, openai.error.Timeout)),
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(3)
)
def chat_completion_with_backoff(**kwargs):
    response = openai.ChatCompletion.create(**kwargs)
    return response


class llm_base:

    def __init__(self, *args, **kwargs):
        '''
        initialize the language model with the necessary parameters.
        '''

    def __call__(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        '''
        This is the main function that will be called when the object is called.
        It takes in a list of dict, specifying the prompt to be passed to the language model.
        It returns a dictionary with the parsed output of the language model, the token usage, and the raw response.
        example:
        prompt = [
            {"role": "system", "content": "Extract primitive concepts and constraint from the instruction."},
            {"role": "user", "content": "I want a x-large, red color."}
        ]
        return {
            'parsed_output': 'primitive_concept:size, constraint:x-large, red color',
            'token_usage': {
                "input": 100,
                "output": 50,
                "total": 150
            },
            'raw_response': Any
        }
        '''
        raise NotImplementedError

    def query_string(self, prompt: List[Dict[str, str]]) -> str:
        assert len(prompt) == 2
        assert prompt[0]["role"] == "system"
        assert prompt[1]["role"] == "user"

        tmp_prompt = deepcopy(prompt)
        tmp_prompt[1]["content"] += "\nPlease only respond with the text input and nothing else.\n"

        print("=" * 10, "Querying String Start", "=" * 10)
        print("system prompt:")
        print(tmp_prompt[0]["content"])
        print("user prompt:")
        print(tmp_prompt[1]["content"])
        response = self(tmp_prompt)["parsed_output"]
        print("=" * 30)
        print(response)
        print("=" * 30)

        if sum([ch == '"' for ch in response]) >= 2:
            ret = response.split('"')[1]
        elif sum([ch == "'" for ch in response]) >= 2:
            ret = response.split("'")[1]
        else:
            ret = response

        print("=" * 10, "Querying String End", "=" * 10)
        return ret

    def query_opinion(self, prompt: List[Dict[str, str]], default_opinion=False) -> bool:

        assert len(prompt) == 2
        assert prompt[0]["role"] == "system"
        assert prompt[1]["role"] == "user"

        tmp_prompt = deepcopy(prompt)
        tmp_prompt[1]["content"] += "\nPlease respond with YES or NO.\n"

        print("=" * 10, "Querying Opinion Start", "=" * 10)
        print("system prompt:")
        print(tmp_prompt[0]["content"])
        print("user prompt:")
        print(tmp_prompt[1]["content"])
        response = self(tmp_prompt)["parsed_output"]
        print("=" * 30)
        print(response)

        upper_response = response.upper()
        if "YES" in upper_response and "NO" not in upper_response:
            ret = True
        elif "NO" in upper_response and "YES" not in upper_response:
            ret = False
        elif "NO" not in upper_response and "YES" not in upper_response:
            ret = default_opinion
        else:
            # find the last occurrence of YES and NO
            last_yes = upper_response.rfind("YES")
            last_no = upper_response.rfind("NO")
            if last_yes > last_no:
                ret = True
            else:
                ret = False
        print("=" * 30)
        print(ret)
        print("=" * 10, "Querying Opinion End", "=" * 10)
        return ret

    def query_index(self, prompt: List[Dict[str, str]], add_none=True, add_message=None) -> int:

        def findFirstInteger(s: str):
            if re.search(r'\d+', s) is None:
                return None
            return int(re.search(r'\d+', s).group())

        assert len(prompt) == 2
        assert prompt[0]["role"] == "system"
        assert prompt[1]["role"] == "user"

        tmp_prompt = deepcopy(prompt)

        if add_message is not None:
            tmp_prompt[1]["content"] += add_message
        else:
            tmp_prompt[1]["content"] += "Please choose one and only element with its index such that element match our instruction. Please respond in the form of 'index-<number>'.\n"
            if add_none:
                tmp_prompt[1]["content"] += "If you can't find any element that match our instruction, please respond with 'None'.\n"
        print("=" * 10, "Querying index Start", "=" * 10)
        print("system prompt:")
        print(tmp_prompt[0]["content"])
        print("user prompt:")
        print(tmp_prompt[1]["content"])
        response = self(tmp_prompt)["parsed_output"]
        print("=" * 30)
        print(response)
        ret = None
        for m in re.finditer('index-', response):
            local = response[m.start():m.start()+12]
            integer = findFirstInteger(local[5:])
            if integer != None:
                ret = integer
        if ret == None:
            ret = findFirstInteger(response)
        print("=" * 30)
        print(ret)
        print("=" * 10, "Querying index End", "=" * 10)
        return ret if ret is not None else -1


class OpenAIFormatLLM(llm_base):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert "model" in kwargs, "model should in kwargs"
        self.model = kwargs['model']
        self.temperature = kwargs.get('temperature', 0.2)

        if "api_key" in kwargs:
            self.api_key = kwargs["api_key"]
        elif "api_key_path" in kwargs:
            with open(kwargs["api_key_path"], encoding="utf-8") as f:
                self.api_key = f.read().strip()
        else:
            raise ValueError("api_key or api_key_path should be provided")

        if "api_base" in kwargs:
            self.api_base = kwargs["api_base"]
        else:
            self.api_base = "https://api.openai.com/v1"

    def call_proxy(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        assert len(prompt) > 0, "prompt should not be empty"
        for (i, p) in enumerate(prompt):
            assert "role" in p, "role key not found in prompt"
            assert "content" in p, "content key not found in prompt"
            assert p["role"] in ["assistant",
                                 "user"] or (p["role"] == "system" and i == 0)

        openai.api_key = self.api_key
        openai.api_base = self.api_base
        openai.api_key_path = None

        os.environ['http_proxy'] = "http://127.0.0.1:8118"
        os.environ['https_proxy'] = "http://127.0.0.1:8118"
        raw_response = chat_completion_with_backoff(
            model=self.model,
            messages=prompt,
            temperature=self.temperature
        )
        del os.environ['http_proxy']
        del os.environ['https_proxy']

        ret = dict()
        ret["raw_response"] = raw_response
        ret["token_usage"] = {
            "input": raw_response.usage.prompt_tokens,
            "output": raw_response.usage.completion_tokens,
            "total": raw_response.usage.total_tokens
        }
        ret["parsed_output"] = raw_response.choices[0].message.content
        return ret

    def call(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        assert len(prompt) > 0, "prompt should not be empty"
        for (i, p) in enumerate(prompt):
            assert "role" in p, "role key not found in prompt"
            assert "content" in p, "content key not found in prompt"
            assert p["role"] in ["assistant",
                                 "user"] or (p["role"] == "system" and i == 0)

        openai.api_key = self.api_key
        openai.api_base = self.api_base
        openai.api_key_path = None
        raw_response = chat_completion_with_backoff(
            model=self.model,
            messages=prompt,
            temperature=self.temperature
        )

        ret = dict()
        ret["raw_response"] = raw_response
        ret["token_usage"] = {
            "input": raw_response.usage.prompt_tokens,
            "output": raw_response.usage.completion_tokens,
            "total": raw_response.usage.total_tokens
        }
        ret["parsed_output"] = raw_response.choices[0].message.content
        return ret


class vlm_base:

    def __init__(self, *args, **kwargs):
        '''
        initialize the vision-language model with the necessary parameters.
        '''

    def __call__(self, prompt: List[Dict[str, Any]]) -> Dict[str, Union[str, int, Any]]:
        '''
        This is the main function that will be called when the object is called.
        It takes in a list of dict, specifying the prompt to be passed to the vision language model.
        It returns a dictionary with the parsed output of the language model, the token usage, and the raw response.
        example:
        prompt = [
            {"role": "system", "content": "Compare the difference of the following two pictures."},
            {"role": "user", "content": [
                "Compare the difference of the following two pictures.",
                Path_1,
                Path_2
            ]}
        ]
        return {
            'parsed_output': 'The difference is ...',
            'token_usage': {
                "input": 100,
                "output": 50,
                "total": 150
            },
            'raw_response': Any
        }
        '''
        raise NotImplementedError

    def query_index(self, prompt: List[Dict[str, Any]]) -> int:
        '''
        This function is used to query the index from the user.
        It takes in a list of dict, specifying the prompt to be passed to the vision language model.
        It returns the index of the element that the user has selected.
        example:
        prompt = [
            {"role": "system", "content": "Please choose one and only element with its index such that element match our instruction."},
            {"role": "user", "content": [
                "Please choose one and only element with its index such that element match our instruction.",
                Path_1,
                Path_2
            ]}
        ]
        return 1
        '''

        def findFirstInteger(s: str):
            if re.search(r'\d+', s) is None:
                return None
            return int(re.search(r'\d+', s).group())

        assert len(prompt) == 2
        assert prompt[0]["role"] == "system"
        assert prompt[1]["role"] == "user"
        new_prompt = deepcopy(prompt)
        add = False
        for i in range(len(new_prompt[1]["content"])):
            if not isinstance(new_prompt[1]["content"][i], Path):
                new_prompt[1]["content"][i] += "Please choose one and only element with its index such that element match our instruction. Please respond in the form of 'index-<number>'.\n"
                add = True
                break
        assert add, "prompt should contain text message"
        print("=" * 10, "Querying index Start", "=" * 10)
        print("system prompt:")
        print(new_prompt[0]["content"])
        print("user prompt:")
        print(new_prompt[1]["content"])
        # for i, p in enumerate(new_prompt[1]["content"]):
        #     if isinstance(p, Path):
        #         import cv2
        #         image = cv2.imread(str(p))
        #         cv2.imwrite("testvlm/image.png", image)
        #         print("look image", i)
        #         input()
        response = self(new_prompt)["parsed_output"]
        print("=" * 30)
        print(response)
        ret = None
        for m in re.finditer('index-', response):
            local = response[m.start():m.start()+12]
            integer = findFirstInteger(local[5:])
            if integer != None:
                ret = integer
        if ret == None:
            ret = findFirstInteger(response)
        print("=" * 30)
        print(ret)
        print("=" * 10, "Querying index End", "=" * 10)
        return ret if ret is not None else -1


class OpenAIFormatVLM(vlm_base):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert "model" in kwargs, "model should in kwargs"
        self.model = kwargs['model']
        self.temperature = kwargs.get('temperature', 0.2)

        if "api_key" in kwargs:
            self.api_key = kwargs["api_key"]
        elif "api_key_path" in kwargs:
            with open(kwargs["api_key_path"], encoding="utf-8") as f:
                self.api_key = f.read().strip()
        else:
            raise ValueError("api_key or api_key_path should be provided")

        if "api_base" in kwargs:
            self.api_base = kwargs["api_base"]
        else:
            self.api_base = "https://api.openai.com/v1"

        self.detail = kwargs.get('detail', 'low')

    def _process_prompt(self, prompt: List[Dict[str, Any]], compress=False) -> List[Dict[str, Any]]:
        new_prompt = []
        for p in prompt:
            role = p["role"]
            content = []
            for c in p["content"]:
                if isinstance(c, Path):
                    pic = cv2.imread(str(c))
                    if not compress:
                        _, pic_encoded = cv2.imencode('.jpg', pic)
                        pic_base64 = base64.b64encode(pic_encoded).decode('utf-8')
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{pic_base64}",
                                "detail": self.detail
                            }
                        })
                    else:
                        height, width = pic.shape[:2]
                        new_size = (int(width * 0.33), int(height * 0.33))
                        print("new size: ", new_size)
                        pic_resized = cv2.resize(pic, new_size, interpolation=cv2.INTER_AREA)
                        _, pic_encoded = cv2.imencode('.jpg', pic_resized)
                        pic_base64 = base64.b64encode(pic_encoded).decode('utf-8')
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{pic_base64}",
                                "detail": self.detail
                            }
                        })
                        
                else:
                    content.append({
                        "type": "text",
                        "text": c
                    })
            new_prompt.append({
                "role": role,
                "content": content
            })
        return new_prompt

    def call(self, prompt: List[Dict[str, Any]], compress=False) -> Dict[str, Union[str, int, Any]]:
        new_prompt = self._process_prompt(prompt, compress=compress)
        # print(new_prompt)
        assert len(new_prompt) > 0, "prompt should not be empty"
        for (i, p) in enumerate(new_prompt):
            assert "role" in p, "role key not found in prompt"
            assert "content" in p, "content key not found in prompt"
            assert p["role"] in ["assistant",
                                 "user"] or (p["role"] == "system" and i == 0)

        openai.api_key = self.api_key
        openai.api_base = self.api_base
        openai.api_key_path = None
        raw_response = chat_completion_with_backoff(
            model=self.model,
            messages=new_prompt,
            temperature=self.temperature
        )

        ret = dict()
        ret["raw_response"] = raw_response
        ret["token_usage"] = {
            "input": raw_response.usage.prompt_tokens,
            "output": raw_response.usage.completion_tokens,
            "total": raw_response.usage.total_tokens
        }
        ret["parsed_output"] = raw_response.choices[0].message.content
        # print(raw_response)
        return ret

    def call_proxy(self, prompt: List[Dict[str, Any]]) -> Dict[str, Union[str, int, Any]]:
        new_prompt = self._process_prompt(prompt)
        assert len(new_prompt) > 0, "prompt should not be empty"
        for (i, p) in enumerate(new_prompt):
            assert "role" in p, "role key not found in prompt"
            assert "content" in p, "content key not found in prompt"
            assert p["role"] in ["assistant",
                                 "user"] or (p["role"] == "system" and i == 0)

        openai.api_key = self.api_key
        openai.api_base = self.api_base
        openai.api_key_path = None
        os.environ['http_proxy'] = "http://127.0.0.1:8118"
        os.environ['https_proxy'] = "http://127.0.0.1:8118"
        raw_response = chat_completion_with_backoff(
            model=self.model,
            messages=new_prompt,
            temperature=self.temperature
        )
        del os.environ['http_proxy']
        del os.environ['https_proxy']

        ret = dict()
        ret["raw_response"] = raw_response
        ret["token_usage"] = {
            "input": raw_response.usage.prompt_tokens,
            "output": raw_response.usage.completion_tokens,
            "total": raw_response.usage.total_tokens
        }
        ret["parsed_output"] = raw_response.choices[0].message.content
        # print(raw_response)
        return ret
