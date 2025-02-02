from pathlib import Path
from enum import Enum
from typing import Dict, List
import csv

with open("apk-info.csv") as f:
    reader = csv.DictReader(f)
    apk_info = {line['apk_name']: {
                'path': "./apks/" + line["apk_name"] + ".apk",
                'package': line['package_name'],
                'username': line['username'],
                'password': line['password'],
                'category': line['category'],
                } for line in reader}
