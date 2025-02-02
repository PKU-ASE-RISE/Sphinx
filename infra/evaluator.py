from .hierarchy import Action
from .util import parse_bound
from .hierarchy import UIHierarchy, Element
from typing import List, Dict, Tuple
import xml.etree.ElementTree as ET
import json
from pathlib import Path


class Evaluator:

    def __init__(self):
        pass

    def evaluate(self, trace: List[Tuple[UIHierarchy, Tuple[str, str]] | Tuple[UIHierarchy, Action]]) -> Tuple[bool, int]:
        # activities: List of (package, activity) tuples
        raise NotImplementedError("Evaluator must implement evaluate method")


class ElementEvaluator(Evaluator):

    def __init__(self):
        super().__init__()

    def _match_element(self, trace: List[Tuple[UIHierarchy, Tuple[str, str]] | Tuple[UIHierarchy, Action]]) -> Tuple[Element, int]:
        # 找到一个 (hierarchy, activity) 对，满足 match_rules
        # 这里对 match_rules 的访问是没有问题的，因为 match_rules 是在子类中定义的

        for i, (hierarchy, activity_info) in enumerate(trace):
            if not isinstance(activity_info, tuple):
                continue
            if self.match_activity != None and self.match_activity != activity_info[1]:
                continue
            element = hierarchy.find_element(self.match_rules, self.match_type)
            if element != None:
                return element, i

        return None, 0

    def _check_element(self, element: Element) -> bool:

        if element == None:
            return False

        # print(self.check_rules.items())
        # print(all([(key in element._attrib and element._attrib[key] == value) for key, value in self.check_rules.items()]))

        if self.check_type == "equal":
            return all([(key in element._attrib and element._attrib[key] == value) for key, value in self.check_rules.items()])
        elif self.check_type == "include":
            return all([(key in element._attrib and value in element._attrib[key]) for key, value in self.check_rules.items()])
        else:
            raise ValueError("check_rule must be either 'equal' or 'include'")


class StopPageEvaluator(ElementEvaluator):

    def __init__(self, match_rules: Dict[str, str], check_rules: Dict[str, str], match_type: str = "equal", check_type: str = "equal"):
        super().__init__()
        self.match_rules = match_rules
        self.check_rules = check_rules
        self.match_type = match_type
        self.check_type = check_type
        self.check_activity = None
        if "activity" in self.match_rules:
            raise ValueError("activity cannot be used in match_rules")
        if "activity" in self.check_rules:
            self.check_activity = self.check_rules["activity"]
            del self.check_rules["activity"]
        if self.match_type not in ["equal", "include"] or self.check_type not in ["equal", "include"]:
            raise ValueError(
                "match_type and check_type must be either 'equal' or 'include'")

    def evaluate(self, trace: List[Tuple[UIHierarchy, Tuple[str, str]] | Tuple[UIHierarchy, Action]]) -> Tuple[bool, int]:

        if len(trace) < 2:
            return False, 0

        stoppage = trace[-2][0]
        activity = trace[-2][1][1]
        element = stoppage.find_element(self.match_rules, self.match_type)

        return self._check_element(element) and (self.check_activity == None or self.check_activity == activity), len(trace) - 2


class FindElementEvaluator(ElementEvaluator):

    def __init__(self, match_rules: Dict[str, str], check_rules: Dict[str, str], match_type: str = "equal", check_type: str = "equal"):
        super().__init__()
        self.match_rules = match_rules
        self.check_rules = check_rules
        self.match_type = match_type
        self.check_type = check_type
        self.match_activity = None
        self.check_activity = None
        if "activity" in self.match_rules:
            self.match_activity = self.match_rules["activity"]
            del self.match_rules["activity"]
        if "activity" in self.check_rules:
            self.check_activity = self.check_rules["activity"]
            del self.check_rules["activity"]
        if self.match_type not in ["equal", "include"] or self.check_type not in ["equal", "include"]:
            raise ValueError(
                "match_type and check_type must be either 'equal' or 'include'")

    def evaluate(self, trace: List[Tuple[UIHierarchy, Tuple[str, str]] | Tuple[UIHierarchy, Action]]) -> Tuple[bool, int]:
        element, idx = self._match_element(trace)

        if element == None:
            return False, 0

        # print("findelement", self._check_element(element))

        return self._check_element(element) and (self.check_activity == None or self.check_activity == trace[idx][1][1]), idx


