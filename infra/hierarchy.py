from __future__ import annotations

from .util import cloneable, parse_bound
from copy import deepcopy, copy
from enum import IntEnum
from typing import Deque, Generator, List, Set, Tuple, Union, cast, Dict, Any, TypedDict
from collections import deque
import xml.etree.ElementTree as ET
import logging
import numpy as np
import pyshine as ps
import cv2


class ActionType(IntEnum):
    NONE = 0

    CLICK = 1
    SWIPE = 2
    TEXT = 3
    LONGCLICK = 4

    BACK = 5
    ENTER = 6

    RESTART = 7
    STOP = 8


ACTION_MAP = {
    "NONE": ActionType.NONE,
    "CLICK": ActionType.CLICK,
    "CHECK": ActionType.CLICK,
    "SWIPE": ActionType.SWIPE,
    "TEXT": ActionType.TEXT,
    "INPUT": ActionType.TEXT,
    "LONGCLICK": ActionType.LONGCLICK,
    "BACK": ActionType.BACK,
    "ENTER": ActionType.ENTER,
    "RESTART": ActionType.RESTART,
    "STOP": ActionType.STOP
}


class Action(TypedDict):
    action_type: ActionType
    coords: List[Tuple[int, int]]
    message: str
    clear: bool
    element: Element


def is_equal_action(action1: Action, action2: Action) -> bool:
    # print("calc equal")
    # print(action1.keys())
    # print(action2.keys())
    if action1["action_type"] != action2["action_type"]:
        return False
    if action1["action_type"] == ActionType.NONE or action1["action_type"] == ActionType.BACK or action1["action_type"] == ActionType.ENTER or action1["action_type"] == ActionType.RESTART or action1["action_type"] == ActionType.STOP:
        return True
    if action1.keys() != action2.keys():
        return False
    if "message" in action1 and action1["message"] != action2["message"]:
        return False
    if "element" in action1:
        return action1["element"]._bounds == action2["element"]._bounds
    else:
        return action1["coords"] == action2["coords"]


def none_action() -> Action:
    return {"action_type": ActionType.NONE}


def back_action() -> Action:
    return {"action_type": ActionType.BACK}


def enter_action() -> Action:
    return {"action_type": ActionType.ENTER}


def restart_action() -> Action:
    return {"action_type": ActionType.RESTART}


def stop_action() -> Action:
    return {"action_type": ActionType.STOP}


def click_action(element: Element = None, coord: Tuple[int, int] = None) -> Action:
    action = {"action_type": ActionType.CLICK}
    if element is not None:
        action["element"] = element
    if coord is not None:
        action["coords"] = [coord]
    if "element" not in action and "coords" not in action:
        raise Exception(
            "Click action must have either (element field) or (coord field).")
    return action


def swipe_action(element: Element = None, coord_from: Tuple[int, int] = None, coord_to: Tuple[int, int] = None, direction: str = "up") -> Action:
    action = {"action_type": ActionType.SWIPE}
    if element is not None:
        action["element"] = element
        action["direction"] = direction
    if coord_from is not None and coord_to is not None:
        action["coords"] = [coord_from, coord_to]
    if "element" not in action and "coords" not in action:
        raise Exception(
            "Swipe action must have either (element field) or (coord_from field and coord_to field).")
    return action


def text_action(message: str, clear: bool = True, element: Element = None, coord: Tuple[int, int] = None) -> Action:
    if message is None:
        raise Exception("Text action must have (message field).")
    action = {"action_type": ActionType.TEXT,
              "message": message, "clear": clear}
    if element is not None:
        action["element"] = element
    if coord is not None:
        action["coords"] = [coord]
    if "element" not in action and "coords" not in action:
        raise Exception(
            "Text action must have either (element field) or (coord field).")
    return action


def longclick_action(element: Element = None, coord: Tuple[int, int] = None) -> Action:
    action = {"action_type": ActionType.LONGCLICK}
    if element is not None:
        action["element"] = element
    if coord is not None:
        action["coords"] = [coord]
    if "element" not in action and "coords" not in action:
        raise Exception(
            "Longclick action must have either (element field) or (coord field).")
    return action


