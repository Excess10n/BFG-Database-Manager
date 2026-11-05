from .models import Association, Substrate, Site, Record, RecordArchive, Fungi, FungiCurrent, FungiArchive, Member
from django.contrib.auth.models import User
import ijson

only_include = ['fungi 6298', 'fungi 6302', 'fungi 6326', 'fungi 6372', 'fungi 6391', 'fungi 6413', 'fungi 6475', 'fungi 6476', 'fungi 6517', 'fungi_con 3886', 'fungi_con 3890', 'fungi_con 3906', 'fungi_con 3937', 'fungi_con 3953', 'fungi_con 3965', 'fungi_con 4011', 'fungi_con 4012', 'fungi_con 4040', 'fungi_2 6303', 'fungi_2 6327', 'fungi_2 6373', 'fungi_2 6392', 'fungi_2 6477', 'fungi_2 6518', 'fungi_arc 6266', 'fungi_arc 6270', 'fungi_arc 6290', 'fungi_arc 6327', 'fungi_arc 6343', 'fungi_arc 6360', 'fungi_arc 6411', 'fungi_arc 6412', 'fungi_arc 6449', 'record RPC0092061', 'record RDJS0090076', 'record RDJS0081574', 'record RDJS0081748', 'record RDJS0081909', 'record DJS0027310', 'record RDJS0082059', 'record RDJS0082061', 'record RNJJ0082643', 'record RDJS0081710', 'record RDJS0086872', 'record RDJS0086881', 'record RDJS0086892', 'record RDJS0081473', 'record RDJS0082770', 'record RDJS0077879', 'record RDJS0081867', 'record RDJS0081744', 'record RDJS0081732', 'record RDJS0081267', 'record RDJS0081274', 'record RDJS0081289', 'record RDJS0081759', 'record RDJS0077845', 'record RDJS0081807', 'record RDJS0081811', 'record RDJS0081424', 'record RDJS0081438', 'record RDJS0081493', 'record RDJS0082055', 'record RDJS0082410', 'record RDJS0081886', 'record RDJS0081926', 'record RDJS0081983', 'record RDJS0082011', 'record RDJS0086619', 'record RDJS0086628', 'record RDJS0086637', 'record RDJS0086638', 'record RDJS0086649', 'record RDJS0086653', 'record RDJS0086660', 'record RDJS0086661', 'record RDJS0086585', 'record RDJS0086595', 'record RDJS0086797', 'record RDJS0086681', 'record RDJS0086725', 'record RDJS0086827', 'record PC0100810', 'record PC0100645', 'record PC0066406', 'record PC0066520', 'record PC0026868', 'record DJS0032368', 'record DJS0030330', 'record RPC0077330A', 'record RPC0077045', 'record RPC0079556', 'record RPC0070420', 'record RDJS0073305', 'record PC0074605', 'record RDJS0070408', 'record RDJS0070420', 'record DJS0029093', 'record RPC0068316', 'record DJS0007716', 'record DJS0007717', 'record DJS0007718', 'record DJS0007719', 'record DJS0007720', 'record PC0020250', 'record DJS0030361', 'record DJS0075036', 'record DJS0026315', 'record DJS0026739', 'record DJS0026740', 'record DJS0026741', 'record DJS0026742', 'record DJS0026743', 'record DJS0026744', 'record DJS0026745', 'record DJS0026746', 'record DJS0026747', 'record DJS0026776', 'record DJS0026781', 'record DJS0027452', 'record DJS0027488', 'record DJS0027534', 'record DJS0027535', 'record DJS0029382', 'record DJS0030020', 'record DJS0078858', 'record DJS0078857', 'record DJS0047172', 'record DJS0074957', 'record DJS0077565', 'record DJS0074956', 'record DJS0077564', 'record DJS0074954', 'record DJS0075037', 'record DJS0073315', 'record DJS0079112', 'record DJS0047171', 'record DJS0078865', 'record DJS0073313', 'record DJS0073312', 'record DJS0073314', 'record DJS0064862', 'record DJS0074953', 'record DJS0073388', 'record DJS0073387', 'record DJS0077562', 'record DJS0066310', 'record RDJS0089269', 'record DJS0019900', 'record DJS0026728', 'record DJS0026729', 'record RNJJ0061812', 'record RNJJ0063540', 'record RNJJ0063526', 'record DJS0027547', 'record DJS0029415', 'record DJS0021484', 'record DJS0026869', 'record DJS0027453', 'record DJS0027454', 'record DJS0029383', 'record DJS0030339', 'record DJS0030503', 'record RNJJ0054553', 'record RNJJ0062529', 'record RNJJ0065081', 'record RNJJ0062296', 'record RNJJ0062899', 'record RNJJ0062849', 'record RNJJ0062782', 'record RNJJ0062936A', 'record RNJJ0063134', 'record RNJJ0063341', 'record RNJJ0063451', 'record RNJJ0064323A', 'record RNJJ0065124', 'record RNJJ0065126', 'record RNJJ0066105', 'record RNJJ0065130', 'record RNJJ0065448', 'record RNJJ0064466A', 'record RNJJ0064469A', 'record RNJJ0064472A', 'record RNJJ0064486A', 'record RNJJ0065530', 'record RNJJ0064655', 'record RNJJ0065142', 'record RNJJ0064951', 'record RNJJ0064965', 'record RNJJ0065066', 'record RNJJ0065068', 'record RNJJ0065429', 'record RNJJ0065072', 'record RNJJ0065075', 'record RNJJ0065077', 'record RNJJ0065178', 'record RNJJ0065198', 'record RNJJ0065199', 'record RNJJ0065245', 'record RNJJ0065679', 'record RNJJ0066092', 'record RNJJ0066128', 'record RNJJ0066135', 'record RNJJ0066147', 'record RNJJ0066006', 'record RNJJ0066068', 'record RNJJ0066223', 'record RNJJ0066243', 'record RNJJ0066245', 'record RNJJ0066318', 'record RNJJ0066320', 'record RNJJ0066347', 'record RNJJ0066356', 'record RNJJ0066393', 'record RNJJ0066396', 'record RNJJ0066425', 'record RNJJ0066427', 'record RNJJ0066493', 'record RNJJ0066511', 'record RNJJ0066603', 'record RDJS0076047', 'record RDJS0075983', 'record RDJS0075993', 'record RDJS0075961', 'record RDJS0075971', 'record RDJS0076100', 'record RDJS0076174', 'record RDJS0076178', 'record RDJS0089157', 'record RDJS0089409', 'record RDJS0089105', 'record RPC0096966', 'record RPC0096986', 'record RPC0096997', 'record RPC0097000', 'record RPC0098899', 'record RPC0101089', 'record RPC0101090', 'record RPC0101092', 'record RPC0101095', 'record RPC0101251', 'record RPC0105268', 'record RPC0105758', 'record RPC0106677', 'record RPC0108359', 'record RPC0108540', 'record RPC0108558', 'record RPC0108638', 'record RPC0110740', 'record RPC0110745', 'record RPC0110867', 'record RPC0111064', 'record RPC0111191', 'record RPC0111628', 'record RPC0111865', 'record RPC0111877', 'record RPC0112228', 'record RPC0113137', 'record RPC0113155', 'record RPC0113204', 'record RPC0113290', 'record RPC0113317', 'record RPC0113382', 'record RPC0113389', 'record RPC0113390', 'record RPC0113395', 'record RPC0113418', 'record RPC0113420', 'record RPC0113433', 'record RPC0113444', 'record RPC0113468', 'record RPC0113519', 'record RPC0113533', 'record RPC0113537', 'record RPC0113540', 'record RPC0113563', 'record RPC0113574', 'record RPC0113579', 'record RPC0113583', 'record RPC0113587', 'record RPC0113596', 'record RPC0113608', 'record RPC0113663', 'record RPC0113714', 'record RPC0113741', 'record RPC0113749']
only_include2 = ['fungi 6298', 'fungi 6302', 'fungi 6326', 'fungi 6372', 'fungi 6391', 'fungi 6413', 'fungi 6475', 'fungi 6476', 'fungi 6517', 'fungi_con 3886', 'fungi_con 3890', 'fungi_con 3906', 'fungi_con 3937', 'fungi_con 3953', 'fungi_con 3965', 'fungi_con 4011', 'fungi_con 4012', 'fungi_con 4040', 'fungi_2 6303', 'fungi_2 6327', 'fungi_2 6373', 'fungi_2 6392', 'fungi_2 6477', 'fungi_2 6518', 'fungi_arc 6266', 'fungi_arc 6270', 'fungi_arc 6290', 'fungi_arc 6327', 'fungi_arc 6343', 'fungi_arc 6360', 'fungi_arc 6411', 'fungi_arc 6412', 'fungi_arc 6449', 'record RDJS0090076', 'record RDJS0081574', 'record RDJS0081748', 'record RDJS0081909', 'record RDJS0082059', 'record RDJS0082061', 'record RNJJ0082643', 'record RDJS0081710', 'record RDJS0086872', 'record RDJS0086881', 'record RDJS0086892', 'record RDJS0081473', 'record RDJS0082770', 'record RDJS0077879', 'record RDJS0081867', 'record RDJS0081744', 'record RDJS0081732', 'record RDJS0081267', 'record RDJS0081274', 'record RDJS0081289', 'record RDJS0081759', 'record RDJS0077845', 'record RDJS0081807', 'record RDJS0081811', 'record RDJS0081424', 'record RDJS0081438', 'record RDJS0081493', 'record RDJS0082055', 'record RDJS0081886', 'record RDJS0081926', 'record RDJS0081983', 'record RDJS0086619', 'record RDJS0086628', 'record RDJS0086637', 'record RDJS0086638', 'record RDJS0086649', 'record RDJS0086653', 'record RDJS0086660', 'record RDJS0086661', 'record RDJS0086585', 'record RDJS0086595', 'record RDJS0086797', 'record RDJS0086681', 'record RDJS0086725', 'record RDJS0086827', 'record PC0100810', 'record PC0066406', 'record PC0066520', 'record PC0026868', 'record DJS0030330', 'record RPC0077330A', 'record RPC0077045', 'record RDJS0070408', 'record RDJS0070420', 'record DJS0029093', 'record DJS0007716', 'record DJS0007717', 'record DJS0007718', 'record DJS0007719', 'record DJS0007720', 'record PC0020250', 'record DJS0075036', 'record DJS0026315', 'record DJS0026739', 'record DJS0026740', 'record DJS0026741', 'record DJS0026742', 'record DJS0026743', 'record DJS0026744', 'record DJS0026745', 'record DJS0026746', 'record DJS0026747', 'record DJS0026776', 'record DJS0026781', 'record DJS0027452', 'record DJS0027488', 'record DJS0027534', 'record DJS0027535', 'record DJS0029382', 'record DJS0030020', 'record DJS0078858', 'record DJS0078857', 'record DJS0047172', 'record DJS0074957', 'record DJS0077565', 'record DJS0074956', 'record DJS0077564', 'record DJS0074954', 'record DJS0075037', 'record DJS0073315', 'record DJS0079112', 'record DJS0047171', 'record DJS0078865', 'record DJS0073313', 'record DJS0073312', 'record DJS0073314', 'record DJS0064862', 'record DJS0074953', 'record DJS0066310', 'record DJS0019900', 'record DJS0026729', 'record RNJJ0061812', 'record RNJJ0063540', 'record RNJJ0063526', 'record DJS0027547', 'record DJS0029415', 'record DJS0021484', 'record DJS0026869', 'record DJS0027453', 'record DJS0027454', 'record DJS0030339', 'record DJS0030503', 'record RNJJ0054553', 'record RNJJ0065081', 'record RNJJ0065130', 'record RNJJ0064472A', 'record RNJJ0064655', 'record RNJJ0065679', 'record RNJJ0066223', 'record RNJJ0066493', 'record RDJS0076047', 'record RDJS0075983', 'record RDJS0075993', 'record RDJS0075961', 'record RDJS0075971', 'record RDJS0076100', 'record RDJS0076174', 'record RDJS0076178', 'record RPC0096966', 'record RPC0096986', 'record RPC0096997', 'record RPC0097000', 'record RPC0101089', 'record RPC0101090', 'record RPC0101092', 'record RPC0101095', 'record RPC0106677', 'record RPC0108359', 'record RPC0108540', 'record RPC0108558', 'record RPC0108638', 'record RPC0111064', 'record RPC0111191', 'record RPC0111628', 'record RPC0111865', 'record RPC0111877', 'record RPC0113137', 'record RPC0113155', 'record RPC0113204', 'record RPC0113317', 'record RPC0113382', 'record RPC0113389', 'record RPC0113390', 'record RPC0113418', 'record RPC0113420', 'record RPC0113444', 'record RPC0113468', 'record RPC0113519', 'record RPC0113533', 'record RPC0113537', 'record RPC0113540', 'record RPC0113574', 'record RPC0113579', 'record RPC0113587', 'record RPC0113608', 'record RPC0113663', 'record RPC0113714', 'record RPC0113741', 'record RPC0113749']

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