class ActionEvaluator(Evaluator):

    ACTION_ATTRIBS = ["action_type", "message"]
    ELEMENT_ATTRIBS = ["resource-id", "class", "text", "content-desc", "bounds", "package", "checkable", "checked",
                       "clickable", "enabled", "focusable", "focused", "scrollable", "long-clickable", "password", "selected", "visible-to-user"]

    def __init__(self):
        super().__init__()

    def _match_action(self, trace: List[Tuple[UIHierarchy, Tuple[str, str]] | Tuple[UIHierarchy, Action]]) -> Tuple[UIHierarchy, Action, int]:
        # 找到一个 (hierarchy, action) 对，其中 action 的属性满足 match_rules，且 hierarchy 中包含 action 要求的 element attribute
        # 这里对 match_rules 的访问是没有问题的，因为 match_rules 是在子类中定义的

        for i, (hierarchy, action) in enumerate(trace):
            # print("action", action)
            if isinstance(action, tuple):
                # print("istuple", action)
                continue
            evaldict = action.copy()
            evaldict["action_type"] = evaldict["action_type"].name.lower()
            if evaldict["action_type"] == "text":
                evaldict["action_type"] = "input"
            # print("_match_action:", action)
            if all([key in self.ACTION_ATTRIBS for key in self.match_rules.keys()]) == True:
                # all of the match_rules are action attributes
                # print(evaldict, self.match_rules)
                if self.match_type == "equal":
                    if all([key in evaldict and evaldict[key] == value for key, value in self.match_rules.items()]):
                        return hierarchy, action, i
                elif self.match_type == "include":
                    if all([key in evaldict and value in evaldict[key] for key, value in self.match_rules.items()]):
                        return hierarchy, action, i
                else:
                    raise ValueError(
                        "match_type must be either 'equal' or 'include")
            else:
                # some of the match_rules are element attributes
                if "element" in evaldict:
                    x1, y1, x2, y2 = parse_bound(
                        evaldict["element"]._attrib["bounds"])
                    evaldict["coords"] = [((x1+x2)//2, (y1+y2)//2)]
                if "coords" not in evaldict:
                    continue
                element = hierarchy.find_element({key: value for key, value in self.match_rules.items(
                ) if key not in self.ACTION_ATTRIBS}, self.match_type, evaldict["coords"][0])
                if element == None:
                    continue
                evaldict = {**evaldict, **element._attrib}
                if self.match_type == "equal":
                    if all([key in evaldict and evaldict[key] == value for key, value in self.match_rules.items()]):
                        return hierarchy, action, i
                elif self.match_type == "include":
                    if all([key in evaldict and value in evaldict[key] for key, value in self.match_rules.items()]):
                        return hierarchy, action, i
                else:
                    raise ValueError(
                        "match_type must be either 'equal' or 'include")

        return None, None, 0

    def _check_action(self, hierarchy: UIHierarchy, action: Action) -> bool:
        # 在 hierarchy 中能够找到一个控件，其属性满足 check_rules，且能够包括 coords
        # 这里对 check_rules 的访问是没有问题的，因为 check_rules 是在子类中定义的
        # print(self.check_rules)
        evaldict = action.copy()
        evaldict["action_type"] = evaldict["action_type"].name.lower()
        if evaldict["action_type"] == "text":
            evaldict["action_type"] = "input"
        # print(evaldict)
        # print(action)
        # print(self.check_rules)
        if all([key in self.ACTION_ATTRIBS for key in self.check_rules.keys()]) == True:
            # all of the check_rules are action attributes
            if self.check_type == "equal":
                if all([key in evaldict and evaldict[key] == value for key, value in self.check_rules.items()]):
                    return True
            elif self.check_type == "include":
                if all([key in evaldict and value in evaldict[key] for key, value in self.check_rules.items()]):
                    return True
            else:
                raise ValueError(
                    "check_type must be either 'equal' or 'include")
        else:
            # some of the check_rules are element attributes
            if "element" in evaldict:
                x1, y1, x2, y2 = parse_bound(
                    evaldict["element"]._attrib["bounds"])
                evaldict["coords"] = [((x1+x2)//2, (y1+y2)//2)]
            if "coords" not in evaldict:
                return False
            element = hierarchy.find_element({key: value for key, value in self.check_rules.items(
            ) if key not in self.ACTION_ATTRIBS}, self.check_type, evaldict["coords"][0])
            # print(hierarchy._nodes)
            # print("widgets:::\n")
            # # print(hierarchy.widgets())
            # for node in hierarchy._nodes:
            #     print(node._attrib["resource-id"])
            #     # print(node._attrib)
            if element == None:
                return False
            evaldict = {**evaldict, **element._attrib}
            if self.check_type == "equal":
                if all([key in evaldict and evaldict[key] == value for key, value in self.check_rules.items()]):
                    return True
            elif self.check_type == "include":
                if all([key in evaldict and value in evaldict[key] for key, value in self.check_rules.items()]):
                    return True
            else:
                raise ValueError(
                    "check_type must be either 'equal' or 'include")

        return False


class LastActionEvaluator(ActionEvaluator):

    def __init__(self, check_rules: Dict[str, str], check_type: str = "equal"):
        super().__init__()
        self.check_rules = check_rules
        self.check_type = check_type
        if self.check_type not in ["equal", "include"]:
            raise ValueError("check_type must be either 'equal' or 'include'")

    def evaluate(self, trace: List[Tuple[UIHierarchy, Tuple[str, str]] | Tuple[UIHierarchy, Action]]) -> Tuple[bool, int]:

        # at least [first_hierarchy, first_action, second_hierarchy, stop_action]
        if len(trace) < 3:
            # last action is already matched by other evaluators
            return False, 0

        # select trace[-3] since the last action is stop action
        lasthierarchy, lastaction = trace[-3]

        return self._check_action(lasthierarchy, lastaction), len(trace) - 3


class FindActionEvaluator(ActionEvaluator):

    def __init__(self, match_rules: Dict[str, str], check_rules: Dict[str, str], match_type: str = "equal", check_type: str = "equal"):
        super().__init__()
        self.match_rules = match_rules
        self.check_rules = check_rules
        self.match_type = match_type
        self.check_type = check_type
        if self.match_type not in ["equal", "include"] or self.check_type not in ["equal", "include"]:
            raise ValueError(
                "match_type and check_type must be either 'equal' or 'include'")

    def evaluate(self, trace: List[Tuple[UIHierarchy, Tuple[str, str]] | Tuple[UIHierarchy, Action]]) -> Tuple[bool, int]:
        hierarchy, action, idx = self._match_action(trace)

        # print("findaction", hierarchy != None, action != None, idx)

        if hierarchy == None or action == None:
            return False, 0

        return self._check_action(hierarchy, action), idx


class FindElementByActionEvaluator(ElementEvaluator, ActionEvaluator):

    def __init__(self, action_match_rules: Dict[str, str], element_match_rules: Dict[str, str], element_check_rules: Dict[str, str], action_match_type: str = "equal", element_match_type: str = "equal", element_check_type: str = "equal"):
        super().__init__()
        self.match_rules = action_match_rules
        self.element_match_rules = element_match_rules
        self.check_rules = element_check_rules
        self.match_type = action_match_type
        self.element_match_type = element_match_type
        self.check_type = element_check_type
        if self.match_type not in ["equal", "include"] or self.element_match_type not in ["equal", "include"] or self.check_type not in ["equal", "include"]:
            raise ValueError(
                "match_type and check_type must be either 'equal' or 'include'")

    def evaluate(self, trace: List[Tuple[UIHierarchy, Tuple[str, str]] | Tuple[UIHierarchy, Action]]) -> Tuple[bool, int]:
        hierarchy, action, idx = self._match_action(trace)

        if hierarchy == None or action == None:
            return False, 0

        element = hierarchy.find_element(
            self.element_match_rules, self.element_match_type)

        return self._check_element(element), idx


class RuleEvaluator(Evaluator):

    def __init__(self, order: str, evaluators: List[Evaluator]):
        super().__init__()
        self.order = order
        self.evaluators = evaluators
        if self.order not in ["sequential", "consecutive", "present"]:
            raise ValueError(
                "order must be either 'sequential', 'consecutive' or 'present'")

    def evaluate(self, trace: List[Tuple[UIHierarchy, Tuple[str, str]] | Tuple[UIHierarchy, Action]]) -> Tuple[bool, int]:
        # we can use the same element multiple times
        # todo(if need): add a evaluator class as placeholder to match the next element
        if self.order == "sequential":
            idx = 0
            for evaluator in self.evaluators:
                # print(idx)
                result, idx_offset = evaluator.evaluate(trace[idx:])
                idx += idx_offset
                if not result:
                    return False, idx
            return True, idx
        elif self.order == "consecutive":
            for i in range(len(trace)):
                idx = i
                main_result = True
                for evaluator in self.evaluators:
                    # print("idx=", idx)
                    result, idx_offset = evaluator.evaluate(
                        trace[idx: idx + 3])
                    # print("result", result)
                    idx += idx_offset
                    if not result:
                        main_result = False
                        break
                # print(i, idx, main_result)
                if main_result:
                    return True, idx
            return False, 0
        elif self.order == "present":
            max_idx = -1
            for evaluator in self.evaluators:
                result, idx = evaluator.evaluate(trace)
                max_idx = max(max_idx, idx)
                if not result:
                    # the max_idx is not used
                    return False, max_idx
            return True, max_idx
        else:
            raise ValueError(
                "order must be either 'sequential', 'consecutive' or 'present'")


class MainEvaluator:

    evaluators: List[Evaluator]

    def _generate(self, raw: Dict[str, str]) -> Evaluator:
        match raw["type"]:
            case "rule":
                order = raw["order"]
                evaluators = [self._generate(evaluator)
                              for evaluator in raw["evaluators"]]
                return RuleEvaluator(order, evaluators)
            case "findelement":
                return FindElementEvaluator(raw["match_rules"], raw["check_rules"], raw["match_type"], raw["check_type"])
            case "stoppage":
                return StopPageEvaluator(raw["match_rules"], raw["check_rules"], raw["match_type"], raw["check_type"])
            case "lastaction":
                return LastActionEvaluator(raw["check_rules"], raw["check_type"])
            case "findaction":
                return FindActionEvaluator(raw["match_rules"], raw["check_rules"], raw["match_type"], raw["check_type"])
            case "findelementbyaction":
                return FindElementByActionEvaluator(raw["action_match_rules"], raw["element_match_rules"], raw["check_rules"], raw["action_match_type"], raw["element_match_type"], raw["check_type"])
            case _:
                raise ValueError("Invalid evaluation type.")

    def __init__(self, evaluator_path: Path = None, evaluator_config: List = []):
        self.evaluators = []
        if evaluator_config == []:
            if evaluator_path == None:
                raise ValueError(
                    "Either evaluator_path or evaluator_config must be provided.")
            if evaluator_path.exists():
                with open(evaluator_path, "r") as f:
                    evaluator_config = json.load(f)
            else:
                print("Warning: evaluator file not found.")
                evaluator_config = []
        for raw in evaluator_config:
            evaluator = self._generate(raw)
            self.evaluators.append(evaluator)

    def evaluate(self, hierarchies: List[UIHierarchy], actions: List[Action], activities: List[Tuple[str, str]]) -> bool:
        for activity in activities:
            if not isinstance(activity, tuple):
                print(activity)
                raise ValueError("Activity must be a tuple.")
        steps = len(actions)
        if len(hierarchies) != steps:
            raise ValueError(
                "The number of hierarchies and actions must be the same.")
        if len(activities) != steps:
            raise ValueError(
                "The number of activities and actions must be the same.")
        trace = sum([[(hierarchy, activity), (hierarchy, action)] for hierarchy,
                    activity, action in zip(hierarchies, activities, actions)], [])
        for evaluator in self.evaluators:
            result, _ = evaluator.evaluate(trace)
            # print("result", result)
            if not result:
                return False
        return True
