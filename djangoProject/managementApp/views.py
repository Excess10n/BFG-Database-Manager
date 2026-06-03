from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import RestrictedError
from .forms import AssocForm, SubtrForm, SiteForm, RecordFilterForm, RecordForm, RecordInitialForm
from .models import Association, Substrate, Site, Record, Fungi, Member
from .viewFunctions import getFungiObjects
import datetime

# Create your views here.

def pagination(current, total):
    if current == None:
        current = 1
    current = int(current)

    pageCount = (total // 50) + 1
    start = current - 4
    end = current + 4
    if start < 1:
        diff = 1 - start
    elif end > pageCount:
        diff = pageCount - end
    else:
        diff = 0
    start += diff
    end += diff
    if end > pageCount:
        end = pageCount
    pageList = range(start, end + 1)

    if current*50 > total:
        return current, pageCount, (current-1)*50, total, pageList
    
    return current, pageCount, (current-1)*50, current*50, pageList

def IndexView(request):
    # list of pages the homepage can direct to
    context = {
        "pages": [
            {
                "title": "Bulk data input",
                "desc": "add and update records in bulk",
                "link": "/record/edit"
            },
            {
                "title": "Record browser",
                "desc": "browse the records",
                "link": "/record/browse"
            },
            {
                "title": "Fungus list",
                "desc": "browse BFG's dictionary of fungi",
                "link": "/fungus"
            },
            {
                "title": "Site details",
                "desc": "view, add, or change any site details",
                "link": "/site"
            },
            {
                "title": "Substrate list",
                "desc": "view, add, or change any substrate details",
                "link": "/substrate"
            },
            {
                "title": "Associated organisms list",
                "desc": "view, add, or change any association details",
                "link": "/association"
            },
            {
                "title": "Record export",
                "desc": "Export for the website or FRDBI",
                "link": "/export"
            },
            {
                "title": "Fungi search",
                "desc": "Get Fungi recommendations based on other data related to the fungus",
                "link": "/search"
            }
        ]
    }
    return render(request, 'index.html', context)

def RecordEditView(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()
    
    # check if delete mode is on
    delete = request.GET.get("delete") == "true"
    if delete:
        deleteText = "true"
    else:
        deleteText = "false"
    
    # the form with the 3 bits of initial data
    param = ""
    data = {}
    if request.GET.get("date") != None and request.GET.get("site") != None and request.GET.get("rec") != None:
        param = f"date={request.GET.get('date')}&site={request.GET.get('site')}&rec={request.GET.get('rec')}"
        data = {
            "date": request.GET.get('date'),
            "site": request.GET.get('site'),
            "rec": request.GET.get('rec')
        }
        try:
            # its either initilized with the params or not
            initForm = RecordInitialForm(request.POST or None, initial={
                "date": data["date"],
                "site": Site.objects.get(id=data["site"]),
                "rec": Member.objects.get(id=data["rec"])
            })
        except:
            initForm = RecordInitialForm(request.POST or None)
    else:
        initForm = RecordInitialForm(request.POST or None, initial={"rec": request.user.user_profile.member.initials})
    
    if initForm.is_valid():
        data = initForm.cleaned_data
        # get the id's of the submitted data
        try:
            site = Site.objects.get(name=data['site'])
        except:
            messages.add_message(request, messages.ERROR, f"{data['site']} not found")
            return redirect('/record/edit?' + param)
        
        try:
            rec = Member.objects.get(initials=data['rec'])
        except:
            messages.add_message(request, messages.ERROR, f"{data['rec']} not found")
            return redirect('/record/edit?' + param)

        param = f"date={data['date']}&site={site.id}&rec={rec.id}"
        return redirect('/record/edit?' + param)
    
    # get records with filters from the above data
    if data == {}:
        records = Record.objects.none()
    else:
        records = Record.objects.all().order_by('-id').filter(dateFound=data["date"], siteFK=Site.objects.get(id=data["site"]), recorderFK=Member.objects.get(id=data["rec"]))

    currentPage = request.GET.get("page")
    currentPage, pageCount, start, end, pageList = pagination(currentPage, records.count())
    records = records[start:end]

    page = {"current": currentPage, "first": currentPage == 1, "last": currentPage == pageCount, "pageCount": pageCount, "list": pageList}

    def manageForm(form, new): # function for saving record forms
        data = form.cleaned_data
        inst = form.save(commit=False)

        # get next unique code (only if this is a new entry)
        if new:
            userCodes = Record.objects.filter(uniqueCode__startswith=f"R{request.user.user_profile.member.initials}").order_by('-uniqueCode')
            if userCodes.count() == 0:
                inst.uniqueCode = f"R{request.user.user_profile.member.initials}0000000"
            else:
                lastCode = userCodes.first().uniqueCode
                num = lastCode[-7:]
                num = int(num) + 1
                num = str(num)
                add = 7 - len(num)
                for i in range(add):
                    num = "0" + num
                inst.uniqueCode = lastCode[:-7] + num

        # get values from params
        if request.GET.get("site") != None:
            inst.siteFK = Site.objects.get(id=request.GET.get("site"))
        else:
            messages.add_message(request, messages.ERROR, "Record Site hasn't been entered")
            return False
        
        if request.GET.get("rec") != None:
            inst.recorderFK = Member.objects.get(id=request.GET.get("rec"))
        else:
            messages.add_message(request, messages.ERROR, "Recorder hasn't been entered")
            return False

        if request.GET.get("date") != None:
            inst.dateFound = datetime.datetime.strptime(request.GET.get("date"), "%Y-%m-%d").date()
        else:
            messages.add_message(request, messages.ERROR, "Record Date hasn't been entered")
            return False
        
        # Fungus needs to be the fungi object not text
        try:
            current, _, _ = getFungiObjects(data["fungus"])
            inst.fungusFK = current
        except:
            messages.add_message(request, messages.ERROR, f"{data['fungus']} not found")
            return False

        # check if this record is the first in the site, bucks, or database
        if new:
            if Record.objects.filter(fungusFK=inst.fungusFK).count() == 0:
                inst.firstRecord = 'D'
            elif Record.objects.filter(fungusFK=inst.fungusFK, siteFK__in=Site.objects.filter(VC=24)).count() == 0:
                inst.firstRecord = 'B'
            elif Record.objects.filter(fungusFK=inst.fungusFK, siteFK=inst.siteFK).count() == 0:
                inst.firstRecord = 'S'
        
        inst.updaterFK = request.user.user_profile.member
        inst.dateUpdated = datetime.datetime.now()

        inst.save()
        return True

    # form list
    formList = []
    index = 0
    for record in records:
        index += 1
        form = RecordForm("Change", request.POST or None, request.FILES or None, instance=record, initial={"fungus": record.fungusFK.currentFungus.fullName}, prefix=f"form{index}")
        if form.is_valid():
            done = manageForm(form, False)
            if done:
                messages.add_message(request, messages.SUCCESS, "Edited record")
            return redirect(f"/record/edit?page={page['current']}&delete={deleteText}&{param}")
        formList.append({"form": form, "id": record.id})
    # new form
    newForm = RecordForm("New", request.POST or None, request.FILES or None, prefix="form0")
    if newForm.is_valid():
        done = manageForm(newForm, True)
        if done:
            messages.add_message(request, messages.SUCCESS, "Added new record")
        return redirect(f"/record/edit?page={page['current']}&delete={deleteText}&{param}")

    context = {"formList": formList, "newForm": newForm, "initForm": initForm, "page": page, "param": param, "delete": delete, "deleteText": deleteText}
    return render(request, 'dataManager/recordEdit.html', context)

def RecordDelete(request, id):
    if not request.user.is_authenticated:
        raise PermissionDenied()
    
    record = get_object_or_404(Record, id=id)
    
    if request.method == "POST":
        try:
            record.delete()
            messages.add_message(request, messages.SUCCESS, "Record deleted")
        except:
            messages.add_message(request, messages.ERROR, "Record failed to delete")

    # get the query paramters to be redirected to
    if request.GET.get("page") != None:
        param = f"page={request.GET.get('page')}"
    else:
        param = "page=1"

    param += "&delete=true"

    if request.GET.get("date") != None and request.GET.get("site") != None and request.GET.get("rec") != None:
        param += f"&date={request.GET.get('date')}&site={request.GET.get('site')}&rec={request.GET.get('rec')}"
    
    return redirect('/record/edit?' + param)

def RecordBrowseView(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()
    
    # get data from query params if any
    param = ""
    data = {}
    data["fungus"] = request.GET.get("fungus")
    data["site"] = request.GET.get("site")
    data["vc"] = request.GET.get("vc")
    data["recorder"] = request.GET.get("rec")
    data["collector"] = request.GET.get("coll")
    data["identifier"] = request.GET.get("idfr")
    data["confirmer"] = request.GET.get("conf")
    data["association"] = request.GET.get("assoc")
    if request.GET.get("dateFrom") != None:
        data["dateFrom"] = datetime.datetime.strptime(request.GET.get("dateFrom"), "%Y-%m-%d").date()
    else:
        data["dateFrom"] = None
    if request.GET.get("dateTo") != None:
        data["dateTo"] = datetime.datetime.strptime(request.GET.get("dateTo"), "%Y-%m-%d").date()
    else:
        data["dateTo"] = None

    filt = False
    for x in data.values():
        if x != None:
            filt = True
            break
    
    form = RecordFilterForm("Filter", request.POST or None, initial=data)
    # if form was submitted then take the data from there instead
    if form.is_valid():
        data = form.cleaned_data
        filt = True
    
    # filter process if data is present
    if filt:
        # repeatative code time
        # ---------------------
        fungus = None
        site = None
        vc = None
        recorder = None
        collector = None
        identifier = None
        confirmer = None
        association = None
        dateFrom = None
        dateTo = None

        if data["fungus"] != "" and data["fungus"] != None:
            try:
                fungus, _, _ = getFungiObjects(data["fungus"])
                param += f"fungus={data['fungus']}&"
            except:
                messages.add_message(request, messages.ERROR, f"{data['fungus']} not found")
                redirect(RecordBrowseView)

        if data["site"] != "" and data["site"] != None:
            try:
                site = Site.objects.get(name=data["site"])
                param += f"site={data['site']}&"
            except:
                messages.add_message(request, messages.ERROR, f"{data['site']} not found")
                redirect(RecordBrowseView)

        if data["vc"] != "" and data["vc"] != None:
            try:
                vc = int(data["vc"])
            except:
                messages.add_message(request, messages.ERROR, "vc is not a number")
            param += f"vc={data['vc']}&"

        if data["recorder"] != "" and data["recorder"] != None:
            try:
                recorder = Member.objects.get(initials=data["recorder"])
                param += f"rec={data['recorder']}&"
            except:
                messages.add_message(request, messages.ERROR, f"{data['recorder']} not found")
                redirect(RecordBrowseView)

        if data["collector"] != "" and data["collector"] != None:
            try:
                collector = Member.objects.get(initials=data["collector"])
                param += f"coll={data['collector']}&"
            except:
                messages.add_message(request, messages.ERROR, f"{data['collector']} not found")
                redirect(RecordBrowseView)

        if data["identifier"] != "" and data["identifier"] != None:
            try:
                identifier = Member.objects.get(initials=data["identifier"])
                param += f"idfr={data['identifier']}&"
            except:
                messages.add_message(request, messages.ERROR, f"{data['identifier']} not found")
                redirect(RecordBrowseView)

        if data["confirmer"] != "" and data["confirmer"] != None:
            try:
                confirmer = Member.objects.get(initials=data["confirmer"])
                param += f"conf={data['confirmer']}&"
            except:
                messages.add_message(request, messages.ERROR, f"{data['confirmer']} not found")
                redirect(RecordBrowseView)

        if data["association"] != "" and data["association"] != None:
            try:
                association = Association.objects.get(name=data["association"])
                param += f"assoc={data['association']}&"
            except:
                messages.add_message(request, messages.ERROR, f"{data['association']} not found")
                redirect(RecordBrowseView)

        if data["dateFrom"] != "" and data["dateFrom"] != None:
            dateFrom = data["dateFrom"]
            param += f"dateFrom={data['dateFrom']}&"
        if data["dateTo"] != "" and data["dateTo"] != None:
            dateTo = data["dateTo"]
            param += f"dateTo={data['dateTo']}&"
        # ---------------------
        if param != "":
            param = param[:-1]

        records = Record.objects.all()
        records2 = []
        for record in records:
            # repeatative code time
            # ---------------------
            if fungus != None:
                if record.fungusFK != fungus:
                    continue
            if site != None:
                if record.siteFK != site:
                    continue
            if vc != None:
                if record.siteFK.VC != vc:
                    continue
            if recorder != None:
                if record.recorderFK != recorder:
                    continue
            if collector != None:
                if record.collectorFK != collector:
                    continue
            if identifier != None:
                if record.identifierFK != identifier:
                    continue
            if confirmer != None:
                if record.confirmerFK != confirmer:
                    continue
            if association != None:
                if record.assoc1FK != association and record.assoc2FK != association and record.assoc3FK != association:
                    continue
            # ---------------------
            if dateFrom != None and dateTo != None:
                if not (dateFrom <= record.dateFound and dateTo >= record.dateFound):
                    continue
            elif dateFrom != None:
                if not (dateFrom <= record.dateFound):
                    continue
            elif dateTo != None:
                if not (dateTo >= record.dateFound):
                    continue
            
            records2.append(record)
        records = records2
        length = len(records)
    
    else:
        # if no filter get all records
        records = Record.objects.all()
        length = records.count()
    
    # pagination
    currentPage = request.GET.get("page")
    currentPage, pageCount, start, end, pageList = pagination(currentPage, length)
    records = records[start:end]

    page = {"current": currentPage, "first": currentPage == 1, "last": currentPage == pageCount, "pageCount": pageCount, "list": pageList}

    # get record to expand if any
    expand = request.GET.get("expand")
    if expand == None:
        expand = -1
    try:
        expand = int(expand)
    except:
        expand = -1

    context = {"records": records, "param": param, "form": form, "page": page, "expand": expand}
    return render(request, 'dataManager/recordBrowse.html', context)

def FungusView(request):
    context = {}
    return render(request, 'dataManager/fungus.html', context)

# ---------
# site view
# ---------

def SiteView(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()
    
    # form
    form = SiteForm(request.POST or None)
    if form.is_valid():
        inst = form.save(commit=False)
        inst.creatorFK = request.user.user_profile.member
        inst.updaterFK = request.user.user_profile.member
        inst.dateUpdated = datetime.datetime.now()
        inst.save()
        redirect(SiteView)
    
    sites = Site.objects.all().order_by('name')
    for site in sites:
        site.total = Record.objects.filter(siteFK=site).count()

    # pagination
    currentPage = request.GET.get("page")
    currentPage, pageCount, start, end, pageList = pagination(currentPage, sites.count())
    sites = sites[start:end]

    page = {"current": currentPage, "first": currentPage == 1, "last": currentPage == pageCount, "pageCount": pageCount, "list": pageList}

    # is user entering a new site
    new = request.GET.get("new") == "true"
    if new:
        newText = "true"
    else:
        newText = "false"

    context = {"newForm": form, "sites": sites, "new": new, "newText": newText, "page": page}
    return render(request, 'dataManager/site.html', context)

# ---------------
# SUBSTRATE VIEWS
# ---------------

def SubstrView(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()
    
    # check if delete mode is on
    delete = request.GET.get("delete") == "true"
    if delete:
        deleteText = "true"
    else:
        deleteText = "false"
    
    # form list
    subtrs = Substrate.objects.all().order_by('name')
    formList = []
    index = 0
    for subtr in subtrs:
        index += 1
        form = SubtrForm("Change", request.POST or None, instance=subtr, prefix=f"form{index}")
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, "Edited substrate")
            return redirect("/substrate?delete=" + deleteText)
        formList.append({"form": form, "id": subtr.id})

    # singular new form
    newForm = SubtrForm("New", request.POST or None, prefix="form0")
    if newForm.is_valid():
        newForm.save()
        messages.add_message(request, messages.SUCCESS, "Added new substrate")
        return redirect("/substrate?delete=" + deleteText)

    context = {"formList": formList, "newForm": newForm, "delete": delete, "deleteText": deleteText}
    return render(request, 'dataManager/substr.html', context)

def SubstrDelete(request, id):
    if not request.user.is_authenticated:
        raise PermissionDenied()
    
    substr = get_object_or_404(Substrate, id=id)
    
    if request.method == "POST":
        try:
            substr.delete()
            messages.add_message(request, messages.SUCCESS, "Substrate deleted")
        except RestrictedError: # if the substrate is being used by a record the delete will be blocked
            messages.add_message(request, messages.ERROR, "Delete failed: Substrate is used in 1 or more records")
        except:
            messages.add_message(request, messages.ERROR, "Delete failed")
    
    return redirect("/substrate?delete=true")

# -----------------
# ASSOCIATION VIEWS
# -----------------

def AssocView(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()
    
    # check if delete mode is on
    delete = request.GET.get("delete") == "true"
    if delete:
        deleteText = "true"
    else:
        deleteText = "false"
    
    # form list
    assocs = Association.objects.all().order_by('name')
    formList = []
    index = 0
    for assoc in assocs:
        index += 1
        form = AssocForm("Change", request.POST or None, instance=assoc, prefix=f"form{index}")
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, "Edited association")
            return redirect("/association?delete=" + deleteText)
        formList.append({"form": form, "id": assoc.id})

    # singular new form
    newForm = AssocForm("New", request.POST or None, prefix="form0")
    if newForm.is_valid():
        newForm.save()
        messages.add_message(request, messages.SUCCESS, "Added new association")
        return redirect("/association?delete=" + deleteText)

    context = {"formList": formList, "newForm": newForm, "delete": delete, "deleteText": deleteText}
    return render(request, 'dataManager/assoc.html', context)

def AssocDelete(request, id):
    if not request.user.is_authenticated:
        raise PermissionDenied()
    
    assoc = get_object_or_404(Association, id=id)
    
    if request.method == "POST":
        try:
            assoc.delete()
            messages.add_message(request, messages.SUCCESS, "Association deleted")
        except RestrictedError: # if the assoc is being used by a record the delete will be blocked
            messages.add_message(request, messages.ERROR, "Delete failed: Association is used in 1 or more records")
        except:
            messages.add_message(request, messages.ERROR, "Delete failed")
    
    return redirect("/association?delete=true")





def ExportView(request):
    context = {}
    return render(request, 'export/export.html', context)