def searchFungiObjects(query): # returns array of currentFungi objects
    fungi = Fungi.objects.filter(fullName__icontains=query, currentName=None)
    currents = FungiCurrent.objects.filter(currentFungus__in=fungi)
    return currents

def createNewCurrentFungi(id):
    curr = FungiCurrent(currentFungus=Fungi.objects.get(id=id))
    curr.save()
    return curr


# import system (similar to seed but more direct) (DEPRECIATED)
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
    index = 0
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

        index += 1
        if index % 10000 == 0:
            print(index)

    index = 0
    print("adding record archives")
    for d in grouped["managementApp.recordarchive"]:
        d["recFK"] = Record.objects.get(id=d["recFK"])
        RecordArchive(**d).save()

        index += 1
        if index % 10000 == 0:
            print(index)
    
    print("backup insertion complete")


def databaseBackupOverwriteBuffered(file, delete_existing):
    grouped = {
        "managementApp.member": [],
        "managementApp.fungi": [],
        "managementApp.fungiarchive": [],
        "managementApp.site": [],
        #"managementApp.record": [],
        #"managementApp.recordarchive": [],
        "managementApp.fungicurrent": [],
        "managementApp.association": [],
        "managementApp.substrate": []
    }

    fails = []

    for d in ijson.items(file, "item"):
        if d["model"] == "managementApp.record" or d["model"] == "managementApp.recordarchive":
            continue
        fields = d["fields"]
        fields["id"] = d["pk"]
        try:
            grouped[d["model"]].append(fields)
        except:
            pass

    if delete_existing:
        Record.objects.all().delete()
        RecordArchive.objects.all().delete()
        FungiCurrent.objects.all().delete()
        Fungi.objects.all().delete()
        FungiArchive.objects.all().delete()
        Site.objects.all().delete()
        Association.objects.all().delete()
        Substrate.objects.all().delete()
        Member.objects.all().delete()

    print("adding members")
    for d in grouped["managementApp.member"]:
        if d["profile"] != None:
            d["profile"] = User.objects.get(id=d["profile"])
        Member(**d).save()

    laterFungi = []

    print("adding fungi pass 1")
    for d in grouped["managementApp.fungi"]:
        try:
            d["creatorFK"] = Member.objects.get(id=d["creatorFK"])
            d["updaterFK"] = Member.objects.get(id=d["updaterFK"])
            if d["currentName"] == None:
                Fungi(**d).save()
            else:
                laterFungi.append(d)
        except:
            fails.append(f"fungi {d['id']}")

    print("adding fungi connectors")
    for d in grouped["managementApp.fungicurrent"]:
        try:
            d["currentFungus"] = Fungi.objects.get(id=d["currentFungus"])
            FungiCurrent(**d).save()
        except:
            fails.append(f"fungi_con {d['id']}")

    print("adding fungi pass 2")
    for d in laterFungi:
        try:
            d["currentName"] = FungiCurrent.objects.get(id=d["currentName"])
            Fungi(**d).save()
        except:
            fails.append(f"fungi_2 {d['id']}")

    print("adding fungi archives")
    for d in grouped["managementApp.fungiarchive"]:
        try:
            d["fungiFK"] = Fungi.objects.get(id=d["fungiFK"])
            FungiArchive(**d).save()
        except:
            fails.append(f"fungi_arc {d['id']}")

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
    index = 0
    file.seek(0)
    for d in ijson.items(file, "item"):
        if d["model"] == "managementApp.record":
            try:
                fields = d["fields"]
                if d["pk"] != None:
                    fields["id"] = d["pk"]

                fields["fungusFK"] = FungiCurrent.objects.get(id=fields["fungusFK"])
                fields["siteFK"] = Site.objects.get(id=fields["siteFK"])
                fields["recorderFK"] = Member.objects.get(id=fields["recorderFK"])
                fields["identifierFK"] = Member.objects.get(id=fields["identifierFK"])
                if fields["confirmerFK"] != None:
                    fields["confirmerFK"] = Member.objects.get(id=fields["confirmerFK"])
                fields["collectorFK"] = Member.objects.get(id=fields["collectorFK"])
                fields["updaterFK"] = Member.objects.get(id=fields["updaterFK"])
                if fields["photographerFK"] != None:
                    fields["photographerFK"] = Member.objects.get(id=fields["photographerFK"])
                Record(**fields).save()
            except:
                fails.append(f"record {fields['uniqueCode']}")


        elif d["model"] == "managementApp.recordarchive":
            fields = d["fields"]
            fields["id"] = d["pk"]

            fields["recFK"] = Record.objects.get(id=fields["recFK"])
            RecordArchive(**fields).save()

        index += 1
        if index % 10000 == 0:
            print(index)

    real_fails = []
    for f in fails:
        if f in only_include2:
            real_fails.append(f)

    return real_fails

def databaseBackupRecordAppend(file):
    for d in ijson.items(file, "item"):
        fields = d["fields"]
        #fields["id"] = d["pk"]

        fields["fungusFK"] = FungiCurrent.objects.get(id=fields["fungusFK"])
        try:
            fields["siteFK"] = Site.objects.get(id=fields["siteFK"])
        except:
            fields["siteFK"] = Site.objects.get(name=fields["siteFK"])
        fields["recorderFK"] = Member.objects.get(id=fields["recorderFK"])
        fields["identifierFK"] = Member.objects.get(id=fields["identifierFK"])
        if fields["confirmerFK"] != None:
            fields["confirmerFK"] = Member.objects.get(id=fields["confirmerFK"])
        fields["collectorFK"] = Member.objects.get(id=fields["collectorFK"])
        fields["updaterFK"] = Member.objects.get(id=fields["updaterFK"])
        if fields["photographerFK"] != None:
            fields["photographerFK"] = Member.objects.get(id=fields["photographerFK"])
        try:
            Record(**fields).save()
        except:
            print(fields["uniqueCode"])