import time, sys
import numpy as np
from typing import Tuple
from functools import wraps
from copy import deepcopy
import cv2
import pyshine as ps

class Timer:    
    def __init__(self, name = ""):
        self._name = name

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_):
        print('='*20 + "TIMER BEGIN" + '='*20)
        print(self._name, time.perf_counter() - self._start)
        print('='*20 + "TIMER END" + '='*20)

def center(bound: Tuple[int, int, int, int]) -> Tuple[int, int]:
    return (bound[0]+bound[2])//2, (bound[1]+bound[3])//2

def parse_bound(bounds: str) -> Tuple[int, int, int, int]:
    left_top,right_bot = bounds.split('][')
    x1,y1 = left_top[1:].split(',')
    x2,y2 = right_bot[:-1].split(',')
    y1,y2 = int(y1),int(y2)
    x1,x2 = int(x1),int(x2)
    return (x1, y1, x2, y2)

# wrappers
def cloneable(init):
    assert init.__name__ == '__init__'
    @wraps(init)
    def wrapper(self, _from, *args, **kwds):
        clazz = getattr(sys.modules[init.__module__], init.__qualname__.split('.')[0])
        #print(_from.__class__.__module__ + '.' + _from.__class__.__name__,
        #        clazz.__module__ + '.' + clazz.__name__)
        #if _from.__class__.__module__ + '.' + _from.__class__.__name__ \
        #        == clazz.__module__ + '.' + clazz.__name__:
        if issubclass(_from.__class__, clazz):
            #print("YAY")
            for k,v in deepcopy(_from).__dict__.items():
                setattr(self, k, v)
            return self
        else:
            return init(self, _from, *args, **kwds)
    return wrapper

# def plot_tags(img, tags):
#     for tag in tags:
#         x1, y1, x2, y2 = parse_bound(tag['bounds'])
#         cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
#         x, y = center((x1, y1, x2, y2))
#         cv2.putText(img, tag['text'], (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
#     return img