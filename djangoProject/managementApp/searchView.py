from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import RestrictedError
from .forms import SearchForm, SearchForm2
from .models import Association, Substrate, Site, Record, Fungi, FungiCentroids, Member
from .viewFunctions import getFungiObjects
import datetime
import PIL.ExifTags
from PIL import Image, ExifTags
import math
from django.conf import settings
import json
from django.http import FileResponse
from django.db.models import Q
import time

DISTANCE_SCALAR = 111.1
DISTANCE_THRESHOLD = 50
RESULTS = 50
LOOKUP_POINT_THRESHOLD = 0.75
YEARS_TO_CHECK = 8

timer = 0
def start():
    return time.time()
def end(x):
    return time.time() - x

def addToDict(dict, item, num):
    if item in dict.keys():
        dict[item] += num
    else:
        dict[item] = num
    return dict

def calculatePoints(points, records, weighting, scaling, calcFunc=None, calcConst=None):
    # weighting is the effect it'll have on total points
    # scaling is how much more than one fungi occurance will effect the total
    occurances = {}
    for record in records:
        name = record.fungusFK.currentFungus.fullName
        if name in occurances.keys(): # if fungus has occured before then increment it
            occurances[name] += 1
            occurance = occurances[name]
        else: # else create new occurance value
            occurance = 1
            occurances[name] = 1
        if scaling == 0.0:
            point = round((calcFunc(record, calcConst)) * weighting, 3)
        else:
            point = round((calcFunc(record, calcConst) / (occurance * scaling)) * weighting, 3)

        points = addToDict(points, name, point)
    
    return points

def calcDistance(coord1, coord2):
    dist = math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)
    return dist * DISTANCE_SCALAR # returns the distance in kilometers

def distScale1(x): # currently: ((-x+50)^0.5) / 7
    return (math.sqrt(-x + DISTANCE_THRESHOLD)) / 7.0

def distScale2(x):
    return math.sqrt(1 / (x + 1))

def distancePoints(points, records, siteWeight, exactWeight, scaling, siteLoc=None, exactLoc=None):

    occurances = {}
    for record in records:
        name = record.fungusFK.currentFungus.fullName
        
        rSiteLoc = [record.siteFK.lat, record.siteFK.lon]
        siteDist = calcDistance(rSiteLoc, siteLoc)
        if siteDist > DISTANCE_THRESHOLD:
            continue

        if name in occurances.keys(): # if fungus has occured before then increment it
            occurances[name] += 1
            occurance = occurances[name]
        else: # else create new occurance value
            occurance = 1
            occurances[name] = 1

        # get points based off site locations
        point = round((distScale1(siteDist) / (occurance * scaling)) * siteWeight, 3)
        points = addToDict(points, name, point)
        
        if exactLoc == None: # skip if no exact location given
            continue

        # get points based off exact location
        if record.lat == 0.0:
            rExactLoc = rSiteLoc
        else:
            rExactLoc = [record.lat, record.lon]

        point = round((distScale2(calcDistance(rExactLoc, exactLoc)) / (occurance * scaling)) * exactWeight, 3)
        if name in points.keys(): # if fungus has points increment those points
            points[name] += point
        else: # else create new fungus point value
            points[name] = point
    
    return points

