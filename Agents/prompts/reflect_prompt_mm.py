from reflect_prompt_common import prompt as base_prompt
from reflect_prompt_image import prompt as reflexion_image_prompt
from reflect_prompt_text import prompt as reflexion_text_prompt
prompt = {
	"system": reflexion_image_prompt,
	"reflection_system": reflexion_image_prompt['reflection_system'],
	"domain_knowledge": base_prompt['domain_knowledge'].format(action_format="click [index-0]"),
	"reflection_domain_knowledge":base_prompt['reflection_domain_knowledge'],
	"examples": base_prompt['examples'],
	"action_space_description": reflexion_text_prompt['action_space_description'],

 "action_template": reflexion_image_prompt['action_template'],

"reflection_template": reflexion_image_prompt['reflection_template'],

	"meta_data": {
		"observation_mode": "image",
		'action_mode':'coordination',
		"answer_phrase": "In summary, the next action I will perform is",
		"action_splitter": "```"
	},
}