from reflect_prompt_common import prompt as base_prompt
from react_prompt_image import prompt as react_image_prompt
prompt = {
	"system": react_image_prompt,
	"reflection_system": base_prompt['reflection_system'].format(prev_observation_description="This is a screenshot of the previous app screen.", curr_observation_description="This is a screenshot of the current app screen."),
	"domain_knowledge": base_prompt['domain_knowledge'].format(action_format="click [123,456]"),
	"reflection_domain_knowledge":base_prompt['reflection_domain_knowledge'],
	"examples": base_prompt['examples'],

 "action_template": """OBSERVATION: The current app screen is the image provided below.
TASK: {instruction}
PREVIOUS ACTION: {previous_action}""",

"reflection_template": """PREVIOUS OBSERVATION: The previous app screen is the first image provided below.
TASK: {instruction}
PREVIOUS ACTION: {previous_action}
CURRENT OBSERVATION: The current app screen is the second image provided below.""",

	"meta_data": {
		"observation_mode": "image",
		'action_mode':'coordination',
		"answer_phrase": "In summary, the next action I will perform is",
		"action_splitter": "```"
	},
}