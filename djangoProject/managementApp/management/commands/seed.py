from django.core.management.base import BaseCommand
from django.core.files.images import ImageFile
import json
import datetime
from ...models import Member, Fungi, FungiCurrent, FungiArchive, Group, Genus, Site, Association, Substrate, Record, RecordArchive
from django.contrib.auth.models import User, Permission
from django.db.utils import IntegrityError
import os

ROOT_DIR = os.path.dirname(__file__)

def catchNullDate(x):
    if x == "" or x == "// 00:00" or "x" in x or "X" in x:
        return None
    else:
        try:
            return datetime.datetime.strptime(x, "%d/%m/%Y %H:%M").date()
        except:
            return None

class Command(BaseCommand):
    help = 'Insert sample data into database for tests'

    def handle(self, *args, **options):
        Record.objects.all().delete()
        RecordArchive.objects.all().delete()
        FungiCurrent.objects.all().delete()
        Fungi.objects.all().delete()
        FungiArchive.objects.all().delete()
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
        with open(ROOT_DIR + '/fungi_old.json') as json_file:
            fungi_old_sample = json.load(json_file)
        
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
        index = 1
        for sample in people_sample:
            if sample["action"] == "DELETE" or sample["action"] == "DUPPED":
                continue
            kwargs = {
                'id': int(sample["id"]),
                'firstname': sample["firstname"],
                'surname': sample["surname"],
                'initials': sample["initials"],
                'dateUpdated': datetime.date.today(),
            }

            if sample["firstname"] == "Penny":
                u = User.objects.create_user('PennyCullington', None, 'password123')
                kwargs['profile'] = User.objects.get(username='PennyCullington')
                permission = Permission.objects.get(codename='manager')
                u.user_permissions.add(permission)
            if sample["firstname"] == "Jonathan":
                u = User.objects.create_user(f"{sample['firstname']}{sample['surname']}", None, 'password123')
                kwargs['profile'] = User.objects.get(username=f"{sample['firstname']}{sample['surname']}")
                permission = Permission.objects.get(codename='member')
                u.user_permissions.add(permission)

            Member(**kwargs).save()
            index += 1

        # admin user
        kwargs = {
            'id': index,
            'firstname': "admin",
            'surname': "admin",
            'initials': "A",
            'dateUpdated': datetime.date.today(),
        }
        u = User.objects.create_superuser('AdminUser', None, "6He03.'jOKzs")
        kwargs['profile'] = User.objects.get(username='AdminUser')
        permission = Permission.objects.get(codename='manager')
        u.user_permissions.add(permission)
        Member(**kwargs).save()

        # kwargs = {
        #     'id': 746,
        #     'firstname': "DELETED",
        #     'surname': "DELETED",
        #     'initials': "DEL.",
        #     'isDeleted': True,
        #     'dateUpdated': datetime.date.today(),
        # }
        # Member(**kwargs).save()

        print("yay members")

        def getMemberId(initials):
            for p in people_sample:
                if p["initials"] == initials:
                    if p["action"] == "DELETE":
                        return 51 # ID of anon
                    return p["id"]
            return 51
        
        # site
        index = 0
        for sample in site_sample:
            index += 1
            if sample["SiteCreator"] == "":
                sample["SiteCreator"] = sample["SiteLastUpdater"]
            
            kwargs = {
                'id': index,
                'name': sample["SiteReportingName"],
                'gridRef': sample["SiteGR"],
                'county': sample["SiteCounty"],
                'type': sample["SiteType"],
                'remarks': sample["SiteRemarks"],
                'dateUpdated': catchNullDate(sample["SiteUpdDate"]),
                'creatorFK': Member.objects.get(id=getMemberId(sample["SiteCreator"])),
                'updaterFK': Member.objects.get(id=getMemberId(sample["SiteLastUpdater"])),
            }
            if sample["SiteVC"] != '':
                kwargs['VC'] = int(sample["SiteVC"])

            try:
                Site(**kwargs).save()
                sample["id"] = index
            except:
                sample["id"] = Site.objects.get(name=sample["SiteReportingName"]).id

        print("yay sites")
        
        # fungi
        # GOING #####################################
        # index = 0
        # later_fungi = []

        # for sample in fungi_sample:
        #     if sample["CurrentName"] != sample["NameId"]:
        #         later_fungi.append(sample)
        #         continue
        #     index += 1

        #     kwargs = {
        #         'id': index,
        #         'uniqueCode': sample["NameId"],
        #         'genus': sample["Genus"],
        #         'species': sample["Species"],
        #         'variety': sample["Variety"],
        #         'group': sample["Group"],
        #         'commonName': sample["CommonName"],
        #         'remarks': sample["Remarks"],
        #         'dateUpdated': datetime.datetime.strptime(sample["ChangeDate"], "%d/%m/%Y %H:%M").date(),
        #         'creatorFK': Member.objects.get(id=getMemberId(sample["Creator"])),
        #         'updaterFK': Member.objects.get(id=getMemberId(sample["Updater"]))
        #     }
        #     Fungi(**kwargs).save()

        #     kwargs = {
        #         'id': index,
        #         'currentFungus': Fungi.objects.get(id=index)
        #     }
        #     FungiCurrent(**kwargs).save()

        #     kwargs = {
        #         'id': index,
        #         'fungiFK': Fungi.objects.get(id=index),
        #         'GBChkLst': sample["GBChkLst"] == "TRUE",
        #         'groupOld': sample["GroupOld"],
        #         'interpretCode': sample["InterpretCode"],
        #         'DJSCode': sample["DJSCode"],
        #         'authority': sample["Authority"],
        #         'BAPspecies': sample["BAPSpecies"] == "TRUE",
        #     }
        #     FungiArchive(**kwargs).save()
        
        # for sample in later_fungi:
        #     index += 1
        #     try:
        #         current = FungiCurrent.objects.get(currentFungus=Fungi.objects.get(uniqueCode=sample["CurrentName"]))
        #     except:
        #         print(sample["NameId"])
        #         continue
        #     kwargs = {
        #         'id': index,
        #         'uniqueCode': sample["NameId"],
        #         'genus': sample["Genus"],
        #         'species': sample["Species"],
        #         'variety': sample["Variety"],
        #         'group': sample["Group"],
        #         'commonName': sample["CommonName"],
        #         'currentName': current,
        #         'remarks': sample["Remarks"],
        #         'dateUpdated': datetime.datetime.strptime(sample["ChangeDate"], "%d/%m/%Y %H:%M").date(),
        #         'creatorFK': Member.objects.get(id=getMemberId(sample["Creator"])),
        #         'updaterFK': Member.objects.get(id=getMemberId(sample["Updater"]))
        #     }
        #     Fungi(**kwargs).save()

        #     kwargs = {
        #         'id': index,
        #         'fungiFK': Fungi.objects.get(id=index),
        #         'GBChkLst': sample["GBChkLst"] == "TRUE",
        #         'groupOld': sample["GroupOld"],
        #         'interpretCode': sample["InterpretCode"],
        #         'DJSCode': sample["DJSCode"],
        #         'authority': sample["Authority"],
        #         'BAPspecies': sample["BAPSpecies"] == "TRUE",
        #     }
        #     FungiArchive(**kwargs).save()
        ###############################################
        
        # fungi
        # PASS 1
        index = 0
        for sample in fungi_sample:
            try:
                if sample["parentId"] != "-1":
                    continue

                old = {}
                for o in fungi_old_sample:
                    if o["NameId"] == sample["oldId"]:
                        old = o
                        break

                kwargs = {
                    'id': int(sample["id"]),
                    'fullName': sample["FullName"].strip(),
                    'englishName': sample["CommonName"],
                    'author': sample["Author"],
                    'group': sample["Group"],
                    'taxonGroup': sample["TaxonGroup"],
                    'currentTVK': sample["CurrentTVK"]
                }

                if old == {}:
                    kwargs['dateUpdated'] = datetime.datetime.now()
                    kwargs['creatorFK'] = Member.objects.get(id=getMemberId("PC"))
                    kwargs['updaterFK'] = Member.objects.get(id=getMemberId("PC"))
                    Fungi(**kwargs).save()
                else:
                    kwargs['remarks'] = old["Remarks"]
                    kwargs['dateUpdated'] = datetime.datetime.strptime(old["ChangeDate"], "%d/%m/%Y %H:%M").date()
                    kwargs['creatorFK'] = Member.objects.get(id=getMemberId(old["Creator"]))
                    kwargs['updaterFK'] = Member.objects.get(id=getMemberId(old["Updater"]))
                    Fungi(**kwargs).save()

                    kwargs = {
                        'id': int(sample["id"]),
                        'fungiFK': Fungi.objects.get(id=sample["id"]),
                        'uniqueCode': old["NameId"],
                        'GBChkLst': old["GBChkLst"] == "TRUE",
                        'groupOld': old["GroupOld"],
                        'interpretCode': old["InterpretCode"],
                        'DJSCode': old["DJSCode"],
                        'authority': old["Authority"],
                        'BAPspecies': old["BAPSpecies"] == "TRUE",
                    }
                    FungiArchive(**kwargs).save()

                index += 1
                kwargs = {
                    'id': index,
                    'currentFungus': Fungi.objects.get(id=int(sample["id"]))
                }
                FungiCurrent(**kwargs).save()

            except IntegrityError as e:
                #print(e)
                pass
        
        # PASS 2
        for sample in fungi_sample:
            try:
                if sample["parentId"] == "-1":
                    continue
        
                old = {}
                for o in fungi_old_sample:
                    if o["NameId"] == sample["oldId"]:
                        old = o
                        break

                #print(sample["FullName"])
                kwargs = {
                    'id': int(sample["id"]),
                    'fullName': sample["FullName"].strip(),
                    'englishName': sample["CommonName"],
                    'author': sample["Author"],
                    'group': sample["Group"],
                    'taxonGroup': sample["TaxonGroup"],
                    'currentTVK': sample["CurrentTVK"],
                    'currentName': FungiCurrent.objects.get(currentFungus=Fungi.objects.get(id=int(sample["parentId"])))
                }
        
                if old == {}:
                    kwargs['dateUpdated'] = datetime.datetime.now()
                    kwargs['creatorFK'] = Member.objects.get(id=getMemberId("PC"))
                    kwargs['updaterFK'] = Member.objects.get(id=getMemberId("PC"))
                    Fungi(**kwargs).save()
                else:
                    kwargs['remarks'] = old["Remarks"]
                    kwargs['dateUpdated'] = datetime.datetime.strptime(old["ChangeDate"], "%d/%m/%Y %H:%M").date()
                    kwargs['creatorFK'] = Member.objects.get(id=getMemberId(old["Creator"]))
                    kwargs['updaterFK'] = Member.objects.get(id=getMemberId(old["Updater"]))
                    Fungi(**kwargs).save()
        
                    kwargs = {
                        'id': int(sample["id"]),
                        'fungiFK': Fungi.objects.get(id=int(sample["id"])),
                        'uniqueCode': old["NameId"],
                        'GBChkLst': old["GBChkLst"] == "TRUE",
                        'groupOld': old["GroupOld"],
                        'interpretCode': old["InterpretCode"],
                        'DJSCode': old["DJSCode"],
                        'authority': old["Authority"],
                        'BAPspecies': old["BAPSpecies"] == "TRUE",
                    }
                    FungiArchive(**kwargs).save()

            except IntegrityError as e:
                #print(e)
                pass

        print("yay fungi")
        
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
        fungi_gone = []
        site_gone = []
        for sample in record_sample:
            print(sample["RecUnique"])
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
                arc = FungiArchive.objects.get(uniqueCode=sample["RecFungus"])
                current = FungiCurrent.objects.filter(currentFungus=arc.fungiFK)
                if current.count() == 1:
                    fungus = current.first()
                else:
                    fungus = arc.fungiFK.currentName
            except:
                fungi_gone.append(sample["RecUnique"])
                continue

            for s in site_sample:
                if s["SiteName"] == sample["RecSite"]:
                    site = Site.objects.get(id=s["id"])
                    break
            else:
                site_gone.append(sample["RecUnique"])
                continue

            kwargs = {
                'id': index,
                'uniqueCode': sample["RecUnique"],
                'fungusFK': fungus,
                'siteFK': site,
                'recorderFK': Member.objects.get(id=getMemberId(sample["RecRecorder"])),
                'identifierFK': Member.objects.get(id=getMemberId(sample["RecIdentifier"])),
                'collectorFK': Member.objects.get(id=getMemberId(sample["RecCollector"])),
                'substrate': sample["RecSubstrate"],
                'assoc1': sample["RecAssoc"],
                'dateFound': catchNullDate(sample["RecDate"]),
                'dateEntered': catchNullDate(sample["RecEnteredDate"]),
                'exported': sample["RecSentBMSInd"] == "TRUE",
                'dateExported': catchNullDate(sample["RecSentBMS"]),
                'remarks': sample["RecRemarks"],
                'dateUpdated': catchNullDate(sample["RecUpdDate"]),
                'updaterFK': Member.objects.get(id=getMemberId(sample["RecLastUpdater"])),
                'firstRecord': first
            }
            # datetime.datetime.strptime(sample["RecDate"], "%d/%m/%Y %H:%M").date()

            if sample["RecConfirmer"] != "":
                kwargs['confirmerFK'] = Member.objects.get(id=getMemberId(sample["RecConfirmer"]))

            Record(**kwargs).save()

            try:
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
                    'BMSdate': catchNullDate(f'{sample["BMSdd"]}/{sample["BMSmm"]}/{sample["BMSyyyy"]} 00:00'),
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
            except:
                pass

        print("RECORDS GONE DUE TO FUNGI")
        print(fungi_gone)
        print("RECORDS GONE DUE TO SITE")
        print(site_gone)
        
        print(str(count) + " records inserted")
        print('Test data inserted into database')
