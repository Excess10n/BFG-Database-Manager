import json
import os
ROOT_DIR = os.path.dirname(__file__)

with open(ROOT_DIR + '/record.json') as json_file:
    record_sample = json.load(json_file)

with open(ROOT_DIR + '/association.json') as json_file:
    substr_sample = json.load(json_file)

for rec in record_sample:
    found = False
    for sub in substr_sample:
        if rec["RecAssoc"] == sub["Association"]:
            found = True
            break
    if not found:
        print(rec["RecAssoc"])