def interact_action(action_type: ActionType, message: str = None, clear: bool = True, element: Element = None, coord: Tuple[int, int] = None, coord_from: Tuple[int, int] = None, coord_to: Tuple[int, int] = None, direction: str = "up") -> Action:
    match action_type:
        case ActionType.CLICK:
            action = {"action_type": ActionType.CLICK}
            if element is not None:
                action["element"] = element
            if coord is not None:
                action["coords"] = [coord]
            if "element" not in action and "coords" not in action:
                raise Exception(
                    "Click action must have either (element field) or (coord field).")
        case ActionType.SWIPE:
            action = {"action_type": ActionType.SWIPE}
            if element is not None:
                action["element"] = element
                action["direction"] = direction
            if coord_from is not None and coord_to is not None:
                action["coords"] = [coord_from, coord_to]
            if "element" not in action and "coords" not in action:
                raise Exception(
                    "Swipe action must have either (element field) or (coord_from field and coord_to field).")
        case ActionType.TEXT:
            if message is None:
                raise Exception("Text action must have (message field).")
            action = {"action_type": ActionType.TEXT,
                      "message": message, "clear": clear}
            if element is not None:
                action["element"] = element
            if coord is not None:
                action["coords"] = [coord]
            if "element" not in action and "coords" not in action:
                raise Exception(
                    "Text action must have either (element field) or (coord field).")
        case ActionType.LONGCLICK:
            action = {"action_type": ActionType.LONGCLICK}
            if element is not None:
                action["element"] = element
            if coord is not None:
                action["coords"] = [coord]
            if "element" not in action and "coords" not in action:
                raise Exception(
                    "Longclick action must have either (element field) or (coord field).")
        case _:
            raise Exception("Invalid action type for interact action.")
    return action


def parse_from_dict(action: Dict) -> Action:
    match action["type"]:
        case "none":
            return none_action()
        case "click":
            element = Element(action["element"])
            return click_action(element=element)
        case "swipe":
            element = Element(action["element"])
            x1, y1, x2, y2 = parse_bound(action["element"]["bounds"])
            direction = action["direction"]
            return swipe_action(element=element, direction=direction)
        case "text" | "input":
            element = Element(action["element"])
            message = action["message"]
            return text_action(message, element=element)
        case "longclick":
            element = Element(action["element"])
            return longclick_action(element=element)
        case "back":
            return back_action()
        case "enter":
            return enter_action()
        case "restart":
            return restart_action()
        case "stop":
            return stop_action()
        case _:
            raise Exception("Invalid action type for parsing.")


def get_description(action: Action) -> str:
    match action["action_type"]:
        case ActionType.NONE:
            return "Do nothing."
        case ActionType.CLICK:
            assert "element" in action
            element = action["element"]
            desc = Element.__str__(element)
            return f"Click on {desc}."
        case ActionType.SWIPE:
            assert "element" in action
            assert "direction" in action
            element = action["element"]
            direction = action["direction"]
            desc = Element.__str__(element)
            return f"Swipe on {desc} in {direction} direction."
        case ActionType.TEXT:
            assert "message" in action
            assert "element" in action
            message = action["message"]
            element = action["element"]
            desc = Element.__str__(element)
            return f"Type {message} on {desc}."
        case ActionType.LONGCLICK:
            assert "element" in action
            element = action["element"]
            desc = Element.__str__(element)
            return f"Long click on {desc}."
        case ActionType.BACK:
            return "Go back."
        case ActionType.ENTER:
            return "Press enter."
        case ActionType.RESTART:
            return "Restart the app."
        case ActionType.STOP:
            return "Stop the app."
        case _:
            raise Exception("Invalid action type for description.")


