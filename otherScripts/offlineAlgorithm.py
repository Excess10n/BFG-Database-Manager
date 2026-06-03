import json
import os
import time

timer = 0
def start():
    return time.time()
def end(x):
    return time.time() - x

ROOT_DIR = os.path.dirname(__file__)

# This is to showcase an offline varient of the offline algorithm that the mobile app would use

with open(ROOT_DIR + "/lookUpTable.json", "r") as json_file:
    table = json.load(json_file)
    json_file.close()

sub = input("enter substrate -> ")
assoc1 = input("enter 1st association -> ")
assoc2 = input("enter 2st association -> ")
assoc3 = input("enter 3st association -> ")

def pointScale(x):
    if x == 0:
        return 0
    return round(-(1.0 / x) + 2, 3)

timer = start()
ordered = []
for tab in table["table"]:
    # loop through all substr and assocs if it is one of the selected ones then add points
    for k in tab["commonSubstrates"].keys():
        if k == sub:
            tab["points"] += pointScale(tab["commonSubstrates"][k])
    for k in tab["commonAssociations"].keys():
        if k == assoc1 or k == assoc2 or k == assoc3:
            tab["points"] += pointScale(tab["commonAssociations"][k])
    
    # insert into ordered list
    for i in range(len(ordered)):
        if ordered[i]["points"] <= tab["points"]:
            ordered.insert(i, tab)
            break

    if len(ordered) == 0:
        ordered.append(tab)

if len(ordered) < 50:
    num = len(ordered)
else:
    num = 50

print(end(timer))

for i in range(num):
    print(f"{ordered[i]['fullName']}\t\t\t{ordered[i]['points']}")