def SearchView(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()
    
    results = []
    
    form = SearchForm(request.POST or None, request.FILES or None, prefix="onlineForm")
    if form.is_valid():
        timer = start()
        data = form.cleaned_data

        if data["date"] != None:
            date = data["date"]
        else:
            date = datetime.datetime.now()
        
        # get the query which is anything 2 years before and after the given date
        date += datetime.timedelta(days=365*2)

        dateQuery = (Q(
            dateFound__lte = date + datetime.timedelta(days=365*YEARS_TO_CHECK)) & Q(
            dateFound__gte = date - datetime.timedelta(days=365*YEARS_TO_CHECK))) | (Q(
            dayOfYear__lte = date.timetuple().tm_yday + 21) & Q(
            dayOfYear__gte = date.timetuple().tm_yday - 21))

        reducedRecords = Record.objects.filter(dateQuery)

        points = {}
        # apply substrate points
        if data["substrate"] != "":
            try:
                sub = Substrate.objects.get(name=data["substrate"])
            except:
                messages.add_message(request, messages.ERROR, f"{data['substrate']} not found")
                pass
            # get all ocurances where this substrate is used
            records = reducedRecords.filter(substrFK=sub)
            def calcFunc(record, x):
                return 1.0
            points = calculatePoints(points, records, data["substrW"], 1.5, calcFunc)
        # apply association points
        assocValues = [
            {
                "weight": data["assocW"],
                "scale": 1.5
            },
            {
                "weight": data["assocW"] - 0.1,
                "scale": 1.5
            },
            {
                "weight": data["assocW"] - 0.2,
                "scale": 1.5
            }
        ]
        for i in range(3):
            assocKey = f"association{i+1}"
            if data[assocKey] != "":
                try:
                    assoc = Association.objects.get(name=data[assocKey])
                except:
                    messages.add_message(request, messages.ERROR, f"{data[assocKey]} not found")
                    pass
                # get all ocurances where this substrate is used
                records = reducedRecords.filter(assoc1FK=assoc)
                records.union(reducedRecords.filter(assoc2FK=assoc))
                records.union(reducedRecords.filter(assoc3FK=assoc))
                def calcFunc(record, x):
                    return 1.0
                points = calculatePoints(points, records, assocValues[i]["weight"], assocValues[i]["scale"], calcFunc)

        # apply date points
        if data["date"] != None:
            # get all records with dates within a week either side of the given date
            def calcFunc(record, date):
                dayDiff = record.dateFound.timetuple().tm_yday - date.timetuple().tm_yday
                if dayDiff >= -7 and dayDiff <= 7:
                    return (7 - abs(dayDiff)) / 7.0
                return 0.0
            points = calculatePoints(points, reducedRecords, data["dateW"], 0.0, calcFunc, data["date"])
        
        # apply location points
        if data["site"] != "" or data["image"] != None:
            if data["image"] != None:
                image = Image.open(data["image"])

                # GET GPS LOCATION FROM IMAGE
                # ---------------------------
                GPSINFO_TAG = next(
                    tag for tag, name in ExifTags.TAGS.items() if name == "GPSInfo"
                )

                info = image.getexif()
                gpsinfo = info.get_ifd(GPSINFO_TAG)
                
                north = gpsinfo[2]
                east = gpsinfo[4]
                elat = (((north[0] * 60) + north[1] * 60) + north[2]) / 60 / 60
                elon = (((east[0] * 60) + east[1] * 60) + east[2]) / 60 / 60
                # ---------------------------
            else:
                elat = None
                elon = None
            
            if data["site"] != "":
                try:
                    site = Site.objects.get(name=data["site"])
                except:
                    messages.add_message(request, messages.ERROR, f"{data['site']} not found")
                    pass
                slat = site.lat
                slon = site.lon
            else:
                slat = elat
                slon = elon
            
            weight = data["locW"]
            if elat == None and elon == None:
                points = distancePoints(points, reducedRecords, weight + (weight / 2), 0.0, 1.5, [slat, slon])
            else:
                points = distancePoints(points, reducedRecords, weight, weight, 1.5, [slat, slon], [elat, elon])
        
        # apply clustering points
        if data["includeClustering"]:
            # find the closet centroid
            def calcDistance(p1, p2): # function taken from clustering.py
                dist = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)
                return dist
            
            closest = -1
            closestDist = 1000000000000
            point = [data["radius"], data["darkness"], data["height"]]
            for cent in FungiCentroids.objects.all():
                dist = calcDistance([cent.capRadius, cent.colourDarkness, cent.height], point)
                if dist < closestDist:
                    closestDist = dist
                    closest = cent.id

            # index the fungi model to get the fungi with that centroid
            fungi = Fungi.objects.filter(centroid=closest)

            # add points to those fungi
            for x in fungi:
                points = addToDict(points, x.fullName, 2.0)

        # restructure and order the points dict so its [fullName, commonName (if it has one), points]
        ordered = []
        for name in points.keys():
            if points[name] > 0.0:
                point = points[name]
                # insert into ordered array
                for i in range(len(ordered)):
                    if ordered[i]["points"] <= point:
                        ordered.insert(i, {"fullName": name, "points": point})
                        break

                if len(ordered) == 0:
                    ordered.append({"fullName": name, "points": point})
        
        # only take the best 50 results
        results = []
        if len(ordered) < RESULTS:
            num = len(ordered)
        else:
            num = RESULTS
        for i in range(num):
            fungus = Fungi.objects.get(fullName=ordered[i]["fullName"])
            # insert commonName if it has one
            if fungus.commonName != "":
                ordered[i]["commonName"] = fungus.commonName
            results.append(ordered[i])
        
        print(end(timer))
    
    form2 = SearchForm2(request.POST or None, prefix="offlineForm")
    if form2.is_valid():
        timer = start()
        data = form2.cleaned_data

        date = data["date"]
        date += datetime.timedelta(days=365*2)

        dateQuery = (Q(
            dateFound__lte = date + datetime.timedelta(days=365*YEARS_TO_CHECK)) & Q(
            dateFound__gte = date - datetime.timedelta(days=365*YEARS_TO_CHECK))) | (Q(
            dayOfYear__lte = date.timetuple().tm_yday + 21) & Q(
            dayOfYear__gte = date.timetuple().tm_yday - 21))

        reducedRecords = Record.objects.filter(dateQuery)

        points = {}
        # get all records with dates within a 3 weeks either side of the given date
        def calcFunc(record, date):
            dayDiff = record.dateFound.timetuple().tm_yday - date.timetuple().tm_yday
            if dayDiff >= -21 and dayDiff <= 21:
                return (21 - abs(dayDiff)) / 21.0
            return 0.0
        points = calculatePoints(points, reducedRecords, 1.0, 0.0, calcFunc, data["date"])

        # get points based on site
        if data["site"] != "":
            try:
                site = Site.objects.get(name=data["site"])
            except:
                messages.add_message(request, messages.ERROR, f"{data['site']} not found")
                pass

            points = distancePoints(points, reducedRecords, 1.0, 0.0, 1.5, [site.lat, site.lon])

        results = []
        for name in points.keys():
            point = points[name]
            if point < LOOKUP_POINT_THRESHOLD:
                continue

            # get a list of the most common substrates and associations for each

            current, _, _ = getFungiObjects(name)
            recs = Record.objects.filter(fungusFK=current)
            substrs = {}
            assocs = {}
            for rec in recs:
                substrs = addToDict(substrs, rec.substrFK.name, 1)
                if rec.assoc1FK != None:
                    assocs = addToDict(assocs, rec.assoc1FK.name, 1)
                if rec.assoc2FK != None:
                    assocs = addToDict(assocs, rec.assoc2FK.name, 1)
                if rec.assoc3FK != None:
                    assocs = addToDict(assocs, rec.assoc3FK.name, 1)


            results.append({
                "fullName": name,
                "points": point,
                "commonSubstrates": substrs,
                "commonAssociations": assocs
            })

        print(end(timer))

        # turn into json and send it
        with open(str(settings.MEDIA_ROOT) + "\\tempFiles\\lookUpTable.json", "w") as json_file:
            json.dump({"table": results}, json_file)
            json_file.close()
            return FileResponse(open(str(settings.MEDIA_ROOT) + "\\tempFiles\\lookUpTable.json", "rb"), as_attachment=True, filename="lookUpTable.json")
        


    context = {"form": form, "form2": form2, "results": results}
    return render(request, 'search/search.html', context)