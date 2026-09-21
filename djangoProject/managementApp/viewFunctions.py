from .models import Association, Substrate, Site, Record, RecordArchive, Fungi, FungiCurrent, FungiArchive, Member
from django.contrib.auth.models import User

def getFungiObjects(name): # returns (currentFungi, parent, array of children)
    try:
        fungus = Fungi.objects.get(fullName=name)
    except:
        return None, None, None
    current = FungiCurrent.objects.filter(currentFungus=fungus)
    if current.count() == 1:
        children = Fungi.objects.filter(currentName=current.first())
        return current.first(), fungus, children
    return fungus.currentName, fungus.currentName.currentFungus, [fungus]

def createNewCurrentFungi(id):
    curr = FungiCurrent(currentFungus=Fungi.objects.get(id=id))
    curr.save()
    return curr


# import system (similar to seed but more direct)
def databaseBackupOverwrite(data):
    # group the lists
    grouped = {
        #"auth.user": [],
        "managementApp.member": [],
        "managementApp.fungi": [],
        "managementApp.fungiarchive": [],
        "managementApp.site": [],
        "managementApp.record": [],
        "managementApp.recordarchive": [],
        "managementApp.fungicurrent": [],
        "managementApp.association": [],
        "managementApp.substrate": []
    }
    for d in data:
        fields = d["fields"]
        fields["id"] = d["pk"]
        try:
            grouped[d["model"]].append(fields)
        except:
            pass

    Record.objects.all().delete()
    RecordArchive.objects.all().delete()
    FungiCurrent.objects.all().delete()
    Fungi.objects.all().delete()
    FungiArchive.objects.all().delete()
    Site.objects.all().delete()
    Association.objects.all().delete()
    Substrate.objects.all().delete()
    Member.objects.all().delete()
    #User.objects.all().delete()

    #for d in grouped["auth.user"]:
    #    User(**d).save()

    print("adding members")
    for d in grouped["managementApp.member"]:
        if d["profile"] != None:
            d["profile"] = User.objects.get(id=d["profile"])
        Member(**d).save()

    laterFungi = []

    print("adding fungi pass 1")
    for d in grouped["managementApp.fungi"]:
        d["creatorFK"] = Member.objects.get(id=d["creatorFK"])
        d["updaterFK"] = Member.objects.get(id=d["updaterFK"])
        if d["currentName"] == None:
            Fungi(**d).save()
        else:
            laterFungi.append(d)

    print("adding fungi connectors")
    for d in grouped["managementApp.fungicurrent"]:
        d["currentFungus"] = Fungi.objects.get(id=d["currentFungus"])
        FungiCurrent(**d).save()

    print("adding fungi pass 2")
    for d in laterFungi:
        d["currentName"] = FungiCurrent.objects.get(id=d["currentName"])
        Fungi(**d).save()

    print("adding fungi archives")
    for d in grouped["managementApp.fungiarchive"]:
        d["fungiFK"] = Fungi.objects.get(id=d["fungiFK"])
        FungiArchive(**d).save()

    print("adding sites")
    for d in grouped["managementApp.site"]:
        d["creatorFK"] = Member.objects.get(id=d["creatorFK"])
        d["updaterFK"] = Member.objects.get(id=d["updaterFK"])
        Site(**d).save()

    print("adding associations")
    for d in grouped["managementApp.association"]:
        Association(**d).save()

    print("adding substrates")
    for d in grouped["managementApp.substrate"]:
        Substrate(**d).save()

    print("adding records")
    for d in grouped["managementApp.record"]:
        d["fungusFK"] = FungiCurrent.objects.get(id=d["fungusFK"])
        d["siteFK"] = Site.objects.get(id=d["siteFK"])
        d["recorderFK"] = Member.objects.get(id=d["recorderFK"])
        d["identifierFK"] = Member.objects.get(id=d["identifierFK"])
        if d["confirmerFK"] != None:
            d["confirmerFK"] = Member.objects.get(id=d["confirmerFK"])
        d["collectorFK"] = Member.objects.get(id=d["collectorFK"])
        d["updaterFK"] = Member.objects.get(id=d["updaterFK"])
        if d["photographerFK"] != None:
            d["photographerFK"] = Member.objects.get(id=d["photographerFK"])
        try:
            Record(**d).save()
        except:
            print(d["uniqueCode"])

    print("adding record archives")
    for d in grouped["managementApp.recordarchive"]:
        d["recFK"] = Record.objects.get(id=d["recFK"])
        RecordArchive(**d).save()
    
    print("backup insertion complete")
