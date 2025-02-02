# from llm_wrapper import gpt3, gpt4, gpt4o, llama3,llama3_70b, mistral7b, qwen7b, qwen14b, qwenmoe, claude3haiku, claude3sonnet, deepseekchat
from LLMs import gpt3, gpt4, gpt4o, gpt4omini, llama3, llama3_70b, llama32_11b_vision, mistral7b, qwen7b, qwen14b, qwenmoe, claude3haiku, claude3sonnet, deepseekchat, gpt4_vlm, gpt4o_vlm, gpt4omini_vlm, qwen_vl_max, qwen_vl_plus, qwen_vl_max_0809, qwen_vl_max_latest, qwen_vl_plus_latest
from typing import Tuple, Dict, List, Union, Any
from pathlib import Path


class PlanParsingError(Exception):
    def __init__(self, message):
        super().__init__(message)


class ActionParsingError(Exception):
    def __init__(self, message):
        super().__init__(message)


def get_llm(llm_name: str, *args, **kwargs):
    if llm_name == "gpt3":
        return gpt3(*args, **kwargs)
    elif llm_name == "gpt4":
        return gpt4(*args, **kwargs)
    elif llm_name == "gpt4o":
        return gpt4o(*args, **kwargs)
    elif llm_name == "gpt4omini":
        return gpt4omini(*args, **kwargs)
    elif llm_name == "llama3":
        return llama3(*args, **kwargs)
    elif llm_name == 'llama3_70b':
        return llama3_70b(*args, **kwargs)
    elif llm_name == "llama32_11b":
        return llama32_11b_vision(*args, **kwargs)
    elif llm_name == "mistral7b":
        return mistral7b(*args, **kwargs)
    elif llm_name == "qwen7b":
        return qwen7b(*args, **kwargs)
    elif llm_name == "qwen14b":
        return qwen14b(*args, **kwargs)
    elif llm_name == "qwenmoe":
        return qwenmoe(*args, **kwargs)
    elif llm_name == "claude3-haiku":
        return claude3haiku(*args, **kwargs)
    elif llm_name == "claude3-sonnet":
        return claude3sonnet(*args, **kwargs)
    elif llm_name == "deepseek":
        return deepseekchat(*args, **kwargs)
    elif llm_name == "gpt4_vlm":
        return gpt4_vlm(*args, **kwargs)
    elif llm_name == "gpt4o_vlm":
        return gpt4o_vlm(*args, **kwargs)
    elif llm_name == "gpt4omini_vlm":
        return gpt4omini_vlm(*args, **kwargs)
    elif llm_name == "qwen_vl_max":
        return qwen_vl_max(*args, **kwargs)
    elif llm_name == "qwen_vl_plus":
        return qwen_vl_plus(*args, **kwargs)
    elif llm_name == "qwen_vl_max_latest":
        return qwen_vl_max_latest(*args, **kwargs)
    elif llm_name == "qwen_vl_plus_latest":
        return qwen_vl_plus_latest(*args, **kwargs)
    elif llm_name == "qwen_vl_max_0809":
        return qwen_vl_max_0809(*args, **kwargs)
    else:
        raise ValueError(f"llm_name {llm_name} not recognized")


def update_token_usage(token_usage, new_token_usage):
    token_usage['input'] += new_token_usage['input']
    token_usage['output'] += new_token_usage['output']
    token_usage['total'] += new_token_usage['total']
    return token_usage


