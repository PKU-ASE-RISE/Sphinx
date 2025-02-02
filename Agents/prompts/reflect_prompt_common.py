from react_prompt_text import prompt as react_text_prompt
from react_prompt_common import react_base_prompt
prompt = {
	"system": react_base_prompt['system'],
    "reflection_system": """You are an autonomous intelligent agent tasked with navigating a mobile app. You will be given app-based tasks. These tasks will be accomplished through the use of specific actions you can issue. You have issued an action and received a response. You will now reflect on the action you just performed.

Here's the information you'll have:
The TASK: This is the task you're trying to complete.
The PREVIOUS OBSERVATION: {prev_observation_description}
The PREVIOUS ACTION: This is the action you just performed. It may be helpful to track your progress.
The CURRENT OBSERVATION: {curr_observation_description}

Based on the information, determine whether the previous action was successful.
""",
    "reflection_domain_knowledge": """To be successful, it is very important to follow the following rules:
1. You should reason step by step to reflect whether the issued action was successful or not. This will help you to determine the next action to take.
2. Generate the reflection in the correct format. The final response should end with ```Yes``` or ```No```.
""",
	"domain_knowledge": react_text_prompt['domain_knowledge'],
 
 	"examples": [
		(
			"""OBSERVATION:
[index-0] link 'HP CB782A#ABA 640 Inkjet Fax Machine (Renewed)'
[index-1] StaticText '$279.49'
TASK: What is the price of HP Inkjet Fax Machine
PREVIOUS ACTION: None""",
			"Let's think step-by-step. This page list the information of HP Inkjet Fax Machine, which is the product identified in the objective. Its price is $279.49. I think I have achieved the objective. I will issue the stop action with the answer. In summary, the next action I will perform is ```stop [$279.49]```",
		),
		(
			"""OBSERVATION:
[164] textbox 'Search' focused: True required: False
[171] button 'Go'
[174] link 'Find directions between two points'
[212] heading 'Search Results'
[216] button 'Close'
URL: http://openstreetmap.org
TASK: Show me the restaurants near CMU
PREVIOUS ACTION: None""",
			"Let's think step-by-step. This page has a search box whose ID is [164]. According to the nominatim rule of openstreetmap, I can search for the restaurants near a location by \"restaurants near\". I can submit my typing by pressing the Enter afterwards. In summary, the next action I will perform is ```type [164] [restaurants near CMU] [1]```",
		),
	],

}