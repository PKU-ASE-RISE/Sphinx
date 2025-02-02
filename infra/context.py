from .hierarchy import *

class Activity:
    pkgname: str
    name: str
    def __init__(self, pkgname, name):
        self.pkgname = pkgname
        self.name = name
    def info(self) -> Tuple[str, str]:
        return self.pkgname, self.name
    def __eq__(self, other: object):
        if not isinstance(other, Activity):
            return False
        other_act = cast(Activity, other)
        return (self.pkgname, self.name) == (other_act.pkgname, other_act.name)

class Context:
    pass
