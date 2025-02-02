import os
from Agents.ReAct import AgentReAct_Text, AgentReAct_IMG, AgentReAct_MultiModal, AgentReAct_AnnotatedImage
from Agents.Reflexion import AgentReflexion_Text, AgentReflexion_IMG
from Agents.LLMPlanner import AgentLLMPlanner_Text

def get_agent(agent_name: str, modality: str, llm_name: str, instruction: str, *args, **kwargs):
    if agent_name == "ReAct":
        match modality:
            case "text":
                agent = AgentReAct_Text(llm_name=llm_name, instruction=instruction,
                            *args, **kwargs)
            case "image":
                agent = AgentReAct_IMG(llm_name=llm_name, instruction=instruction,
                            *args, **kwargs)
            case "multimodal":
                agent = AgentReAct_MultiModal(llm_name=llm_name, instruction=instruction,
                            *args, **kwargs)
            case "annotated_image":
                agent = AgentReAct_AnnotatedImage(llm_name=llm_name, instruction=instruction,
                            *args, **kwargs)
            case _:
                raise ValueError(f"modality {modality} not recognized")
    elif agent_name == "Reflexion":
        match modality:
            case  "text":
                agent = AgentReflexion_Text(llm_name=llm_name, instruction=instruction,
                            *args, **kwargs)
            case "image":
                agent = AgentReflexion_IMG(llm_name=llm_name, instruction=instruction,
                            *args, **kwargs)
            case _:
                raise ValueError(f"modality {modality} not recognized")
    elif agent_name == "LLMPlanner":
        agent = AgentLLMPlanner_Text(llm_name=llm_name,
                                instruction=instruction,
                                *args, **kwargs)
    else:
        raise ValueError(f"agent_name {agent_name} not recognized")

    return agent
