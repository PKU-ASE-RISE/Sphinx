from reflect_prompt_common import prompt as base_prompt
from react_prompt_text import prompt as react_text_prompt
prompt = {
	"system":react_text_prompt['system'],
	"reflection_system": base_prompt['reflection_system'].format(prev_observation_description="This is a simplified representation of the previous UI screen, providing key information.", curr_observation_description="This is a simplified representation of the current UI screen, providing key information."),
	"domain_knowledge": base_prompt['domain_knowledge'].format(action_format="click [index-0]"),
	"reflection_domain_knowledge":base_prompt['reflection_domain_knowledge'],
	"action_space_description":react_text_prompt['action_space_description'],
	"examples": base_prompt['examples'],

 "action_template": """OBSERVATION:
{observation}
TASK: {instruction}
PREVIOUS ACTION: {previous_action}""",

"reflection_template": """PREVIOUS OBSERVATION:
{observation}
TASK: {instruction}
PREVIOUS ACTION: {previous_action}
CURRENT OBSERVATION: {next_observation}""",

	"meta_data": {
		"observation_mode": "text",
		'action_mode':'element_id',
		"answer_phrase": "In summary, the next action I will perform is",
		"action_splitter": "```"
	},
}