from functools import lru_cache

from django import forms
from .models import Association, Substrate, Site, Fungi, Member, Record
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML
from crispy_forms.bootstrap import Div
from crispy_forms import bootstrap

# AI GEN:
# the below functions where made so you the migrations don't get stuck

@lru_cache(maxsize=1)
def get_member_names():
    return tuple(Member.objects.values_list("fullName", flat=True))


@lru_cache(maxsize=1)
def get_site_names():
    return tuple(Site.objects.values_list("name", flat=True))


@lru_cache(maxsize=1)
def get_substrate_names():
    return tuple(Substrate.objects.values_list("name", flat=True))


@lru_cache(maxsize=1)
def get_association_names():
    return tuple(Association.objects.values_list("name", flat=True)) + tuple(Association.objects.values_list("latin", flat=True))


class ListTextWidget(forms.TextInput):

    def __init__(self, dataset, name, *args, **kwargs):
        super().__init__(*args)
        self._name = name
        self._dataset = dataset
        self.attrs.update({'list':'list__%s' % self._name})
        if 'width' in kwargs:
            width = kwargs['width']
            self.attrs.update({'style': 'width:{}px;'.format(width)})
        if 'identifier' in kwargs:
            self.attrs.update({'id':kwargs['identifier']})

    def _get_list(self):
        if callable(self._dataset):
            return list(self._dataset())
        return self._dataset

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super().render(name, value, attrs=attrs)
        data_list = '<datalist id="list__%s">' % self._name
        current = []
        for item in self._get_list():
            if item not in current:
                data_list += '<option value="%s">' % item
                current.append(item)
        data_list += '</datalist>'
        return (text_html + data_list)