class Element:
    _index: int
    _resource_id: str
    _class: str
    _package: str
    _content_desc: str
    _text: str
    _static_text: str
    _dynamic_text: str
    _checkable: bool
    _checked: bool
    _clickable: bool
    _focusable: bool
    _focused: bool
    _enabled: bool
    _scrollable: bool
    _long_clickable: bool
    _password: bool
    _selected: bool
    _visible_to_user: bool
    _bounds: Tuple[int, int, int, int]

    @cloneable
    def __init__(self, _from: Union[ET.Element, Element, dict, None] = None):
        assert not isinstance(_from, Element)
        if _from == None:
            self._attrib = None
            return

        get = (lambda x, y="": _from.get(x, default=y)) if isinstance(_from, ET.Element) else \
            (lambda x, y="": cast(dict, _from).get(x, y))
        self._attrib = _from.attrib if type(_from) == ET.Element else _from
        self._index = int(get('index'))
        self._resource_id = get('resource-id').split('/')[-1].strip()
        self._class = get('class').strip()
        self._package = get('package').strip()
        self._checkable = get('checkable') == 'true'
        self._checked = get('checked') == 'true'
        self._clickable = get('clickable') == 'true'
        self._focusable = get('focusable') == 'true'
        self._focused = get('focused') == 'true'
        self._enabled = get('enabled') == 'true'
        self._scrollable = get('scrollable') == 'true'
        self._long_clickable = get('long-clickable') == 'true'
        self._password = get('password') == 'true'
        self._selected = get('selected') == 'true'
        self._visible_to_user = get('visible-to-user', 'true') == 'true'
        self._bounds = cast(Tuple[int, int, int, int],
                            tuple(map(int, parse_bound(get('bounds')))))
        self._content_desc = get('content-desc').strip()
        self._text = get('text').strip()

        assert len(self._bounds) == 4, self._bounds
        self._dynamic_text = self._content_desc if len(
            self._content_desc) > 0 else self._text
        self._static_text = type(self).extract_static_text(self._dynamic_text)

    @staticmethod
    def extract_static_text(text: str) -> str:
        return text

    def is_shown_to_user(self) -> bool:
        return self._visible_to_user

    def is_interactable(self) -> bool:
        return self.is_shown_to_user() and len(self._available_actions()) > 0

    def get_mid_point(self) -> Tuple[int, int]:
        return (self._bounds[0] + self._bounds[2]) // 2, (self._bounds[1] + self._bounds[3]) // 2

    def __str__(self) -> str:  # type: ignore
        return f"{self._class}@{self._package}/{self._resource_id}#{self._content_desc}#{self._static_text}"

    def __hash__(self) -> int:  # type: ignore
        return hash(str(self))

    def to_widget(self) -> Union[Widget, None]:
        if not self.is_shown_to_user():
            return None
        try:
            return Widget(self, cast(List[Union[ActionType, str]], self._available_actions()))
        except Exception as e:
            raise e

    def _available_actions(self) -> List[ActionType]:
        ret = []
        if self._class == "android.widget.EditText":
            ret.append(ActionType.TEXT)
        else:
            if self._clickable or self._checkable:
                ret.append(ActionType.CLICK)
            if self._long_clickable:
                ret.append(ActionType.LONGCLICK)
        if self._scrollable:
            ret.append(ActionType.SWIPE)
        return ret

    def __str__(self) -> str:
        description = []
        if len(self._content_desc) > 0:
            description.append(f"content-desc: {self._content_desc}")
        if len(self._resource_id) > 0:
            description.append(
                f"resource-id: {self._resource_id.split('/')[-1]}")
        if len(self._text) > 0:
            description.append(f"text: {self._text}")
        if len(self._class) > 0:
            description.append(f"class: {self._class}")
        return f"a View{' (' + ', '.join(description) + ')' if len(description) != 0 else ''}"

    def is_dull(self) -> bool:
        return len(self._content_desc) == 0 \
            and len(self._resource_id) == 0 \
            and len(self._text) == 0


Element = Element


class Widget(Element):
    _action_types: List[ActionType]

    @cloneable
    def __init__(self, _from: ET.Element | Element | Widget | dict | None = None,
                 _action_types: Union[List[Union[ActionType, str]], None] = None):
        assert not isinstance(_from, Widget)
        super().__init__(_from)
        if _from != None:
            # here we should do a inferrence
            self._action_types = [(ACTION_MAP[ty.upper()] if isinstance(ty, str) else ty) for ty in _action_types] \
                if _action_types is not None else self._available_actions()

    def to_events(self) -> List[Event]:
        # print(self._action_types)
        return [Event(self, a) for a in self._action_types]

    def __str__(self) -> str:
        actions = [x.name.lower() for x in self._action_types]
        if len(actions) == 0:
            return super().__str__() + " to do nothing"
        elif len(actions) == 1:
            return super().__str__() + f" to {actions[0]}"
        else:
            return super().__str__() + f" to {', '.join(actions[:-1])} or {actions[-1]}"


