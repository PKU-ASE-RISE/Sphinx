from enum import Flag, auto
from typing import List, Dict, Tuple
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from .controller import AndroidController
from .hierarchy import Event, UIHierarchy
    
class ObservationHandler:

    def __init__(self):
        pass
    
    def get_observation(self, controller: AndroidController) -> Tuple[Dict, bool]:
        obs = {}
        obs["screen"] = controller.capture_screen(format="pillow")
        obs["hierarchy_str"] = controller.dumpstr()
        obs["hierarchy"] = UIHierarchy(ET.fromstring(obs["hierarchy_str"]))
        obs["widgets"] = obs["hierarchy"].widgets()
        obs['numbered_widgets'] = {i: widget for i, widget in enumerate(obs['widgets'])}
        # todo: judge when to terminate
        return obs, False