class RecordForm(forms.ModelForm):
    def __init__(self, buttonText, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        #self.helper.form_show_labels = False

        # AI GEN english name gets displayed under the selected fungus
        english_name = ""
        fungus_current = getattr(getattr(self.instance, "fungusFK", None), "currentFungus", None)
        if fungus_current is not None:
            english_name = getattr(fungus_current, "englishName", "") or ""

        form_fields = [Div('fungus')]
        if english_name:
            form_fields.append(HTML(f'<div class="text-muted small">English name:</div>'))
            form_fields.append(HTML(f'<div class="text-muted small">{english_name}</div>'))
        form_fields.append(Div('substrate'))

        # first site/bucks/database record gets displayed
        first = getattr(self.instance, "firstRecord", None)
        if first is not None:
            if first == "S":
                form_fields.append(HTML(f'<div class="text-danger"><b>First Site Record!</b></div>'))
            elif first == "B":
                form_fields.append(HTML(f'<div class="text-danger"><b>First Bucks Record!</b></div>'))
            elif first == "D":
                form_fields.append(HTML(f'<div class="text-danger"><b>First Database Record!</b></div>'))

        self.helper.layout = Layout(
            Div(
                Div(*form_fields, css_class="col"),
                Div(
                    Div('assoc1'),
                    Div('assoc2'),
                    Div('assoc3'),
                css_class="col"),
                Div(
                    Div('collectorFK'),
                    Div('identifierFK'),
                    Div('confirmerFK'),
                css_class="col"),
                Div(
                    Div('remarks'),
                    Div('photographerFK'),
                css_class="col"),
                Div(
                    Div('litRef'),
                    Div('DNATest'),
                    Div('image'),
                css_class="col"),
                Div(
                    bootstrap.FormActions(Submit('submit', buttonText, css_class='btn btn-primary')),
                    css_class='col-1 mt-3'
                    ),
                css_class='row',
            ),
        )

        self.fields['remarks'].required = False
        self.fields['DNATest'].required = False
        self.fields['image'].widget = forms.ClearableFileInput(attrs={
            'class': 'form-control custom-file-input',
            'accept': 'image/*'
        })
    
    fungus = forms.CharField(label="Fungus", max_length=64, required=True, widget=forms.TextInput(attrs={"list": "fungusList", "autocomplete": "off"}))
    collectorFK = forms.CharField(label="Collector", max_length=128, required=True, widget=ListTextWidget(dataset=get_member_names, name="collectorList"))
    identifierFK = forms.CharField(label="Identifier", max_length=128, required=True, widget=ListTextWidget(dataset=get_member_names, name="identifierList"))
    confirmerFK = forms.CharField(label="Confirmer", max_length=128, required=False, widget=ListTextWidget(dataset=get_member_names, name="confirmerList"))
    photographerFK = forms.CharField(label="Photographer", max_length=128, required=False, widget=ListTextWidget(dataset=get_member_names, name="photographerList"))

    substrate = forms.CharField(label="Substrate", max_length=128, required=True, widget=ListTextWidget(dataset=get_substrate_names, name="substrateList"))
    assoc1 = forms.CharField(label="Association 1", max_length=128, required=False, widget=ListTextWidget(dataset=get_association_names, name="assoc1List"))
    assoc2 = forms.CharField(label="Association 2", max_length=128, required=False, widget=ListTextWidget(dataset=get_association_names, name="assoc2List"))
    assoc3 = forms.CharField(label="Association 3", max_length=128, required=False, widget=ListTextWidget(dataset=get_association_names, name="assoc3List"))

    class Meta:
        model = Record
        fields = [
            #"fungusFK",
            #"substrFK",
            #"assoc1FK",
            #"assoc2FK",
            #"assoc3FK",
            #"collectorFK",
            #"identifierFK",
            #"confirmerFK",
            "remarks",
            "litRef",
            "DNATest",
            "image"
        ]
        labels = {
            #"fungusFK": "Fungus",
            #"substrFK": "Substrate",
            #"assoc1FK": "Association 1",
            #"assoc2FK": "Association 2",
            #"assoc3FK": "Association 3",
            #"collectorFK": "Collector",
            #"identifierFK": "Indentifier",
            #"confirmerFK": "Confirmer",
            "remarks": "Remarks",
            "litRef": "Lit Ref.",
            "DNATest": "DNA Test?",
            "image": "Image"
        }
        widgets = {
            #"fungusFK": forms.TextInput(attrs={"list": "fungusList", "autocomplete": "off"}),
            "remarks": forms.Textarea(attrs={"rows": 5}),
        }

class RecordFormBrowse(forms.ModelForm):
    def __init__(self, buttonText, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        #self.helper.form_show_labels = False

        # AI GEN taken from above
        english_name = ""
        fungus_current = getattr(getattr(self.instance, "fungusFK", None), "currentFungus", None)
        if fungus_current is not None:
            english_name = getattr(fungus_current, "englishName", "") or ""

        form_fields = [Div('fungus')]
        if english_name:
            form_fields.append(HTML(f'<div class="text-muted small">English name:</div>'))
            form_fields.append(HTML(f'<div class="text-muted small">{english_name}</div>'))
        form_fields.append(Div('site'))
        form_fields.append(Div('dateFound'))

        self.helper.layout = Layout(
            Div(
                Div(*form_fields, css_class="col"),
                Div(
                    Div('substrate'),
                    Div('assoc1'),
                    Div('assoc2'),
                    Div('assoc3'),
                css_class="col"),
                Div(
                    Div('recorderFK'),
                    Div('collectorFK'),
                    Div('identifierFK'),
                    Div('confirmerFK'),
                css_class="col"),
                Div(
                    Div('remarks'),
                    Div('photographerFK'),
                css_class="col"),
                Div(
                    Div('litRef'),
                    Div('DNATest'),
                    Div('image'),
                css_class="col"),
                Div(
                    bootstrap.FormActions(Submit('submit', buttonText, css_class='btn btn-primary')),
                    css_class='col-1 mt-3'
                    ),
                css_class='row',
            ),
            Div(
                Div(
                    Div('DNAseq'),
                    css_class="col"
                ),
                css_class="row"
            )
        )

        self.fields['remarks'].required = False
        self.fields['DNATest'].required = False
        self.fields['DNAseq'].required = False
        self.fields['image'].widget = forms.ClearableFileInput(attrs={
            'class': 'form-control custom-file-input',
            'accept': 'image/*'
        })
    
    fungus = forms.CharField(label="Fungus", max_length=64, required=True, widget=forms.TextInput(attrs={"list": "fungusList", "autocomplete": "off"}))
    site = forms.CharField(label="Site", max_length=128, required=True, widget=ListTextWidget(dataset=get_site_names, name="siteList"))
    recorderFK = forms.CharField(label="Recorder", max_length=128, required=True, widget=ListTextWidget(dataset=get_member_names, name="recorderList"))
    collectorFK = forms.CharField(label="Collector", max_length=128, required=True, widget=ListTextWidget(dataset=get_member_names, name="collectorList"))
    identifierFK = forms.CharField(label="Identifier", max_length=128, required=True, widget=ListTextWidget(dataset=get_member_names, name="identifierList"))
    confirmerFK = forms.CharField(label="Confirmer", max_length=128, required=False, widget=ListTextWidget(dataset=get_member_names, name="confirmerList"))
    photographerFK = forms.CharField(label="Photographer", max_length=128, required=False, widget=ListTextWidget(dataset=get_member_names, name="photographerList"))

    substrate = forms.CharField(label="Substrate", max_length=128, required=True, widget=ListTextWidget(dataset=get_substrate_names, name="substrateList"))
    assoc1 = forms.CharField(label="Association 1", max_length=128, required=False, widget=ListTextWidget(dataset=get_association_names, name="assoc1List"))
    assoc2 = forms.CharField(label="Association 2", max_length=128, required=False, widget=ListTextWidget(dataset=get_association_names, name="assoc2List"))
    assoc3 = forms.CharField(label="Association 3", max_length=128, required=False, widget=ListTextWidget(dataset=get_association_names, name="assoc3List"))

    class Meta:
        model = Record
        fields = [
            "remarks",
            "litRef",
            "DNATest",
            "DNAseq",
            "image",
            "dateFound"
        ]
        labels = {
            "remarks": "Remarks",
            "litRef": "Lit Ref.",
            "DNATest": "DNA Test?",
            "image": "Image",
            "dateFound": "Date",
            "DNAseq": "DNA Sequence"
        }
        widgets = {
            "remarks": forms.Textarea(attrs={"rows": 5}),
            "DNAseq": forms.Textarea(attrs={"rows": 3}),
            "dateFound": forms.TextInput(attrs={'type': 'date'})
        }

class RecordInitialForm(forms.Form):
    date = forms.DateField(label="Date of record", widget=forms.TextInput(attrs={'type': 'date'}))
    site = forms.CharField(label="Recorded at", max_length=64, widget=ListTextWidget(dataset=get_site_names, name="siteList"))
    rec = forms.CharField(label="Recorded by", max_length=128, widget=ListTextWidget(dataset=get_member_names, name="memberList"))


class RecordFilterForm(forms.Form):
    def __init__(self, buttonText, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div('fungus', css_class="col-3"),
                Div('recorder', css_class="col-2"),
                Div('collector', css_class="col-2"),
                Div('identifier', css_class="col-2"),
                Div('confirmer', css_class="col-2"),
                Div('site', css_class="col-3"),
                Div('substrate', css_class='col-2'),
                Div('association', css_class="col-2"),
                Div('dateFrom', css_class="col-2"),
                Div('dateTo', css_class="col-2"),
                Div(bootstrap.FormActions(
                    Submit('submit', buttonText, css_class='btn btn-primary')),
                    css_class='col'
                    ),
                Div('vc', css_class="col-1"),
                Div(css_class="col-7"),
                Div('month', css_class="col-1"),
                Div('dateSingle', css_class="col-2"),
                css_class='row',
            )
        )
    
    # def fungiDataset():
    #     fungi = []
    #     records = Record.objects.all()
    #     for record in records:
    #         fungi.append(record.fungusFK.fullName)
    #     return fungi

    fungus = forms.CharField(label="Fungus", max_length=64, required=False, widget=forms.TextInput(attrs={"list": "fungusList", "autocomplete": "off"}))
    site = forms.CharField(label="Site", max_length=64, required=False, widget=ListTextWidget(dataset=get_site_names, name="siteList"))
    vc = forms.IntegerField(label="VC", max_value=100, required=False)
    recorder = forms.CharField(label="Recorder", max_length=128, required=False, widget=ListTextWidget(dataset=get_member_names, name="recorderList"))
    collector = forms.CharField(label="Collector", max_length=128, required=False, widget=ListTextWidget(dataset=get_member_names, name="collectorList"))
    identifier = forms.CharField(label="Identifier", max_length=128, required=False, widget=ListTextWidget(dataset=get_member_names, name="identifierList"))
    confirmer = forms.CharField(label="Confirmer", max_length=128, required=False, widget=ListTextWidget(dataset=get_member_names, name="confirmerList"))
    association = forms.CharField(label="Association", max_length=64, required=False, widget=ListTextWidget(dataset=get_association_names, name="associationList"))
    substrate = forms.CharField(label="Substrate", max_length=64, required=False, widget=ListTextWidget(dataset=get_substrate_names, name="substrateList"))
    dateFrom = forms.DateField(label="From", required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    dateTo = forms.DateField(label="To", required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    dateSingle = forms.DateField(label="Specific Date", required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    month = forms.IntegerField(label="Month", max_value=12, required=False)


class RecordOrderForm(forms.Form):
    CHOICES = [
        ('1', 'Time'),
        ('2', 'Name'),
    ]
    order = forms.ChoiceField(
        label= "",
        required=False,
        widget=forms.RadioSelect,
        choices=CHOICES,
    )

class SiteForm(forms.ModelForm):
    def __init__(self, buttonText, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div('name', css_class="col-3"),
                Div('gridRef', css_class="col-3"),
                Div('county', css_class="col-3"),
                Div('VC', css_class="col-1"),
                Div('type', css_class="col-3"),
                Div('remarks', css_class='col-4'),
                Div(bootstrap.FormActions(
                    Submit('submit', buttonText, css_class='btn btn-primary')),
                    css_class='col'
                    ),
                css_class='row',
            )
        )

        self.fields['remarks'].required = False
        self.fields['type'].required = False
        self.fields['VC'].required = False

    class Meta:
        model = Site
        fields = [
            "name",
            "gridRef",
            "county",
            "VC",
            "type",
            "remarks"
        ]
        labels = {
            "name": "Name",
            "gridRef": "Grid Reference",
            "county": "County",
            "VC": "VC",
            "type": "Site Type",
            "remarks": "Remarks"
        }
        # exclude = [
        #     "dateUpdated",
        #     "creatorFK",
        #     "updaterFK"
        # ]
        widgets = {
            "county": ListTextWidget(dataset=lambda: Site.objects.values_list("county", flat=True), name="countyList"),
            "type": ListTextWidget(dataset=lambda: Site.objects.values_list("type", flat=True), name="typeList"),
            "remarks": forms.Textarea(attrs={"rows": 5}),
        }

class SiteSearchForm(forms.Form):
    site = forms.CharField(label="Site Search", max_length=64, required=False, widget=ListTextWidget(dataset=get_site_names, name="siteList"))

class MemberForm(forms.ModelForm):
    def __init__(self, buttonText, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div('firstname', css_class="col-2"),
                Div('surname', css_class="col-2"),
                Div('initials', css_class="col-1"),
                Div(bootstrap.FormActions(
                    Submit('submit', buttonText, css_class='btn btn-primary')),
                    css_class='col'
                    ),
                css_class='row',
            )
        )

    class Meta:
        model = Member
        fields = [
            "firstname",
            "surname",
            "initials"
        ]
        labels = {
            "firstname": "First Name",
            "surname": "Surname",
            "initials": "Initials"
        }

class MemberSearchForm(forms.Form):
    member = forms.CharField(label="Member Search", max_length=64, required=False, widget=ListTextWidget(dataset=get_member_names, name="memberList"))

class SubtrForm(forms.ModelForm):
    def __init__(self, buttonText, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Div(
                Div('name', css_class="col"),
                Div(bootstrap.FormActions(
                    Submit('submit', buttonText, css_class='btn btn-primary')),
                    css_class='col-2'
                    ),
                css_class='row',
            )
        )

    class Meta:
        model = Substrate
        fields = [
            "name"
        ]


class AssocForm(forms.ModelForm):
    def __init__(self, buttonText, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Div(
                Div('name', css_class="col"),
                Div('latin', css_class="col"),
                Div(bootstrap.FormActions(
                    Submit('submit', buttonText, css_class='btn btn-primary')),
                    css_class='col-2'
                    ),
                css_class='row',
            )
        )

    class Meta:
        model = Association
        fields = [
            "name",
            "latin"
        ]