class Event(Widget):
    _action: ActionType
    _params: list

    @cloneable
    def __init__(self, _from: ET.Element | Widget | Event | dict | None = None,
                 _action: Union[ActionType, str, None] = None, _params: list = []):
        super().__init__(_from)
        assert _action is not None
        self._action = ACTION_MAP[_action.upper()] if isinstance(
            _action, str) else _action
        self._params = [x for x in _params]
        if _from is not None:
            # the event in source testcase may not satisfy this property
            # assert self._action in self._action_types
            pass

    @staticmethod
    def restart() -> Event:
        return Event(_action=ActionType.RESTART, _from=None)

    @staticmethod
    def back() -> Event:
        return Event(_action=ActionType.BACK, _from=None)

    def add_param(self, param: str):
        self._params = [param]

    def need_param(self) -> bool:
        return self._action == ActionType.TEXT

    def __str__(self) -> str:
        if self._action == ActionType.RESTART:
            return "restart"
        elif self._action == ActionType.BACK:
            return "back"
        elif self._action == ActionType.TEXT:
            return super(Widget, self).__str__() + f" to edit text {', '.join(self._params)}"
        else:
            return super(Widget, self).__str__() + f" to {self._action.name.lower()} {', '.join(self._params)}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Event):
            return False
        return self._text == other._text and self._action == other._action \
            and self._content_desc == other._content_desc and self._resource_id == other._resource_id \
            and self._class == other._class


