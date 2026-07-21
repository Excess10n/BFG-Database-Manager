from django.core.management.base import BaseCommand
from django.core.files.images import ImageFile
import json
import datetime
from ...models import Member, Fungi, FungiCurrent, FungiArchive, Group, Genus, Site, Association, Substrate, Record, RecordArchive
from django.contrib.auth.models import User
import os

ROOT_DIR = os.path.dirname(__file__)

def catchNullDate(x):
    if x == "" or x == "// 00:00" or "x" in x:
        return None
    else:
        return datetime.datetime.strptime(x, "%d/%m/%Y %H:%M").date()

class Command(BaseCommand):
    help = 'Insert sample data into database for tests'

    def handle(self, *args, **options):
        Record.objects.all().delete()
        RecordArchive.objects.all().delete()
        FungiCurrent.objects.all().delete()
        Fungi.objects.all().delete()
        FungiArchive.objects.all().delete()
        Group.objects.all().delete()
        Genus.objects.all().delete()
        Site.objects.all().delete()
        Association.objects.all().delete()
        Substrate.objects.all().delete()

        Member.objects.all().delete()
        User.objects.all().delete()
        print("yay")

        with open(ROOT_DIR + '/people.json') as json_file:
            people_sample = json.load(json_file)

        with open(ROOT_DIR + '/association.json') as json_file:
            assoc_sample = json.load(json_file)
        
        with open(ROOT_DIR + '/fungi.json') as json_file:
            fungi_sample = json.load(json_file)
        
        with open(ROOT_DIR + '/genus.json') as json_file:
            genus_sample = json.load(json_file)
        
        with open(ROOT_DIR + '/group.json') as json_file:
            group_sample = json.load(json_file)
        
        with open(ROOT_DIR + '/record.json') as json_file:
            record_sample = json.load(json_file)
        
        with open(ROOT_DIR + '/site.json') as json_file:
            site_sample = json.load(json_file)
        
        with open(ROOT_DIR + '/substrate.json') as json_file:
            substr_sample = json.load(json_file)
        
        # members
        index = 0
        for sample in people_sample:
            index += 1
            kwargs = {
                'id': index,
                'firstname': sample["firstname"],
                'surname': sample["surname"],
                'initials': sample["initials"],
                'dateUpdated': datetime.date.today(),
            }

            if sample["firstname"] == "Penny":
                User.objects.create_user('PennyCullington', None, 'password123')
                kwargs['profile'] = User.objects.get(username='PennyCullington')

            Member(**kwargs).save()

            sample["id"] = index

        User.objects.create_superuser('AdminUser', None, "6He03.'jOKzs")

        def getMemberId(initials):
            for p in people_sample:
                if p["initials"] == initials:
                    return p["id"]
            return 1

        # genus
        index = 0
        for sample in genus_sample:
            index += 1
            kwargs = {
                'id': index,
                'name': sample["GenusName"],
                'meaning': sample["GenusMeaning"]
            }
            Genus(**kwargs).save()
        
        # group
        index = 0
        for sample in group_sample:
            index += 1
            kwargs = {
                'id': index,
                'name': sample["GroupName"],
                'repName': sample["GroupRepName"],
                'repNameSort': sample["GroupRepNameSort"],
                'dateUpdated': datetime.datetime.strptime(sample["GroupUpdDate"], "%d/%m/%Y %H:%M").date()
            }
            Group(**kwargs).save()
        
        # fungi
        index = 0
        later_fungi = []

        for sample in fungi_sample:
            if sample["CurrentName"] != sample["NameId"]:
                later_fungi.append(sample)
                continue
            index += 1

            kwargs = {
                'id': index,
                'uniqueCode': sample["NameId"],
                'genus': sample["Genus"],
                'species': sample["Species"],
                'variety': sample["Variety"],
                'group': sample["Group"],
                'commonName': sample["CommonName"],
                'remarks': sample["Remarks"],
                'dateUpdated': datetime.datetime.strptime(sample["ChangeDate"], "%d/%m/%Y %H:%M").date(),
                'creatorFK': Member.objects.get(id=getMemberId(sample["Creator"])),
                'updaterFK': Member.objects.get(id=getMemberId(sample["Updater"]))
            }
            Fungi(**kwargs).save()

            kwargs = {
                'id': index,
                'currentFungus': Fungi.objects.get(id=index)
            }
            FungiCurrent(**kwargs).save()

            kwargs = {
                'id': index,
                'fungiFK': Fungi.objects.get(id=index),
                'GBChkLst': sample["GBChkLst"] == "TRUE",
                'groupOld': sample["GroupOld"],
                'interpretCode': sample["InterpretCode"],
                'DJSCode': sample["DJSCode"],
                'authority': sample["Authority"],
                'BAPspecies': sample["BAPSpecies"] == "TRUE",
            }
            FungiArchive(**kwargs).save()
        
        for sample in later_fungi:
            index += 1
            try:
                current = FungiCurrent.objects.get(currentFungus=Fungi.objects.get(uniqueCode=sample["CurrentName"]))
            except:
                print(sample["NameId"])
                continue
            kwargs = {
                'id': index,
                'uniqueCode': sample["NameId"],
                'genus': sample["Genus"],
                'species': sample["Species"],
                'variety': sample["Variety"],
                'group': sample["Group"],
                'commonName': sample["CommonName"],
                'currentName': current,
                'remarks': sample["Remarks"],
                'dateUpdated': datetime.datetime.strptime(sample["ChangeDate"], "%d/%m/%Y %H:%M").date(),
                'creatorFK': Member.objects.get(id=getMemberId(sample["Creator"])),
                'updaterFK': Member.objects.get(id=getMemberId(sample["Updater"]))
            }
            Fungi(**kwargs).save()

            kwargs = {
                'id': index,
                'fungiFK': Fungi.objects.get(id=index),
                'GBChkLst': sample["GBChkLst"] == "TRUE",
                'groupOld': sample["GroupOld"],
                'interpretCode': sample["InterpretCode"],
                'DJSCode': sample["DJSCode"],
                'authority': sample["Authority"],
                'BAPspecies': sample["BAPSpecies"] == "TRUE",
            }
            FungiArchive(**kwargs).save()
        
        # site
        index = 0
        for sample in site_sample:
            index += 1

            if sample["SiteVC"] == '':
                kwargs = {
                    'id': index,
                    'name': sample["SiteName"],
                    'reportingName': sample["SiteReportingName"],
                    'gridRef': sample["SiteGR"],
                    'county': sample["SiteCounty"],
                    'country': sample["SiteCountry"],
                    'type': sample["SiteType"],
                    'remarks': sample["SiteRemarks"],
                    'dateUpdated': catchNullDate(sample["SiteUpdDate"]),
                    'creatorFK': Member.objects.get(id=getMemberId(sample["SiteCreator"])),
                    'updaterFK': Member.objects.get(id=getMemberId(sample["SiteLastUpdater"])),
                }
            else:
                kwargs = {
                    'id': index,
                    'name': sample["SiteName"],
                    'reportingName': sample["SiteReportingName"],
                    'gridRef': sample["SiteGR"],
                    'county': sample["SiteCounty"],
                    'VC': int(sample["SiteVC"]),
                    'country': sample["SiteCountry"],
                    'type': sample["SiteType"],
                    'remarks': sample["SiteRemarks"],
                    'dateUpdated': catchNullDate(sample["SiteUpdDate"]),
                    'creatorFK': Member.objects.get(id=getMemberId(sample["SiteCreator"])),
                    'updaterFK': Member.objects.get(id=getMemberId(sample["SiteLastUpdater"])),
                }
            
            Site(**kwargs).save()
        
        # substr
        index = 0
        for sample in substr_sample:
            index += 1
            kwargs = {
                'id': index,
                'name': sample["Substrate"]
            }
            Substrate(**kwargs).save()
        
        # assoc
        index = 0
        for sample in assoc_sample:
            index += 1
            kwargs = {
                'id': index,
                'name': sample["Association"],
                'latin': sample["AssocLatin"]
            }
            Association(**kwargs).save()
        
        # record
        index = 0
        count = 0
        for sample in record_sample:
            index += 1

            if sample["Rec1stDB"] == "TRUE":
                first = "D"
            elif sample["Rec1stBucks"] == "TRUE":
                first = "B"
            elif sample["Rec1stSite"] == "TRUE":
                first = "S"
            else:
                first = "N"

            # not used since substr and assoc is now a string value
            # if Substrate.objects.filter(name=sample["RecSubstrate"]).count() == 0:
            #     continue
            # if Association.objects.filter(name=sample["RecAssoc"]).count() == 0:
            #     continue

            try:
                fungus = FungiCurrent.objects.get(currentFungus=Fungi.objects.get(uniqueCode=sample["RecFungus"]))
            except:
                print(sample["RecFungus"])
                continue              
            
            kwargs = {
                'id': index,
                'uniqueCode': sample["RecUnique"],
                'fungusFK': fungus,
                'siteFK': Site.objects.get(name=sample["RecSite"]),
                'recorderFK': Member.objects.get(id=getMemberId(sample["RecRecorder"])),
                'identifierFK': Member.objects.get(id=getMemberId(sample["RecIdentifier"])),
                'collectorFK': Member.objects.get(id=getMemberId(sample["RecCollector"])),
                'substrate': sample["RecSubstrate"],
                'assoc1': sample["RecAssoc"],
                'dateFound': datetime.datetime.strptime(sample["RecDate"], "%d/%m/%Y %H:%M").date(),
                'dateEntered': datetime.datetime.strptime(sample["RecEnteredDate"], "%d/%m/%Y %H:%M").date(),
                'sentBMS': sample["RecSentBMSInd"] == "TRUE",
                'dateSentBMS': catchNullDate(sample["RecSentBMS"]),
                'remarks': sample["RecRemarks"],
                'dateUpdated': datetime.datetime.strptime(sample["RecUpdDate"], "%d/%m/%Y %H:%M").date(),
                'updaterFK': Member.objects.get(id=getMemberId(sample["RecLastUpdater"])),
                'firstRecord': first
            }

            num = getMemberId(sample["RecConfirmer"])
            if num != 1:
                kwargs['confirmerFK'] = Member.objects.get(id=num)

            Record(**kwargs).save()
            
            kwargs = {
                'id': index,
                'recFK': Record.objects.get(id=index),
                'repFungus': sample["RecRepFungus"],
                'repFungusLocked': sample["RecRepFungusLocked"] == "TRUE",
                'sense': sample["RecSense"],
                'ecoSys': sample["RecEcoSys"],
                'appox': sample["RecApprox"] == "TRUE",
                'morph': sample["RecMorph"],
                'herbarium': sample["RecHerbarium"],
                'herbRef': sample["RecHerbRef"],
                'photoLoc': sample["RecPhotoLoc"],
                'BMSDupInd': sample["RecBMSDupInd"] == "TRUE",
                'BMSHold': sample["RecBMSHold"] == "TRUE",
                'BMSForay': sample["BMSForay"] == "TRUE",
                'BMSMisident': sample["BMSMisident"] == "TRUE",
                'BMSdate': catchNullDate(f'{sample["BMSdd"]}/{sample["BMSmm"]}/{sample["BMSyyyy"]} 00:00' ),
                'batchRemarks': sample["RecBatchRemarks"],
                'foray': sample["RecForay"],
                'origin': sample["RecOrigin"],
                'uniqueFlat': sample["RecUniqueFlat"],
                'DRecUnique': int(sample["DRecUnique"]),
                'DRecSpecimenNumber': sample["DRecSpecimenNumber"],
                'DRecMore': sample["DRecMore"],
                'DRecSpecimen': sample["DRecSpecimen"],
                'DRecCulture': sample["DRecCulture"],
                'DRecRecordNumber': sample["DRecRecordNumber"],
                'DRecRecordedAs': sample["DRecRecordedAs"],
                'DRec2005': sample["DRec2005"] == "TRUE",
                'RecMsg2': sample["RecMsg2"]
            }
            if sample["BMSRecNo"] != '':
                kwargs["BMSRecNo"] = int(sample["BMSRecNo"])
            if sample["BMSSenderNo"] != '':
                kwargs["BMSSenderNo"] = int(sample["BMSSenderNo"])

            RecordArchive(**kwargs).save()
            count += 1
        print(str(count) + " records inserted")
        print('Test data inserted into database')
