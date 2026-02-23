import json
import os
ROOT_DIR = os.path.dirname(__file__)

with open(ROOT_DIR + '/site.json') as json_file:
    site_sample = json.load(json_file)

max = 0
for site in site_sample:
    if len(site["SiteName"]) > max:
        max = len(site["SiteName"])
print(max)