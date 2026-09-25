from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.db.models import RestrictedError, Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from .forms import AssocForm, SubtrForm, SiteForm, SiteSearchForm, RecordOrderForm, RecordFilterForm, RecordForm, RecordFormBrowse, RecordInitialForm, MemberForm, MemberSearchForm, MemberLoginForm, ReportExportForm, FRDBIExportForm, FungiForm, FungiSearchForm
from .models import Association, Substrate, Site, Record, RecordArchive, Fungi, FungiCurrent, FungiArchive, Member, MemberLogin
from django.contrib.auth.models import User, Permission
from .viewFunctions import getFungiObjects, createNewCurrentFungi, databaseBackupOverwrite, databaseBackupOverwriteBuffered
import datetime
import io
import itertools
import os
import logging
import zipfile

import pypandoc

# returns True if the current user is manager, False if member
# alternatively you can set admin to True to only return True if the current user is a member
def checkPerms(user, admin=False):
    if admin:
        if user.is_superuser:
            return True
        else:
            return False
        
    if user.has_perm("managementApp.manager"):
        return True
    else:
        return False

# function for pagination calculations
# takes the current page of the user, the total number of items to be displayed, and the max number of items to be displayed on 1 page
# returns current page, the number of pages, the index of the first and last item to be displayed, the total items displayed, and page number options to be displayed to the user
def pagination(current, total, max=50):
    if current == None:
        current = 1
    current = int(current)

    pageCount = (total // max) + 1
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

    if current*max > total:
        return current, pageCount, (current-1)*max, total, pageList
    
    return current, pageCount, (current-1)*max, current*max, pageList

# provides the index page with the relevant information
def IndexView(request):
    isManager = checkPerms(request.user)
    if isManager:
        context = {
            # list of pages the index page can direct to
            "pages": [
                {
                    "title": "Bulk data input",
                    "desc": "add and update records in bulk",
                    "link": "/record/edit"
                },
                {
                    "title": "Record browser",
                    "desc": "browse and edit records",
                    "link": "/record/browse"
                },
                {
                    "title": "Fungus dictionary",
                    "desc": "browse BFG's dictionary of fungi",
                    "link": "/fungus"
                },
                {
                    "title": "Site details",
                    "desc": "add or change any site details",
                    "link": "/site"
                },
                {
                    "title": "Member details",
                    "desc": "add or change any member details",
                    "link": "/member"
                },
                {
                    "title": "Substrate list",
                    "desc": "edit the substrate dropdown list",
                    "link": "/substrate"
                },
                {
                    "title": "Associated organisms list",
                    "desc": "edit the associations dropdown list",
                    "link": "/association"
                },
                {
                    "title": "Record export",
                    "desc": "export for the website, FRDBI, or site owners",
                    "link": "/export"
                }
            ],
            "isManager": isManager
        }
    else:
        context = {
            "pages": [
                {
                    "title": "Record browser",
                    "desc": "browse the records",
                    "link": "/record/browse"
                }
            ],
            "isManager": isManager
        }
    if request.user.is_authenticated:
        return render(request, 'index.html', context)
    else:
        # provide the landing page instead if the user is not logged in
        return render(request, 'index_landing.html', context)

# records are edited in multiple different locations so the logic for saving those forms is this function
# takes the form itself, if the record is new, and if the record is being edited through the browser or not (True for browser, False for bulk)
# returns True is successful, False if failed, the reason for failing will be added to messages
def manageForm(form, new, edit, request):
    data = form.cleaned_data
    inst = form.save(commit=False)

    def get_member(full_name, label):
        if not full_name:
            return None
        try:
            return Member.objects.get(fullName=full_name)
        except Member.DoesNotExist:
            messages.add_message(request, messages.ERROR, f"Name \"{label}\" not found")
            return None

    def get_site(name):
        try:
            return Site.objects.get(name=name)
        except Site.DoesNotExist:
            messages.add_message(request, messages.ERROR, f"Site \"{name}\" not found")
            return None

    # get values from the pre-selected site, recorder, and date params (bulk only)
    if not edit:
        site_id = request.GET.get("site")
        if site_id is not None:
            inst.siteFK = Site.objects.get(id=site_id)
        else:
            messages.add_message(request, messages.ERROR, "Record Site hasn't been entered")
            return False

        if new: # recorder is only added to the record if its new
            recorder_id = request.GET.get("rec")
            if recorder_id is not None:
                inst.recorderFK = Member.objects.get(id=recorder_id)
            else:
                messages.add_message(request, messages.ERROR, "Recorder hasn't been entered")
                return False

        date_value = request.GET.get("date")
        if date_value is not None:
            inst.dateFound = datetime.datetime.strptime(date_value, "%Y-%m-%d").date()
        else:
            messages.add_message(request, messages.ERROR, "Record Date hasn't been entered")
            return False

        # create the next availible unique code (only if this is a new entry)
        if new:
            nameCode = inst.recorderFK.initials
            userCodes = Record.objects.filter(uniqueCode__startswith=f"BFG{nameCode}").order_by('-uniqueCode')
            if userCodes.exists():
                lastCode = userCodes.first().uniqueCode
                num = int(lastCode[-7:]) + 1
                inst.uniqueCode = f"{lastCode[:-7]}{num:07d}"
            else:
                inst.uniqueCode = f"BFG{nameCode}0000001"

    # if this is not bulk entered the site and member must be retrived from the form
    else:
        site = get_site(data["site"])
        if site is None:
            return False
        inst.siteFK = site

        recorder = get_member(data["recorderFK"], data["recorderFK"])
        if recorder is None:
            return False
        inst.recorderFK = recorder

        # DNATest must be "Yes" for a DNAseq to be provided
        if data['DNAseq'] not in ("", None) and data['DNATest'] != "Yes":
            inst.DNAseq = ""
            messages.add_message(request, messages.ERROR, "DNA Sequence not submitted because the DNA Test? option has not been set to yes")

    # ensure all other fields are valid (and change the provided text into an actual object where required)
    try:
        current, _, _ = getFungiObjects(data["fungus"])
        inst.fungusFK = current
    except:
        messages.add_message(request, messages.ERROR, f"Fungus \"{data['fungus']}\" not found")
        return False

    identifier = get_member(data["identifierFK"], data["identifierFK"])
    if identifier is None:
        return False
    inst.identifierFK = identifier

    confirmer = None
    if data["confirmerFK"]:
        confirmer = get_member(data["confirmerFK"], data["confirmerFK"])
        if confirmer is None:
            return False
    inst.confirmerFK = confirmer

    collector = get_member(data["collectorFK"], data["collectorFK"])
    if collector is None:
        return False
    inst.collectorFK = collector

    photographer = None
    if data["photographerFK"]:
        photographer = get_member(data["photographerFK"], data["photographerFK"])
        if photographer is None:
            return False
    inst.photographerFK = photographer

    if data["substrate"] == "":
        messages.add_message(request, messages.ERROR, f"Substrate is empty")
        return False
    inst.substrate = data["substrate"]
    if data["assoc1"] != "":
        inst.assoc1 = data["assoc1"]
    if data["assoc2"] != "":
        inst.assoc2 = data["assoc2"]
    if data["assoc3"] != "":
        inst.assoc3 = data["assoc3"]

    # check if this record is the first in the site, bucks, or database
    site_history = list(
        Record.objects.filter(fungusFK=inst.fungusFK)
        .values_list("siteFK_id", "siteFK__VC")
    )
    if not site_history:
        inst.firstRecord = 'D'
    elif not any(vic == 24 for _, vic in site_history):
        inst.firstRecord = 'B'
    elif not any(site_id == inst.siteFK_id for site_id, _ in site_history):
        inst.firstRecord = 'S'

    # changed updater and the date it was updated
    inst.updaterFK = request.user.user_profile
    inst.dateUpdated = datetime.datetime.now()

    inst.save()
    return True

# this was AI generated for a singular purpose only, do not touch
def _get_submitted_record_form_prefix(post_data):
    for key in post_data.keys():
        if key.startswith("form") and "-" in key:
            return key.split("-", 1)[0]
    return None


def RecordEditView(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    # check if delete mode is on
    delete = request.GET.get("delete") == "true"
    if delete:
        deleteText = "true"
    else:
        deleteText = "false"

    # get page
    currentPage = request.GET.get("page")
    if currentPage == None or currentPage == "None":
        currentPage = 1
    
    # the form with the 3 bits of initial data
    param = ""
    data = {}
    init_form_post = (
        request.POST
        if request.method == "POST"
        and all(field in request.POST for field in ("date", "site", "rec"))
        else None
    )
    if request.GET.get("date") != None and request.GET.get("site") != None and request.GET.get("rec") != None:
        param = f"date={request.GET.get('date')}&site={request.GET.get('site')}&rec={request.GET.get('rec')}"
        data = {
            "date": request.GET.get('date'),
            "site": request.GET.get('site'),
            "rec": request.GET.get('rec')
        }
        try:
            # its either initilized with the params or not
            initForm = RecordInitialForm(init_form_post, initial={
                "date": data["date"],
                "site": Site.objects.get(id=data["site"]),
                "rec": Member.objects.get(id=data["rec"])
            })
        except:
            initForm = RecordInitialForm(init_form_post)
        initPresent = True
    else:
        initForm = RecordInitialForm(init_form_post, initial={"rec": request.user.user_profile.fullName})
        initPresent = False
    
    if initForm.is_valid():
        data = initForm.cleaned_data
        # get the id's of the submitted data
        try:
            site = Site.objects.get(name=data['site'])
        except:
            messages.add_message(request, messages.ERROR, f"site \"{data['site']}\" not found")
            return redirect('/record/edit?' + param)
        
        try:
            rec = Member.objects.get(fullName=data['rec'])
        except:
            messages.add_message(request, messages.ERROR, f"name \"{data['rec']}\" not found")
            return redirect('/record/edit?' + param)

        param = f"date={data['date']}&site={site.id}&rec={rec.id}"
        return redirect('/record/edit?' + param)
    
    # get records with filters from the above data
    if data == {}:
        records = Record.objects.none()
    else:
        records = Record.objects.all().order_by('-id').filter(dateFound=data["date"], siteFK=Site.objects.get(id=data["site"]))#, recorderFK=Member.objects.get(id=data["rec"]))

    # record orderings
    order = request.GET.get("order")
    if order == None:
        order = "1"
    order_form_post = (
        request.POST
        if request.method == "POST" and "orderform-order" in request.POST
        else None
    )
    orderForm = RecordOrderForm(order_form_post, initial={"order": order}, prefix="orderform")
    if request.method == "POST" and f"{orderForm.prefix}-order" in request.POST:
        if orderForm.is_valid():
            order = orderForm.cleaned_data["order"]
            param += f"&order={order}"
            return redirect(f"/record/edit?page={currentPage}&delete={deleteText}&{param}")
    
    param += f"&order={order}"

    submitted_prefix = None
    if request.method == "POST":
        submitted_prefix = _get_submitted_record_form_prefix(request.POST)

    if request.method == "POST" and submitted_prefix:
        if submitted_prefix == "form0":
            newForm = RecordForm("New", request.POST if submitted_prefix == "form0" else None, request.FILES or None, prefix="form0")
            if newForm.is_valid():
                done = manageForm(newForm, True, False, request)
                if done:
                    messages.add_message(request, messages.INFO, "Added new record")
                    return redirect(f"/record/edit?page={currentPage}&delete={deleteText}&{param}&last=new")
        else:
            try:
                record_index = int(submitted_prefix.replace("form", "")) - 1
            except ValueError:
                record_index = None

            if record_index is not None and 0 <= record_index < len(records):
                record = records[record_index]
                init = {
                    "fungus": record.fungusFK.currentFungus.fullName,
                    "collectorFK": record.collectorFK.fullName,
                    "identifierFK": record.identifierFK.fullName,
                    "substrate": record.substrate
                }
                if record.confirmerFK != None:
                    init["confirmerFK"] = record.confirmerFK.fullName
                if record.photographerFK != None:
                    init["photographerFK"] = record.photographerFK.fullName
                if record.assoc1 != None:
                    init["assoc1"] = record.assoc1
                if record.assoc2 != None:
                    init["assoc2"] = record.assoc2
                if record.assoc3 != None:
                    init["assoc3"] = record.assoc3

                form = RecordForm("Change", request.POST or None, request.FILES or None, instance=record, initial=init, prefix=submitted_prefix)
                if form.is_valid():
                    done = manageForm(form, False, False, request)
                    if done:
                        messages.add_message(request, messages.INFO, "Edited record")
                        return redirect(f"/record/edit?page={currentPage}&delete={deleteText}&{param}&last={record.id}")

    # form list
    formList = []
    index = 0
    for record in records:
        index += 1
        prefix = f"form{index}"
        init = {
            "fungus": record.fungusFK.currentFungus.fullName,
            "collectorFK": record.collectorFK.fullName,
            "identifierFK": record.identifierFK.fullName,
            "substrate": record.substrate
        }
        if record.confirmerFK != None:
            init["confirmerFK"] = record.confirmerFK.fullName
        if record.photographerFK != None:
            init["photographerFK"] = record.photographerFK.fullName
        if record.assoc1 != None:
            init["assoc1"] = record.assoc1
        if record.assoc2 != None:
            init["assoc2"] = record.assoc2
        if record.assoc3 != None:
            init["assoc3"] = record.assoc3

        form = RecordForm(
            "Change",
            request.POST if prefix == submitted_prefix else None,
            request.FILES or None,
            instance=record,
            initial=init,
            prefix=prefix,
        )

        dic = {"form": form, "id": record.id, "name": record.fungusFK.currentFungus.fullName, "date": record.dateFound}
        if order == "2":
            for i in range(len(formList)):
                if record.fungusFK.currentFungus.fullName < formList[i]["name"]:
                    formList.insert(i, dic)
                    break
            else:
                formList.append(dic)
        else:
            formList.append(dic)

    # pagination
    currentPage, pageCount, start, end, pageList = pagination(currentPage, records.count(), 15)
    formList = formList[start:end]

    page = {"current": currentPage, "first": currentPage == 1, "last": currentPage == pageCount, "pageCount": pageCount, "list": pageList}

    # new form
    newForm = RecordForm("New", request.POST if submitted_prefix == "form0" else None, request.FILES or None, prefix="form0")

    # get species count
    species = records.values_list("fungusFK_id", flat=True).distinct().count()
    #Record.objects.values_list("fungusFK_id", flat=True).distinct()

    context = {"formList": formList, "newForm": newForm, "initForm": initForm, "orderForm": orderForm, "page": page, "param": param, "delete": delete, "deleteText": deleteText, "initPresent": initPresent, "last": request.GET.get('last'), "species": species}
    return render(request, 'dataManager/recordEdit.html', context)

def RecordDelete(request, id):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    record = get_object_or_404(Record, id=id)
    
    if request.method == "POST":
        try:
            record.delete()
            messages.add_message(request, messages.INFO, "Record deleted")
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

    if request.GET.get("order") != None:
        param += f"&order={request.GET.get('order')}"
    
    return redirect('/record/edit?' + param)

def RecordBrowseView(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    isManager = checkPerms(request.user)
    
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
    data["substrate"] = request.GET.get("subtr")
    data["association"] = request.GET.get("assoc")
    data["month"] = request.GET.get("month")
    if request.GET.get("dateFrom") != None:
        data["dateFrom"] = datetime.datetime.strptime(request.GET.get("dateFrom"), "%Y-%m-%d").date()
    else:
        data["dateFrom"] = None
    if request.GET.get("dateTo") != None:
        data["dateTo"] = datetime.datetime.strptime(request.GET.get("dateTo"), "%Y-%m-%d").date()
    else:
        data["dateTo"] = None
    if request.GET.get("dateSingle") != None:
        data["dateSingle"] = datetime.datetime.strptime(request.GET.get("dateSingle"), "%Y-%m-%d").date()
    else:
        data["dateSingle"] = None

    currentPage = request.GET.get("page")

    filt = False
    for x in data.values():
        if x != None:
            filt = True
            break
    
    form = RecordFilterForm("Filter", request.POST or None, initial=data, prefix="filterform")
    # if form was submitted then take the data from there instead
    if form.is_valid():
        data = form.cleaned_data
        filt = True
        currentPage = 1
    
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
        substrate = None
        association = None
        dateFrom = None
        dateTo = None
        dateSingle = None
        month = None

        if data["fungus"] != "" and data["fungus"] != None:
            fungus, _, _ = getFungiObjects(data["fungus"])
            if fungus == None:
                messages.add_message(request, messages.ERROR, f"Fungus \"{data['fungus']}\" not found")
                redirect(RecordBrowseView)
            param += f"fungus={data['fungus']}&"

        if data["site"] != "" and data["site"] != None:
            try:
                site = Site.objects.get(name=data["site"])
                param += f"site={data['site']}&"
            except:
                messages.add_message(request, messages.ERROR, f"Site \"{data['site']}\" not found")
                redirect(RecordBrowseView)

        if data["vc"] != "" and data["vc"] != None:
            try:
                vc = int(data["vc"])
            except:
                messages.add_message(request, messages.ERROR, "The entered vc is not a number")
            param += f"vc={data['vc']}&"

        if data["recorder"] != "" and data["recorder"] != None:
            try:
                recorder = Member.objects.get(fullName=data["recorder"])
                param += f"rec={data['recorder']}&"
            except:
                messages.add_message(request, messages.ERROR, f"Name \"{data['recorder']}\" not found")
                redirect(RecordBrowseView)

        if data["collector"] != "" and data["collector"] != None:
            try:
                collector = Member.objects.get(fullName=data["collector"])
                param += f"coll={data['collector']}&"
            except:
                messages.add_message(request, messages.ERROR, f"Name \"{data['collector']}\" not found")
                redirect(RecordBrowseView)

        if data["identifier"] != "" and data["identifier"] != None:
            try:
                identifier = Member.objects.get(fullName=data["identifier"])
                param += f"idfr={data['identifier']}&"
            except:
                messages.add_message(request, messages.ERROR, f"Name \"{data['identifier']}\" not found")
                redirect(RecordBrowseView)

        if data["confirmer"] != "" and data["confirmer"] != None:
            try:
                confirmer = Member.objects.get(fullName=data["confirmer"])
                param += f"conf={data['confirmer']}&"
            except:
                messages.add_message(request, messages.ERROR, f"Name \"{data['confirmer']}\" not found")
                redirect(RecordBrowseView)

        if data["substrate"] != "" and data["substrate"] != None:
            substrate = data["substrate"]
            param += f"subtsr={data['substrate']}&"

        if data["association"] != "" and data["association"] != None:
            association = data["association"]
            param += f"assoc={data['association']}&"

        if data["dateFrom"] != "" and data["dateFrom"] != None:
            dateFrom = data["dateFrom"]
            param += f"dateFrom={data['dateFrom']}&"
        if data["dateTo"] != "" and data["dateTo"] != None:
            dateTo = data["dateTo"]
            param += f"dateTo={data['dateTo']}&"
        if data["dateSingle"] != "" and data["dateSingle"] != None:
            dateSingle = data["dateSingle"]
            param += f"dateSingle={data['dateSingle']}&"
        
        if data["month"] != "" and data["month"] != None:
            try:
                month = int(data["month"])
            except:
                messages.add_message(request, messages.ERROR, "The entered month is not a number")
            param += f"month={data['month']}&"

        # ---------------------
        if param != "":
            param = param[:-1]

        records = Record.objects.all().order_by("-dateFound", "fungusFK__currentFungus__fullName")

        # substrate and assoc filters
        if substrate != None:
            records = records.filter(substrate__icontains=substrate)
        if association != None:
            records = records.filter(
                Q(assoc1__icontains=association)
                | Q(assoc2__icontains=association)
                | Q(assoc3__icontains=association)
            )
        if fungus != None:
            records = records.filter(fungusFK=fungus)
        if site != None:
            records = records.filter(siteFK=site)
        if vc != None:
            records = records.filter(siteFK__VC=vc)
        if recorder != None:
            records = records.filter(recorderFK=recorder)
        if collector != None:
            records = records.filter(collectorFK=collector)
        if identifier != None:
            records = records.filter(identifierFK=identifier)
        if confirmer != None:
            records = records.filter(confirmerFK=confirmer)

        if dateSingle != None:
            records = records.filter(dateFound=dateSingle)
        elif dateFrom != None and dateTo != None:
            records = records.filter(dateFound__range=[dateFrom, dateTo])
        elif dateFrom != None:
            records = records.filter(dateFound__gte=dateFrom)
        elif dateTo != None:
            records = records.filter(dateTo__lte=dateTo)

        if month != None:
            records = records.filter(dateFound__month=month)

        # records2 = []
        # for record in records:
        #     # repeatative code time
        #     # ---------------------
        #     if fungus != None:
        #         if record.fungusFK != fungus:
        #             continue
        #     if site != None:
        #         if record.siteFK != site:
        #             continue
        #     if vc != None:
        #         if record.siteFK.VC != vc:
        #             continue
        #     if recorder != None:
        #         if record.recorderFK != recorder:
        #             continue
        #     if collector != None:
        #         if record.collectorFK != collector:
        #             continue
        #     if identifier != None:
        #         if record.identifierFK != identifier:
        #             continue
        #     if confirmer != None:
        #         if record.confirmerFK != confirmer:
        #             continue
            
        #     # ---------------------
        #     if dateSingle != None:
        #         if not (dateSingle == record.dateFound):
        #             continue
        #     elif dateFrom != None and dateTo != None:
        #         if not (dateFrom <= record.dateFound and dateTo >= record.dateFound):
        #             continue
        #     elif dateFrom != None:
        #         if not (dateFrom <= record.dateFound):
        #             continue
        #     elif dateTo != None:
        #         if not (dateTo >= record.dateFound):
        #             continue
            
        #     if month != None:
        #         if record.dateFound.month != month:
        #             continue
            
            
        #     records2.append(record)
        # records = records2
        length = len(records)
    
    else:
        # if no filter get all records
        records = Record.objects.all().order_by("-dateFound", "fungusFK__currentFungus__fullName")
        length = records.count()

    # pagination
    
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

    context = {"records": records, "param": param, "form": form, "page": page, "expand": expand, "isManager": isManager}
    return render(request, 'dataManager/recordBrowse.html', context)

def RecordEditSingle(request, id):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    record = get_object_or_404(Record, id=id)

    param = ""
    deleteOption = False
    for key, value in request.GET.items():
        if key == "deleteOption":
            deleteOption = value == "True"
            continue
        if value is not None:
            param += f"{key}={value}&"
    if param:
        param = param[:-1]

    init = {
        "fungus": record.fungusFK.currentFungus.fullName,
        "collectorFK": record.collectorFK.fullName,
        "identifierFK": record.identifierFK.fullName,
        "recorderFK": record.recorderFK.fullName,
        "substrate": record.substrate,
        "site": record.siteFK.name
    }
    if record.confirmerFK != None:
        init["confirmerFK"] = record.confirmerFK.fullName
    if record.photographerFK != None:
        init["photographerFK"] = record.photographerFK.fullName
    if record.assoc1 != None:
        init["assoc1"] = record.assoc1
    if record.assoc2 != None:
        init["assoc2"] = record.assoc2
    if record.assoc3 != None:
        init["assoc3"] = record.assoc3

    form = RecordFormBrowse("Change", request.POST or None, request.FILES or None, initial=init, instance=record)
    if form.is_valid():
        done = manageForm(form, False, True, request)
        if done:
            messages.add_message(request, messages.INFO, "Edited record")
            return redirect(f"/record/browse/{id}?{param}")
    
    context = {"record": record, "form": form, "param": param, "deleteOption": deleteOption}
    return render(request, 'dataManager/recordEditSingle.html', context)

def RecordDelete2(request, id):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    record = get_object_or_404(Record, id=id)

    # get the query paramters to be redirected to
    param = ""
    for key, value in request.GET.items():
        if value is not None:
            param += f"{key}={value}&"
    if param:
        param = param[:-1]
    
    if request.method == "POST":
        try:
            record.delete()
            messages.add_message(request, messages.INFO, "Record deleted")
        except:
            messages.add_message(request, messages.ERROR, "Record failed to delete")
            return redirect(f"/record/browse/{id}?{param}")
    
    return redirect('/record/browse?' + param)

# -----------
# fungi views
# -----------

def clean_synonyms(text):
    print(text)
    spl = text.split("\n")
    arr = []
    for s in spl:
        if s.strip() != "":
            arr.append(s.strip())
    return arr

def FungusView(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    param = ""
    new = request.GET.get("new") == "true"
    if new:
        param += "new=true&"
    else:
        param += "new=false&"

    fungus = request.GET.get("search")
    searchForm = FungiSearchForm(request.POST or None, initial={"fungus": fungus}, prefix="searchForm")
    if request.method == "POST" and "searchForm-fungus" in request.POST:
        if searchForm.is_valid():
            fungus = searchForm.cleaned_data["fungus"]
            param += f"search={fungus}&"
            return redirect('/fungus?' + param)
    else:
        if fungus != None:
            param += f"search={fungus}&"

    form = FungiForm("Add", request.POST or None, prefix="newForm")
    if form.is_valid():
        inst = form.save(commit=False)
        inst.creatorFK = request.user.user_profile
        inst.updaterFK = request.user.user_profile
        inst.dateUpdated = datetime.datetime.now()
        inst.save()
        curr = createNewCurrentFungi(inst.id)
        # handle alt names
        alts = clean_synonyms(form.cleaned_data["synonyms"])
        for alt in alts:
            kwargs = {
                'fullName': alt,
                'englishName': "",
                'author': "",
                'group': "",
                'taxonGroup': "",
                'currentTVK': "",
                'currentName': curr,
                'dateUpdated': datetime.datetime.now(),
                'creatorFK': request.user.user_profile,
                'updaterFK': request.user.user_profile
            }
            Fungi(**kwargs).save()
        messages.add_message(request, messages.INFO, "Added new fungus")
        return redirect('/fungus?' + param)
    
    if fungus != None:
        # if this is true then the name provided is an old name and the new one should be returned
        if Fungi.objects.filter(fullName=fungus, currentName__isnull=False).exists():
            _, current, _ = getFungiObjects(fungus)
            fungus = current.fullName
        fungi = Fungi.objects.filter(fullName__icontains=fungus, currentName=None).order_by('fullName')
    else:
        fungi = Fungi.objects.filter(currentName=None).order_by('fullName')

    currentPage = request.GET.get("page")
    currentPage, pageCount, start, end, pageList = pagination(currentPage, fungi.count())
    fungi = fungi[start:end]

    page = {"current": currentPage, "first": currentPage == 1, "last": currentPage == pageCount, "pageCount": pageCount, "list": pageList}

    context = {"newForm": form, "searchForm": searchForm, "new": new, "fungi": fungi, "param": param, "page": page}
    return render(request, 'dataManager/fungus.html', context)


def FungusEditSingle(request, id):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    fungus = get_object_or_404(Fungi, id=id)

    param = ""
    deleteOption = False
    for key, value in request.GET.items():
        if key == "deleteOption":
            deleteOption = value == "True"
            continue
        if key == "new":
            continue
        if value is not None:
            param += f"{key}={value}&"
    if param:
        param = param[:-1]

    # get existing alts
    _, _, existing = getFungiObjects(fungus.fullName)
    existing = existing.values_list("fullName", flat=True)
    string = ""
    for e in existing:
        string = string + e + "\n"
    string = string[:-1]

    form = FungiForm("Change", request.POST or None, instance=fungus, initial={"synonyms": string})
    if form.is_valid():
        inst = form.save(commit=False)
        inst.updaterFK = request.user.user_profile
        inst.dateUpdated = datetime.datetime.now()
        inst.save()
        # handle alt names
        alts = clean_synonyms(form.cleaned_data["synonyms"])
        toAdd = []
        toDelete = []
        for alt in alts:
            if not alt in existing:
                toAdd.append(alt)
        for ex in existing:
            if not ex in alts:
                toDelete.append(ex)
        
        for delete in toDelete:
            Fungi.objects.get(fullName=delete).delete()

        curr, _, _ = getFungiObjects(inst.fullName)

        for add in toAdd:
            kwargs = {
                'fullName': add,
                'englishName': "",
                'author': "",
                'group': "",
                'taxonGroup': "",
                'currentTVK': "",
                'currentName': curr,
                'dateUpdated': datetime.datetime.now(),
                'creatorFK': request.user.user_profile,
                'updaterFK': request.user.user_profile
            }
            Fungi(**kwargs).save()
        
        messages.add_message(request, messages.INFO, "Edited fungus")
        return redirect(f"/fungus/{id}?{param}")
    
    context = {"fungus": fungus, "form": form, "param": param, "deleteOption": deleteOption}
    return render(request, 'dataManager/fungusEditSingle.html', context)


def FungusDelete(request, id):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    fungus = get_object_or_404(Fungi, id=id)

    param = ""
    for key, value in request.GET.items():
        if value is not None:
            param += f"{key}={value}&"
    if param:
        param = param[:-1]
    
    if request.method == "POST":
        current, _, _ = getFungiObjects(fungus.fullName)
        try:
            current.delete()
            fungus.delete()
            messages.add_message(request, messages.INFO, "Fungus deleted")
        except RestrictedError:
            messages.add_message(request, messages.ERROR, "Delete failed: Fungus is used in 1 or more records")
            return redirect(f"/fungus/{id}?{param}")
        except:
            messages.add_message(request, messages.ERROR, "Fungus failed to delete")
            return redirect(f"/fungus/{id}?{param}")
    
    return redirect('/fungus?' + param)

# ----------
# site views
# ----------

def SiteView(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    param = ""
    # is user entering a new site
    new = request.GET.get("new") == "true"
    if new:
        param += "new=true&"
    else:
        param += "new=false&"

    # search
    site = request.GET.get("search")
    searchForm = SiteSearchForm(request.POST or None, initial={"site": site}, prefix="searchForm")
    if request.method == "POST" and "searchForm-site" in request.POST:
        if searchForm.is_valid():
            site = searchForm.cleaned_data["site"]
            param += f"search={site}&"
            return redirect('/site?' + param)
    else:
        if site != None:
            param += f"search={site}&"

    # form
    form = SiteForm("Add", request.POST or None, prefix="newForm")
    if form.is_valid():
        inst = form.save(commit=False)
        inst.creatorFK = request.user.user_profile
        inst.updaterFK = request.user.user_profile
        inst.dateUpdated = datetime.datetime.now()
        inst.save()
        messages.add_message(request, messages.INFO, "Added new site")
        return redirect('/site?' + param)
    
    if site != None:
        sites = Site.objects.all().filter(name__icontains=site).order_by('name')
    else:
        sites = Site.objects.all().order_by('name')

    # pagination
    currentPage = request.GET.get("page")
    currentPage, pageCount, start, end, pageList = pagination(currentPage, sites.count())
    sites = sites[start:end]

    for site in sites:
        site.total = Record.objects.filter(siteFK=site).count()

    page = {"current": currentPage, "first": currentPage == 1, "last": currentPage == pageCount, "pageCount": pageCount, "list": pageList}


    context = {"newForm": form, "searchForm": searchForm, "new": new, "sites": sites, "param": param, "page": page}
    return render(request, 'dataManager/site.html', context)

def SiteEditSingle(request, id):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    site = get_object_or_404(Site, id=id)

    param = ""
    deleteOption = False
    for key, value in request.GET.items():
        if key == "deleteOption":
            deleteOption = value == "True"
            continue
        if key == "new":
            continue
        if value is not None:
            param += f"{key}={value}&"
    if param:
        param = param[:-1]

    form = SiteForm("Change", request.POST or None, instance=site)
    if form.is_valid():
        inst = form.save(commit=False)
        inst.updaterFK = request.user.user_profile
        inst.dateUpdated = datetime.datetime.now()
        inst.save()
        messages.add_message(request, messages.INFO, "Edited site")
        return redirect(f"/site/{id}?{param}")
    
    context = {"site": site, "form": form, "param": param, "deleteOption": deleteOption}
    return render(request, 'dataManager/siteEditSingle.html', context)

def SiteDelete(request, id):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    site = get_object_or_404(Site, id=id)

    # get the query paramters to be redirected to
    param = ""
    for key, value in request.GET.items():
        if value is not None:
            param += f"{key}={value}&"
    if param:
        param = param[:-1]
    
    if request.method == "POST":
        try:
            site.delete()
            messages.add_message(request, messages.INFO, "Site deleted")
        except RestrictedError: # if the site is being used by a record the delete will be blocked
            messages.add_message(request, messages.ERROR, "Delete failed: Site is used in 1 or more records")
            return redirect(f"/site/{id}?{param}")
        except:
            messages.add_message(request, messages.ERROR, "Site failed to delete")
            return redirect(f"/site/{id}?{param}")
    
    return redirect('/site?' + param)

# ------------
# MEMBER VIEWS
# ------------
def MemberView(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    param = ""
    # is user entering a new site
    new = request.GET.get("new") == "true"
    if new:
        param += "new=true&"
    else:
        param += "new=false&"

    # search
    member = request.GET.get("search")
    searchForm = MemberSearchForm(request.POST or None, initial={"member": member}, prefix="searchForm")
    if request.method == "POST" and "searchForm-member" in request.POST:
        if searchForm.is_valid():
            member = searchForm.cleaned_data["member"]
            param += f"search={member}&"
            return redirect('/member?' + param)
    else:
        if member != None:
            param += f"search={member}&"

    # BFGmember login
    if MemberLogin.objects.count() == 0:
        login = None
        loginForm = MemberLoginForm("Change", request.POST or None, prefix="loginForm")
    else:
        login = MemberLogin.objects.first()
        loginForm = MemberLoginForm("Change", request.POST or None, prefix="loginForm", initial={"username": login.username})

    if request.method == "POST" and "loginForm-username" in request.POST:
        if loginForm.is_valid():
            username = loginForm.cleaned_data["username"]
            password = loginForm.cleaned_data["password"]
            conf = loginForm.cleaned_data["confPassword"]
            if username == "" or password == "" or conf == "":
                messages.add_message(request, messages.ERROR, f"username or password field is empty")
                return redirect(f"/member")
            if password != conf:
                messages.add_message(request, messages.ERROR, f"Passwords do not match")
                return redirect(f"/member")
    
            if login != None:
                user = User.objects.get(username=login.username)
                user.set_password(password)
                user.username = username
                user.save()
                login.username = username
                login.save()
                messages.add_message(request, messages.INFO, "Changed member login details")
                return redirect(f"/member")
            
            user = User.objects.create_user(username, None, password)
            permission = Permission.objects.get(codename='member')
            user.user_permissions.add(permission)
            MemberLogin(username=username).save()
            messages.add_message(request, messages.INFO, "Changed member login details")
            return redirect(f"/member")

    # form
    form = MemberForm("Add", request.POST or None, prefix="newForm")
    if form.is_valid():
        inst = form.save(commit=False)
        if inst.initials.isalpha():
            numbers = []
            for m in Member.objects.filter(initials__icontains=inst.initials).order_by('initials'):
                num = ""
                index = -1
                while num.isnumeric() or num == "":
                    num = m.initials[index] + num
                    index -= 1
                num = num[1:]
                if num == "":
                    num = "1"
                numbers.append(int(num))

            index = 1
            while True:
                if index in numbers:
                    index += 1
                else:
                    break

            if index != 1:
                inst.initials = inst.initials + str(index)

        else:
            messages.add_message(request, messages.ERROR, "New member not added: Initials must not have a number (as this is automatically assigned)")
            return redirect('/member?' + param)
        
        inst.dateUpdated = datetime.datetime.now()
        inst.save()
        messages.add_message(request, messages.INFO, "Added new member")
        return redirect('/member?' + param)
    
    if member != None:
        members = Member.objects.all().filter(fullName__icontains=member).order_by('fullName')
    else:
        members = Member.objects.all().order_by('fullName')

    # pagination
    currentPage = request.GET.get("page")
    currentPage, pageCount, start, end, pageList = pagination(currentPage, members.count())
    members = members[start:end]

    page = {"current": currentPage, "first": currentPage == 1, "last": currentPage == pageCount, "pageCount": pageCount, "list": pageList}

    for member in members:
        member.total = Record.objects.filter(
            Q(recorderFK=member)
            | Q(identifierFK=member)
            | Q(confirmerFK=member)
            | Q(collectorFK=member)
        ).count()

    context = {"newForm": form, "searchForm": searchForm, "loginForm": loginForm, "new": new, "members": members, "param": param, "page": page}
    return render(request, 'dataManager/member.html', context)

def MemberEditSingle(request, id):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    member = get_object_or_404(Member, id=id)

    param = ""
    deleteOption = False
    for key, value in request.GET.items():
        if key == "deleteOption":
            deleteOption = value == "True"
            continue
        if key == "new":
            continue
        if value is not None:
            param += f"{key}={value}&"
    if param:
        param = param[:-1]

    form = MemberForm("Change", request.POST or None, instance=member, prefix="editForm")
    if request.method == "POST" and "editForm-firstname" in request.POST:
        if form.is_valid():
            inst = form.save(commit=False)
            inst.dateUpdated = datetime.datetime.now()
            inst.save()
            messages.add_message(request, messages.INFO, "Edited member")
            return redirect(f"/member/{id}?{param}")

    # manager management
    isAdmin = False
    current = False
    if member.profile == None:
        loginForm = MemberLoginForm("Create new manager", request.POST or None, prefix="loginForm")
        isManager = False
    else:
        loginForm = MemberLoginForm("Change manager login details", request.POST or None, prefix="loginForm", initial={"username": member.profile.username})
        isManager = True
        if member.profile.is_superuser:
            isAdmin = True
        if member.profile == request.user:
            current = True
    
    if loginForm.is_valid():
        username = loginForm.cleaned_data["username"]
        password = loginForm.cleaned_data["password"]
        conf = loginForm.cleaned_data["confPassword"]
        if username == "" or password == "" or conf == "":
            messages.add_message(request, messages.ERROR, f"username or password field is empty")
            return redirect(f"/member/{id}?{param}")
        if password != conf:
            messages.add_message(request, messages.ERROR, f"Passwords do not match")
            return redirect(f"/member/{id}?{param}")

        if isManager:
            user = member.profile
            user.set_password(password)
            user.username = username
            user.save()
            messages.add_message(request, messages.INFO, "Changed manager details")
            if current:
                return redirect("/")
            return redirect(f"/member/{id}?{param}")
        
        user = User.objects.create_user(username, None, password)
        permission = Permission.objects.get(codename='manager')
        user.user_permissions.add(permission)
        member.profile = user
        member.save()
        messages.add_message(request, messages.INFO, "Created new manager")
        return redirect(f"/member/{id}?{param}")

    
    context = {"member": member, "form": form, "loginForm": loginForm, "param": param, "deleteOption": deleteOption, "isManager": isManager, "isAdmin": isAdmin, "current": current}
    return render(request, 'dataManager/memberEditSingle.html', context)

def MemberDelete(request, id):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    member = get_object_or_404(Member, id=id)

    # get the query paramters to be redirected to
    param = ""
    for key, value in request.GET.items():
        if value is not None:
            param += f"{key}={value}&"
    if param:
        param = param[:-1]

    if member.surname == "anon":
        messages.add_message(request, messages.ERROR, "anon can't be deleted")
        return redirect(f"/member/{id}?{param}")
    
    if member.profile != None:
        messages.add_message(request, messages.ERROR, "This member is a manager and can't be deleted")
        return redirect(f"/member/{id}?{param}")
    
    if request.method == "POST":
        replacement_member = Member.objects.get(surname="anon")

        for site in Site.objects.filter(creatorFK=member):
            site.creatorFK = replacement_member
            site.save(update_fields=["creatorFK"])
        for site in Site.objects.filter(updaterFK=member):
            site.updaterFK = replacement_member
            site.save(update_fields=["updaterFK"])

        for fungi in Fungi.objects.filter(creatorFK=member):
            fungi.creatorFK = replacement_member
            fungi.save(update_fields=["creatorFK"])
        for fungi in Fungi.objects.filter(updaterFK=member):
            fungi.updaterFK = replacement_member
            fungi.save(update_fields=["updaterFK"])

        for record in Record.objects.filter(recorderFK=member):
            record.recorderFK = replacement_member
            record.save(update_fields=["recorderFK"])
        for record in Record.objects.filter(identifierFK=member):
            record.identifierFK = replacement_member
            record.save(update_fields=["identifierFK"])
        for record in Record.objects.filter(confirmerFK=member):
            record.confirmerFK = replacement_member
            record.save(update_fields=["confirmerFK"])
        for record in Record.objects.filter(collectorFK=member):
            record.collectorFK = replacement_member
            record.save(update_fields=["collectorFK"])
        for record in Record.objects.filter(updaterFK=member):
            record.updaterFK = replacement_member
            record.save(update_fields=["updaterFK"])
        for record in Record.objects.filter(photographerFK=member):
            record.photographerFK = replacement_member
            record.save(update_fields=["photographerFK"])

        member.delete()
        messages.add_message(request, messages.INFO, "Member deleted")
    
    return redirect('/member?' + param)

def ManagerDelete(request, id):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    member = get_object_or_404(Member, id=id)

    # get the query paramters to be redirected to
    param = ""
    for key, value in request.GET.items():
        if value is not None:
            param += f"{key}={value}&"
    if param:
        param = param[:-1]

    if member.profile == None:
        messages.add_message(request, messages.ERROR, "Manager delete failed: This member is not a manager")
        return redirect(f"/member/{id}?{param}")
    
    if member.profile == request.user:
        messages.add_message(request, messages.ERROR, "Manager delete failed: You cannot delete your own manager details")
        return redirect(f"/member/{id}?{param}")

    if member.profile.is_superuser:
        messages.add_message(request, messages.ERROR, "Manager delete failed: This member is an admin")
        return redirect(f"/member/{id}?{param}")
    
    if request.method == "POST":
        user = member.profile
        member.profile = None
        member.save()
        user.delete()
        messages.add_message(request, messages.INFO, "Manager deleted")
    
    return redirect(f"/member/{id}?{param}")

# ---------------
# SUBSTRATE VIEWS
# ---------------

def SubstrView(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
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
            messages.add_message(request, messages.INFO, "Edited substrate")
            return redirect("/substrate?delete=" + deleteText)
        formList.append({"form": form, "id": subtr.id})

    # singular new form
    newForm = SubtrForm("New", request.POST or None, prefix="form0")
    if newForm.is_valid():
        newForm.save()
        messages.add_message(request, messages.INFO, "Added new substrate")
        return redirect("/substrate?delete=" + deleteText)

    context = {"formList": formList, "newForm": newForm, "delete": delete, "deleteText": deleteText}
    return render(request, 'dataManager/substr.html', context)

def SubstrDelete(request, id):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    substr = get_object_or_404(Substrate, id=id)
    
    if request.method == "POST":
        try:
            substr.delete()
            messages.add_message(request, messages.INFO, "Substrate deleted")
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

    if not checkPerms(request.user):
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
            messages.add_message(request, messages.INFO, "Edited association")
            return redirect("/association?delete=" + deleteText)
        formList.append({"form": form, "id": assoc.id})

    # singular new form
    newForm = AssocForm("New", request.POST or None, prefix="form0")
    if newForm.is_valid():
        newForm.save()
        messages.add_message(request, messages.INFO, "Added new association")
        return redirect("/association?delete=" + deleteText)

    context = {"formList": formList, "newForm": newForm, "delete": delete, "deleteText": deleteText}
    return render(request, 'dataManager/assoc.html', context)

def AssocDelete(request, id):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()
    
    assoc = get_object_or_404(Association, id=id)
    
    if request.method == "POST":
        try:
            assoc.delete()
            messages.add_message(request, messages.INFO, "Association deleted")
        except RestrictedError: # if the assoc is being used by a record the delete will be blocked
            messages.add_message(request, messages.ERROR, "Delete failed: Association is used in 1 or more records")
        except:
            messages.add_message(request, messages.ERROR, "Delete failed")
    
    return redirect("/association?delete=true")

# ------------
# Export views
# ------------

def ExportView(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()
    
    if not checkPerms(request.user):
        raise PermissionDenied()

    date = request.GET.get("date")
    site = request.GET.get("site")

    reportForm = ReportExportForm(request.POST or None, initial={"date": date, "site": site}, prefix="rep")
    if request.method == "POST" and (f"{reportForm.prefix}-date" in request.POST) or (f"{reportForm.prefix}-site" in request.POST):
        if reportForm.is_valid():
            param = ""
            date = reportForm.cleaned_data["date"]
            if date != None and date != "":
                param += f"date={date}&"

            site = reportForm.cleaned_data["site"]
            if site != None and site != "":
                isSite = Site.objects.filter(name=site).exists()
                if not isSite:
                    messages.add_message(request, messages.ERROR, f"Site \"{site}\" not found")
                    return redirect("/export?" + param)
                param += f"site={site}&"

            return redirect("/export?" + param)

    forays = []
    records = Record.objects.all()
    if date != None:
        records = records.filter(dateFound=date)
    if site != None:
        records = records.filter(siteFK=Site.objects.get(name=site))
    if date == None and site == None:
        records = records.filter(dateFound__gte=datetime.date.today() - datetime.timedelta(days=365))
        
    records = records.order_by("-dateFound")
    for rec in records:
        date_str = rec.dateFound.strftime("%Y-%m-%d")
        x = {"dateValue": date_str, "date": rec.dateFound, "site": rec.siteFK.name}
        if not x in forays:
            forays.append(x)
        if len(forays) >= 10:
            break

    FRDBIForm = FRDBIExportForm(request.POST or None, prefix="frd")
    if FRDBIForm.is_valid():
        return redirect(f"/export/FRDBI?dateFrom={FRDBIForm.cleaned_data['dateFrom']}&dateTo={FRDBIForm.cleaned_data['dateTo']}")
    
    context = {"forays": forays, "reportForm": reportForm, "FRDBIForm": FRDBIForm, "isAdmin": request.user.is_superuser}
    return render(request, 'export/export.html', context)

def ExportFRDBI(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()
    
    if not checkPerms(request.user):
        raise PermissionDenied()

    dateFrom = request.GET.get("dateFrom")
    dateTo = request.GET.get("dateTo")
    site_name = request.GET.get("site")

    if dateFrom == None or dateTo == None:
        messages.add_message(request, messages.ERROR, "Invalid request")
        return redirect("/export")

    records = Record.objects.filter(dateFound__range=[dateFrom, dateTo])
    if site_name != None:
        try:
            site = Site.objects.get(name=site_name)
        except:
            messages.add_message(request, messages.ERROR, f"Site \"{site_name}\" not found")
            return redirect("/export")

        records = records.filter(siteFK=site)

    numGone = records.filter(exported=True).count()
    numGoing = records.filter(exported=False).count()

    if dateFrom == dateTo:
        date = datetime.datetime.strptime(dateFrom, "%Y-%m-%d").strftime("%d/%m/%Y")
        single = True
    else:
        date = datetime.datetime.strptime(dateFrom, "%Y-%m-%d").strftime("%d/%m/%Y") + " - " + datetime.datetime.strptime(dateTo, "%Y-%m-%d").strftime("%d/%m/%Y")
        single = False

    context = {"date": date, "dateFrom": dateFrom, "dateTo": dateTo, "numGone": numGone, "numGoing": numGoing, "site": site_name, "single": single}

    return render(request, 'export/exportFRDBI.html', context)
    
def ExportExcel(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()
    
    if not checkPerms(request.user):
        raise PermissionDenied()

    dateFrom = request.GET.get("dateFrom")
    dateTo = request.GET.get("dateTo")
    site_name = request.GET.get("site")
    exported = request.GET.get("exported")
    style = request.GET.get("style")

    today = datetime.datetime.now()
    
    if style == "2":
        records = Record.objects.filter(dateFound__range=[dateFrom, dateTo], siteFK=Site.objects.get(name=site_name))

        file = "RecordDate,Site,ReportingName,EnglishName,Collector,Identifier,Confirmer,Association 1,Association 2,Association 3,Substrate,OS Grid Ref,Comments\n"

        for rec in records:
            file += f"{rec.dateFound.strftime('%d/%m/%Y')},\"{rec.siteFK.name}\",\"{rec.fungusFK.currentFungus.fullName}\",\"{rec.fungusFK.currentFungus.englishName}\",\"{rec.collectorFK.fullName}\",\"{rec.identifierFK.fullName}\","
            if rec.confirmerFK != None:
                file += f"\"{rec.confirmerFK.fullName}\","
            else:
                file += ","
            file += f"\"{rec.assoc1}\",\"{rec.assoc2}\",\"{rec.assoc3}\",\"{rec.substrate}\",{rec.siteFK.gridRef},\"{rec.remarks}\"\n"

        date = datetime.datetime.strptime(dateFrom, "%Y-%m-%d").strftime("%d/%m/%Y")
        response = HttpResponse(file, content_type="application/csv")
        response["Content-Disposition"] = f'attachment; filename="Excel site owners export {date}.csv"'
        return response


    if site_name == None or site_name == "None":
        records = Record.objects.filter(dateFound__range=[dateFrom, dateTo])
    else:
        records = Record.objects.filter(dateFound__range=[dateFrom, dateTo], siteFK=Site.objects.get(name=site_name))

    if exported == "y":
        records = records.filter(exported=True)
    elif exported == "n":
        records = records.filter(exported=False)

    file = "Collection Date,Location,Fungus Name,Certainty,Collector,Identifier,Independent Confirmer,Assoc. organism 1,Assoc. organism 2,Assoc. organism 3,Other Substrate,Map reference,County,VC no,Sender's no,Fungus Notes,Other literature,ImageName\n"

    for rec in records:
        file += f"{rec.dateFound.strftime('%d/%m/%Y')},\"{rec.siteFK.name}\",\"{rec.fungusFK.currentFungus.fullName}\",{rec.certainty},\"{rec.collectorFK.fullName}\",\"{rec.identifierFK.fullName}\","
        if rec.confirmerFK != None:
            file += f"\"{rec.confirmerFK.fullName}\","
        else:
            file += ","
        file += f"\"{rec.assoc1}\",\"{rec.assoc2}\",\"{rec.assoc3}\",\"{rec.substrate}\",{rec.siteFK.gridRef},{rec.siteFK.county},{rec.siteFK.VC},{rec.uniqueCode},\"{rec.remarks}\","
        if rec.litRef != None:
            file += f"\"{rec.litRef}\","
        else:
            file += ","
        # put image name in the .csv
        if not rec.image:
            file += "\n"
        else:
            image_name = os.path.basename(rec.image.name)
            extension = os.path.splitext(image_name)[1]
            file += f"\"{rec.uniqueCode}{extension}\"\n"

    # AI GEN for zipping every image
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as export_zip:
        export_zip.writestr("records.csv", file)
        for rec in records:
            if not rec.image:
                continue
            try:
                image_name = os.path.basename(rec.image.name)
                extension = os.path.splitext(image_name)[1]
                with rec.image.open("rb") as image_file:
                    export_zip.writestr(f"images/{rec.uniqueCode}{extension}", image_file.read())
            except (OSError, ValueError) as error:
                logging.warning("Unable to add image for record %s: %s", rec.uniqueCode, error)

    response = HttpResponse(
        archive.getvalue(),
        content_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="Excel export {today.strftime("%d/%m/%Y")}.zip"'},
    )

    for rec in records:
        rec.exported = True
        rec.dateExported = today
        rec.save()

    return response

    # example stuff from AI:
def ExportReport(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()

    date = request.GET.get("date")
    site_name = request.GET.get("site")
    if not date or not site_name:
        messages.add_message(request, messages.ERROR, "Missing date or site for report export.")
        return redirect("/export")

    try:
        site = Site.objects.get(name=site_name)
    except Site.DoesNotExist:
        messages.add_message(request, messages.ERROR, f"Site \"{site_name}\" not found")
        return redirect("/export")

    records = Record.objects.filter(dateFound=date, siteFK=site).order_by("fungusFK__currentFungus__group", "fungusFK__currentFungus__fullName")
    groups = []
    sortedRecords = []
    members = []
    for rec in records:
        gro = rec.fungusFK.currentFungus.group
        if not gro in groups:
            groups.append(gro)
            sortedRecords.append({"group": gro, "records": [rec], "total": 1})
        else:
            for s in sortedRecords:
                if s["group"] == gro:
                    s["records"].append(rec)
                    s["total"] += 1
                    break

        mem = f"{rec.collectorFK.initials}= {rec.collectorFK.firstname} {rec.collectorFK.surname}"
        if not mem in members:
            members.append(mem)

        mem = f"{rec.identifierFK.initials}= {rec.identifierFK.firstname} {rec.identifierFK.surname}"
        if not mem in members:
            members.append(mem)

        if rec.confirmerFK != None:
            mem = f"{rec.confirmerFK.initials}= {rec.confirmerFK.firstname} {rec.confirmerFK.surname}"
            if not mem in members:
                members.append(mem)
        

    old = sortedRecords
    sortedRecords = []
    for o in old:
        for i in range(len(sortedRecords)):
            if sortedRecords[i]["total"] < o["total"]:
                sortedRecords.insert(i, o)
                break
        else:
            sortedRecords.append(o)

    text = ""
    for mem in members:
        text = text + mem + ",&nbsp;&nbsp;&nbsp;"
    text = text[:-19]

    date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
    context = {
        "sortedRecords": sortedRecords,
        "date": date,
        "site": site.name, 
        "members": text,
        "total": records.count()
    }

    html = render_to_string("export/report_template.html", context, request=request)

    rtf = pypandoc.convert_text(html, "rtf", format="html")

    rtf = rtf.replace('\\fs24', '\\fs16')
    rtf = rtf.replace('\\fs30', '\\fs20')
    rtf = rtf.replace('\\fs32', '\\fs28')

    rtf = rtf.replace('cellx960', 'cellx2800')
    rtf = rtf.replace('cellx1920', 'cellx5000')
    rtf = rtf.replace('cellx2880', 'cellx7000')
    rtf = rtf.replace('cellx3840', 'cellx9000')
    rtf = rtf.replace('cellx4800', 'cellx10600')
    rtf = rtf.replace('cellx5760', 'cellx11200')
    rtf = rtf.replace('cellx6720', 'cellx11800')
    rtf = rtf.replace('cellx7680', 'cellx12600')
    rtf = rtf.replace('cellx8640', 'cellx16000')

    rtf = rtf.replace('sa180', 'sa0')
    rtf = rtf.replace(r'{\pard\intbl \ql \f0 \fs16 \sa0 \li0 \fi0 \outlinelevel2 \b \fs20 \par}', '')

    rtf = r'{\rtf1\ansi\deff0{\fonttbl{\f0\froman Arial;}}\paperw16836\paperh11904\margl567\margr792\margt284\margb188\gutter0' + rtf + '}'

    rtf = rtf.replace(r'\pard \ql \f0 \fs16 \sa0 \li0 \fi0 \outlinelevel1 \b \fs28 BFG Fungi Walk at', r'\pard \qc \f0 \fs16 \sa400 \li0 \fi0 \outlinelevel1 \b \fs28 BFG Fungi Walk at')

    rtf = rtf.replace('&nbsp;', ' ')

    rtf = rtf.replace(r'\pard \ql \f0 \fs16 \sa0 \li0 \fi0 \outlinelevel1 \b \fs28 Species total for visit:', r'\pard \qc \f0 \fs16 \sa0 \li0 \fi0 \outlinelevel1 \b \fs28 Species total for visit:')

    response = HttpResponse(rtf, content_type="application/rtf")
    response["Content-Disposition"] = f'attachment; filename="BFG Walk Report {date}.rtf"'
    return response


def ExportBackup(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user):
        raise PermissionDenied()

    models = [Association, Substrate, Site, Record, RecordArchive, Fungi, FungiCurrent, FungiArchive, Member, User]

    database_objects = itertools.chain.from_iterable(
        model.objects.all() for model in models
    )
    database_json = serializers.serialize("json", database_objects, indent=2)
    today = datetime.date.today().strftime("%Y-%m-%d")

    return HttpResponse(
        database_json,
        content_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="BFG database {today}.json"'},
    )


def ImportBackup(request):
    if not request.user.is_authenticated:
        raise PermissionDenied()

    if not checkPerms(request.user, True):
        raise PermissionDenied()

    if request.method != "POST":
        return redirect("Export")

    uploaded_file = request.FILES.get("database_file")
    if uploaded_file is None:
        messages.add_message(request, messages.ERROR, "Please select a database backup JSON file")
        return redirect("Export")

    #data = json.load(uploaded_file)
    #databaseBackupOverwrite(data)
    databaseBackupOverwriteBuffered(uploaded_file)
    
    messages.add_message(request, messages.INFO, "Backup inserted")
    return redirect("Export")