class UIHierarchy:
    STATIC_TEXTS: Set[str] = set()

    _nodes: List[Node]
    _children: List[Node]

    class Node(Element):
        _depth: int
        _children: List[Node]
        _output_index: int

        @cloneable
        def __init__(self, _from: Union[Node, Element, ET.Element], _children: List[Node] = [], _depth: int = 1):
            assert not isinstance(_from, Node)
            super().__init__(_from)
            self._children = _children
            self._depth = _depth
            self._output_index = -1

        def add_child(self, child: Node):
            self._children.append(child)

        def add_children(self, children: List[Node]):
            for child in children:
                self.add_child(child)

        def __iter__(self):
            return iter(self._children)

        def __deepcopy__(self, memo):
            # only instance of kid can be copied
            result = type(self).__new__(type(self))
            for k, v in self.__dict__.items():
                if k == "_children":
                    setattr(result, k, copy(v))
                else:
                    setattr(result, k, deepcopy(v, memo))
            return result

    @cloneable
    def __init__(self, _from: Union[UIHierarchy, ET.ElementTree, ET.Element]):
        assert not isinstance(_from, UIHierarchy)
        if isinstance(_from, ET.ElementTree):
            _from = _from.getroot()
        self._nodes = []
        self._children = self._build_children(_from)

    def _build_children(self, _from) -> List[Node]:
        return [self._build_from_element(ch) for ch in cast(ET.Element, _from) if ch.attrib.get("package") != "com.android.systemui"]

    def _build_from_element(self, cur_elem: ET.Element) -> Node:
        q: Deque[Tuple[Node, ET.Element]] = deque()

        def process_elem(elem, father: Node | None = None):
            node = type(self).Node(elem, [], father._depth +
                                   1 if father is not None else 1)
            self._nodes.append(node)
            for ch in elem:
                q.append((node, ch))
            return node
        ret = process_elem(cur_elem)
        while len(q) > 0:
            father, child_elem = q.popleft()
            child = process_elem(child_elem, father)
            father.add_child(child)
        return ret

    def events(self) -> List[Event]:
        return sum(map(lambda x: cast(Widget, x.to_widget()).to_events(),
                   filter(lambda x: x.is_interactable(), self._nodes)), [])

    def widgets(self) -> List[Widget]:
        return [cast(Widget, node.to_widget()) for node in
                filter(lambda x: x.is_interactable(), self._nodes)]

    def __iter__(self):
        return iter(self._nodes)

    def __str__(self) -> str:
        ret = ""
        q: Deque[Node] = deque(self._children)
        while len(q) > 0:
            node = q.popleft()
            ret += "\t"*node._depth + str(node) + '\n'
            for child in reversed(list(node)):  # reverse to assure order
                q.appendleft(child)
        return ret

    def find_element(self, match_rule: Dict[str, str], match_type: str = "equal", must_include_point: Tuple[int, int] | None = None) -> Element | None:
        if match_type == "equal":
            for node in self._nodes:
                if all([(key in node._attrib and node._attrib[key] == value) for key, value in match_rule.items()]):
                    if must_include_point is not None:
                        x, y = must_include_point
                        if node._bounds[0] <= x <= node._bounds[2] and node._bounds[1] <= y <= node._bounds[3]:
                            return node
                    else:
                        return node
        elif match_type == "include":
            for node in self._nodes:
                if all([(key in node._attrib and value in node._attrib[key]) for key, value in match_rule.items()]):
                    if must_include_point is not None:
                        x, y = must_include_point
                        if node._bounds[0] <= x <= node._bounds[2] and node._bounds[1] <= y <= node._bounds[3]:
                            return node
                    else:
                        return node
        else:
            raise ValueError("match_type should be 'equal' or 'include'")
        return None

    def dump_widget_tree(self):
        index = 0
        for node in self._nodes:
            if node.is_interactable():
                node._output_index = index
                index += 1

        def dfs(node: Node, indent: int) -> str:
            if node.is_interactable():
                ret = "\t" * indent + \
                    f"[{node._output_index}] {node.to_widget()}\n"
            else:
                ret = "\t" * indent + f"{node}\n"
            for child in node:
                ret += dfs(child, indent + 1)
            return ret
        ret = ""
        for child in self._children:
            if child._package != "com.android.systemui":
                ret += dfs(child, 0)
        return ret

    def dump_annotated_image(self, image: np.ndarray) -> np.ndarray:
        index = 0
        for node in self._nodes:
            if node.is_interactable():
                node._output_index = index
                index += 1

        def dfs(node: Node):
            for child in node:
                dfs(child)
            if node.is_interactable():
                actions = node._available_actions()
                label = f"{node._output_index}"
                x1, y1, x2, y2 = node._bounds
                # draw the bound
                if ActionType.CLICK in actions:
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
                elif ActionType.SWIPE in actions:
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                elif ActionType.TEXT in actions:
                    cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
                elif ActionType.LONGCLICK in actions:
                    cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 255), 2)
                for i, action in enumerate(actions):
                    offset_x = (x1 * (i + 1) + x2 * (len(actions) - i)
                                ) // (len(actions) + 1) + 5
                    offset_y = (y1 + y2) // 2 + 5
                    if action == ActionType.CLICK:
                        ps.putBText(image, label, text_offset_x=offset_x, text_offset_y=offset_y, vspace=5, hspace=5,
                                    font_scale=1, background_RGB=(255, 0, 0), text_RGB=(255, 250, 250), thickness=2, alpha=0.7)
                    elif action == ActionType.SWIPE:
                        ps.putBText(image, label, text_offset_x=offset_x, text_offset_y=offset_y, vspace=5, hspace=5,
                                    font_scale=1, background_RGB=(0, 255, 0), text_RGB=(255, 250, 250), thickness=2, alpha=0.7)
                    elif action == ActionType.TEXT:
                        ps.putBText(image, label, text_offset_x=offset_x, text_offset_y=offset_y, vspace=5, hspace=5,
                                    font_scale=1, background_RGB=(0, 0, 255), text_RGB=(255, 250, 250), thickness=2, alpha=0.7)
                    elif action == ActionType.LONGCLICK:
                        ps.putBText(image, label, text_offset_x=offset_x, text_offset_y=offset_y, vspace=5, hspace=5,
                                    font_scale=1, background_RGB=(255, 0, 255), text_RGB=(255, 250, 250), thickness=2, alpha=0.7)
                    else:
                        raise NotImplementedError(
                            f"action {action} not supported")
        for child in self._children:
            dfs(child)
        return image


Node = UIHierarchy.Node