def load_react_prompt(modality, use_demonstrations=False, use_skill="") -> Tuple[str, Dict[str, str]]:

    match modality:
        # case "html":
        #     from .prompts.react_prompt_text import prompt
        case "text":
            from .prompts.react_prompt_text import prompt
        case "image":
            from .prompts.react_prompt_image import prompt
        case "annotated_image":
            from .prompts.react_prompt_annotated_image import prompt
        case "multimodal":
            from .prompts.react_prompt_mm import prompt
        case _:
            raise ValueError(f"modality {modality} not recognized")
    prompt: Dict[str, str]

    system_prompt = prompt['system']
    action_space_description = prompt['action_space_description']
    domain_knowledge = prompt['domain_knowledge']
    examples = prompt['examples']
    template = prompt['template']
    meta_data = prompt['meta_data']

    prompt_skill = ""
    prompt_examples = ""

    if use_demonstrations:
        prompt_examples = "\n".join(examples)
    if len(use_skill) > 0:
        prompt_skill = "The SKILL: These are the detailed steps you should follow to achieve the task goal.\n"
    system_prompt += prompt_skill
    return "\n".join([system_prompt, action_space_description, domain_knowledge, prompt_examples, template]), meta_data


def load_reflexion_prompt(modality, use_demonstrations=False) -> Tuple[str, str, Dict[str, str]]:
    match modality:
        case "html":
            from .prompts.reflect_prompt_text import prompt
        case "text":
            from .prompts.reflect_prompt_text import prompt
        case "image":
            from .prompts.reflect_prompt_image import prompt
        case "multimodal":
            from .prompts.reflect_prompt_mm import prompt
    prompt: Dict[str, str]

    system_prompt = prompt['system']
    action_space_description = prompt['action_space_description']
    reflection_prompt = prompt['reflection_system']
    reflection_template = prompt['reflection_template']
    reflection_domain_knowledge = prompt['reflection_domain_knowledge']
    domain_knowledge = prompt['domain_knowledge']
    examples = prompt['examples']
    action_template = prompt['action_template']
    meta_data = prompt['meta_data']
    if use_demonstrations:
        return "\n".join([system_prompt, action_space_description, domain_knowledge, "\n".join(examples), action_template]), "\n".join([reflection_prompt, reflection_domain_knowledge, reflection_template]), meta_data
    return "\n".join([system_prompt, action_space_description, domain_knowledge, action_template]), "\n".join([reflection_prompt, reflection_domain_knowledge, reflection_template]), meta_data


def load_llm_planner_prompt(modality, use_demonstrations=False) -> Tuple[str, str, Dict[str, str]]:

    match modality:
        case "html":
            from .prompts.llmplanner_prompt_text import prompt
        case "text":
            from .prompts.llmplanner_prompt_text import prompt
        case "image":
            from .prompts.llmplanner_prompt_image import prompt
        case "multimodal":
            from .prompts.llmplanner_prompt_mm import prompt

    prompt: Dict[str, str]

    system_prompt_planning = prompt['system_grounding']
    system_prompt_grounding = prompt['system_grounding']
    domain_knowledge_planning = prompt['domain_knowledge_planning']
    domain_knowledge_grounding = prompt['domain_knowledge_grounding']
    examples_planning = prompt['examples_planning']
    examples_grounding = prompt['examples_grounding']
    grounding_template = prompt['grounding_template']
    planning_template = prompt['planning_template']
    meta_data = prompt['meta_data']
    if use_demonstrations:
        return "\n".join([system_prompt_planning, domain_knowledge_planning, "\n".join(examples_planning), planning_template]), "\n".join([system_prompt_grounding, domain_knowledge_grounding, "\n".join(examples_grounding), grounding_template]), meta_data
    return "\n".join([system_prompt_planning, domain_knowledge_planning, planning_template]), "\n".join([system_prompt_grounding, domain_knowledge_grounding, grounding_template]), meta_data


def pack_vl_prompt(prompts: List[Union[str, Path]]) -> List[Dict[str, str]]:
    packed_prompt = [{"role": "user", "content": [p for p in prompts]}]
    return packed_prompt


def pack_text_prompt(prompt: str) -> List[Dict[str, str]]:
    packed_prompt = [{"role": "user", "content": prompt}]
    return packed_prompt


def pack_prompt(prompt: Union[str, List[Union[str, Path]]]) -> List[Dict[str, str]]:
    if isinstance(prompt, str):
        return pack_text_prompt(prompt)
    elif isinstance(prompt, List):
        return pack_vl_prompt(prompt)
