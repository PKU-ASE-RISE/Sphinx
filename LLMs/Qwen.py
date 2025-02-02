from typing import List, Dict, Union, Any
from pathlib import Path
# import dashscope
from .Base import OpenAIFormatLLM, vlm_base, OpenAIFormatVLM
from copy import deepcopy


class qwen7b(OpenAIFormatLLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="http://10.129.165.103:8003/v1",
                         api_key="EMPTY", model="qwen7b")

    def __call__(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        return super().call(prompt)


class qwen14b(OpenAIFormatLLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="http://10.129.165.103:8004/v1",
                         api_key="EMPTY", model="qwen14b")

    def __call__(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        return super().call(prompt)


class qwenmoe(OpenAIFormatLLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="http://10.129.165.103:8005/v1",
                         api_key="EMPTY", model="qwenmoe")

    def __call__(self, prompt: List[Dict[str, str]]) -> Dict[str, Union[str, int, Any]]:
        return super().call(prompt)


# class dashscope_vlm(vlm_base):

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.api_key_file_path = Path('./dashscope_api.key').absolute()
#         assert "model" in kwargs, "model should be either qwen-vl-plus or qwen-vl-max"
#         self.model = kwargs['model']

#     def __call__(self, prompt: List[Dict[str, Any]]) -> Dict[str, Union[str, int, Any]]:
#         # qwen-vl series recommend not to use system role
#         new_prompt = []
#         for p in prompt:
#             role = p["role"]
#             if role == "system":
#                 role = "user"
#             content = []
#             for c in p["content"]:
#                 if isinstance(c, Path):
#                     content.append({"image": "file://" + str(c.absolute())})
#                 else:
#                     content.append({"text": c[:20000]})
#             new_prompt.append({
#                 "role": role,
#                 "content": content
#             })
#         assert len(new_prompt) > 0, "prompt should not be empty"
#         for (i, p) in enumerate(new_prompt):
#             assert "role" in p, "role key not found in prompt"
#             assert "content" in p, "content key not found in prompt"
#             assert p["role"] in ["assistant", "user"]

#         while True:
#             try:
#                 dashscope.api_key_file_path = self.api_key_file_path
#                 response = dashscope.MultiModalConversation.call(
#                     model=self.model, messages=new_prompt)

#             # print(response)
#             # print(len(new_prompt[-1]["content"][0]["text"]))

#                 ret = dict()
#                 ret["raw_response"] = response
#                 ret["parsed_output"] = response.output.choices[0].message.content[0]["text"]
#                 ret["token_usage"] = {
#                     "input": response.usage.input_tokens,
#                     "output": response.usage.output_tokens,
#                     "total": response.usage.input_tokens + response.usage.output_tokens
#                 }
#                 return ret
#             except Exception as e:
#                 pass


class qwen_vl_plus(OpenAIFormatVLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
                         api_key_path=Path('./dashscope_api.key').absolute(), model="qwen-vl-plus-2023-12-01")

    def __call__(self, prompt: List[Dict[str, Any]]) -> Dict[str, Union[str, int, Any]]:
        new_prompt = deepcopy(prompt)
        for p in new_prompt:
            for i, c in enumerate(p["content"]):
                if isinstance(c, Path):
                    continue
                else:
                    p["content"][i] = p["content"][i][:20000]
        return super().call(new_prompt, compress=True)


class qwen_vl_max(OpenAIFormatVLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
                         api_key_path=Path('./dashscope_api.key').absolute(), model="qwen-vl-max-0201")

    def __call__(self, prompt: List[Dict[str, Any]]) -> Dict[str, Union[str, int, Any]]:
        new_prompt = deepcopy(prompt)
        for p in new_prompt:
            for i, c in enumerate(p["content"]):
                if isinstance(c, Path):
                    continue
                else:
                    p["content"][i] = p["content"][i][:15000]
        return super().call(new_prompt, compress=True)
    
    
class qwen_vl_max_0809(OpenAIFormatVLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
                         api_key_path=Path('./dashscope_api.key').absolute(), model="qwen-vl-max-0809")

    def __call__(self, prompt: List[Dict[str, Any]]) -> Dict[str, Union[str, int, Any]]:
        new_prompt = deepcopy(prompt)
        # for p in new_prompt:
        #     for c in p["content"]:
        #         if isinstance(c, Path):
        #             continue
        #         else:
        #             p["content"] = p["content"][:30000]
        return super().call(new_prompt)

class qwen_vl_plus_latest(OpenAIFormatVLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
                         api_key_path=Path('./dashscope_api.key').absolute(), model="qwen-vl-plus")

    def __call__(self, prompt: List[Dict[str, Any]]) -> Dict[str, Union[str, int, Any]]:
        new_prompt = deepcopy(prompt)
        for p in new_prompt:
            for i, c in enumerate(p["content"]):
                if isinstance(c, Path):
                    continue
                else:
                    p["content"][i] = p["content"][i][:20000]
        return super().call(new_prompt)


class qwen_vl_max_latest(OpenAIFormatVLM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
                         api_key_path=Path('./dashscope_api.key').absolute(), model="qwen-vl-max")

    def __call__(self, prompt: List[Dict[str, Any]]) -> Dict[str, Union[str, int, Any]]:
        new_prompt = deepcopy(prompt)
        # for p in new_prompt:
        #     for c in p["content"]:
        #         if isinstance(c, Path):
        #             continue
        #         else:
        #             p["content"] = p["content"][:30000]
        return super().call(new_prompt)



# class qwen_vl_plus(dashscope_vlm):

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs, model="qwen-vl-plus-2023-12-01")


# class qwen_vl_max(dashscope_vlm):

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs, model="qwen-vl-max-0201")
