from .react_prompt_common import react_base_prompt

prompt = {
    "system": react_base_prompt["system"].format(observation_description="This is a screenshot of the current app screen."),
    "domain_knowledge": react_base_prompt["domain_knowledge"].format(action_format="text [123,456] [some text]"),
    "action_space_description": """The actions you can perform fall into several categories:

Touch Screen Actions:
`click [x,y]`: This action clicks on a coordination (x,y) on the screen.
`longclick [x,y]`: This action long clicks on a coordination (x,y) on the screen.
`text [x,y] [content]`: Use this to type the content into the field with coordination (x,y).
`swipe [start_x,start_y] [end_x,end_y]`: swipe from coordination (start_x, start_y) to coordination (end_x, end_y).


Global Navigation Actions:
`press [back]`: Press back button.
`press [restart]`: Press to restart the app.
`press [home]`:  Press to return to the desktop.
`press [none]`: Do nothing but wait for the UI page completely loaded.
`press [stop]`: Issue this action when you believe the task is complete.
`press [enter]`: Press the "Enter" key.
""",
    "examples": [
        (
            """OBSERVATION:
[1744] link 'HP CB782A#ABA 640 Inkjet Fax Machine (Renewed)'
		[1749] StaticText '$279.49'
		[1757] button 'Add to Cart'
		[1760] button 'Add to Wish List'
		[1761] button 'Add to Compare'
URL: http://onestopmarket.com/office-products/office-electronics.html
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
    "template": """
OBSERVATION: The observation of the current app screen is the image provided below. The resolution of the screenshot is 768 * 1280.
TASK: {instruction}
PREVIOUS ACTION: {previous_action}""",
    "meta_data": {
        "observation": "image",
                "action_type": "coordination",
                "keywords": ["task", "previous_action"],
                "answer_phrase": "In summary, the next action I will perform is",
                "action_splitter": "```"
    },
}
