from django import forms
from .models import Association, Substrate, Site, Fungi, Member, Record
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from crispy_forms.bootstrap import Div
from crispy_forms import bootstrap

class ListTextWidget(forms.TextInput):

    def __init__(self, dataset, name, *args, **kwargs):
        super().__init__(*args)
        self._name = name
        self._list = dataset
        self.attrs.update({'list':'list__%s' % self._name})
        if 'width' in kwargs:
            width = kwargs['width']
            self.attrs.update({'style': 'width:{}px;'.format(width)})
        if 'identifier' in kwargs:
            self.attrs.update({'id':kwargs['identifier']})

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super().render(name, value, attrs=attrs)
        data_list = '<datalist id="list__%s">' % self._name
        current = []
        for item in self._list:
            if not item in current:  
                data_list += '<option value="%s">' % item
                current.append(item)
        data_list += '</datalist>'
        return (text_html + data_list)

#EXTRA
class SearchForm(forms.Form):
    substrate = forms.CharField(label="Substrate", max_length=64, required=False, widget=ListTextWidget(dataset=Substrate.objects.values_list("name", flat=True), name="substrList"))
    substrW = forms.FloatField(
        label="Substrate weight",
        widget=forms.NumberInput(attrs={'type': 'range', 'min': '0.5', 'max': '4.0', 'step': '0.1', 'class': 'form-range'}),
        initial=1.0,
        required=False
    )
    association1 = forms.CharField(label="Association 1", max_length=64, required=False, widget=ListTextWidget(dataset=Association.objects.values_list("name", flat=True), name="assocList"))
    association2 = forms.CharField(label="Association 2", max_length=64, required=False, widget=ListTextWidget(dataset=Association.objects.values_list("name", flat=True), name="assocList"))
    association3 = forms.CharField(label="Association 3", max_length=64, required=False, widget=ListTextWidget(dataset=Association.objects.values_list("name", flat=True), name="assocList"))
    assocW = forms.FloatField(
        label="Association weight",
        widget=forms.NumberInput(attrs={'type': 'range', 'min': '0.5', 'max': '4.0', 'step': '0.1', 'class': 'form-range'}),
        initial=1.0,
        required=False
    )
    date = forms.DateField(label="Date", required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    dateW = forms.FloatField(
        label="Date weight",
        widget=forms.NumberInput(attrs={'type': 'range', 'min': '0.5', 'max': '4.0', 'step': '0.1', 'class': 'form-range'}),
        initial=1.0,
        required=False
    )
    site = forms.CharField(label="Site", max_length=64, required=False, widget=ListTextWidget(dataset=Site.objects.values_list("name", flat=True), name="siteList"))
    image = forms.ImageField(label="Image", required=False)
    locW = forms.FloatField(
        label="Location weight",
        widget=forms.NumberInput(attrs={'type': 'range', 'min': '0.5', 'max': '4.0', 'step': '0.1', 'class': 'form-range'}),
        initial=1.0,
        required=False
    )
    maxNum = forms.IntegerField(label="Max number of results", initial=20)

class SearchForm2(forms.Form):
    site = forms.CharField(label="Site", max_length=64, required=True, widget=ListTextWidget(dataset=Site.objects.values_list("name", flat=True), name="siteList"))
    date = forms.DateField(label="Date", required=True, widget=forms.TextInput(attrs={'type': 'date'}))

class RecordForm(forms.ModelForm):
    def __init__(self, buttonText, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        #self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Div(
                Div(
                    Div('fungus'),
                    Div('substrFK'),
                css_class="col"),
                Div(
                    Div('assoc1FK'),
                    Div('assoc2FK'),
                    Div('assoc3FK'),
                css_class="col"),
                Div(
                    Div('collectorFK'),
                    Div('identifierFK'),
                    Div('confirmerFK'),
                css_class="col-1"),
                Div('remarks', css_class="col"),
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
            )
        )

        self.fields['assoc1FK'].required = False
        self.fields['assoc2FK'].required = False
        self.fields['assoc3FK'].required = False
        self.fields['confirmerFK'].required = False
        self.fields['remarks'].required = False
    
    fungus = forms.CharField(label="Fungus", max_length=64, required=False, widget=forms.TextInput(attrs={"list": "fungusList", "autocomplete": "off"}))

    class Meta:
        model = Record
        fields = [
            #"fungusFK",
            "substrFK",
            "assoc1FK",
            "assoc2FK",
            "assoc3FK",
            "collectorFK",
            "identifierFK",
            "confirmerFK",
            "remarks",
            "litRef",
            "DNATest",
            "image"
        ]
        labels = {
            #"fungusFK": "Fungus",
            "substrFK": "Substrate",
            "assoc1FK": "Association 1",
            "assoc2FK": "Association 2",
            "assoc3FK": "Association 3",
            "collectorFK": "Collector",
            "identifierFK": "Indentifier",
            "confirmerFK": "Confirmer",
            "remarks": "Remarks",
            "litRef": "Lit Ref.",
            "DNATest": "DNA Test?",
            "image": "Image"
        }
        widgets = {
            #"fungusFK": forms.TextInput(attrs={"list": "fungusList", "autocomplete": "off"}),
            "remarks": forms.Textarea(attrs={"rows": 5}),
        }


class RecordInitialForm(forms.Form):
    date = forms.DateField(label="Date of record", widget=forms.TextInput(attrs={'type': 'date'}))
    site = forms.CharField(label="Recorded at", max_length=64, widget=ListTextWidget(dataset=Site.objects.values_list("name", flat=True), name="siteList"))
    rec = forms.CharField(label="Recorded by", max_length=5, widget=ListTextWidget(dataset=Member.objects.values_list("initials", flat=True), name="memberList"))


class RecordFilterForm(forms.Form):
    def __init__(self, buttonText, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div('fungus', css_class="col-3"),
                Div('site', css_class="col-2"),
                Div('vc', css_class="col-1"),
                Div('recorder', css_class="col-1"),
                Div('collector', css_class="col-1"),
                Div('identifier', css_class="col-1"),
                Div('confirmer', css_class="col-1"),
                Div('association', css_class="col-2"),
                Div('dateFrom', css_class="col-2"),
                Div('dateTo', css_class="col-2"),
                Div(bootstrap.FormActions(
                    Submit('submit', buttonText, css_class='btn btn-primary')),
                    css_class='col'
                    ),
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
    site = forms.CharField(label="Site", max_length=64, required=False, widget=ListTextWidget(dataset=Site.objects.values_list("name", flat=True), name="siteList"))
    vc = forms.IntegerField(label="VC", max_value=100, required=False)
    recorder = forms.CharField(label="Recorder", max_length=5, required=False, widget=ListTextWidget(dataset=Member.objects.values_list("initials", flat=True), name="recorderList"))
    collector = forms.CharField(label="Collector", max_length=5, required=False, widget=ListTextWidget(dataset=Member.objects.values_list("initials", flat=True), name="collectorList"))
    identifier = forms.CharField(label="Identifier", max_length=5, required=False, widget=ListTextWidget(dataset=Member.objects.values_list("initials", flat=True), name="identifierList"))
    confirmer = forms.CharField(label="Confirmer", max_length=5, required=False, widget=ListTextWidget(dataset=Member.objects.values_list("initials", flat=True), name="confirmerList"))
    association = forms.CharField(label="Association", max_length=64, required=False, widget=ListTextWidget(dataset=Association.objects.values_list("name", flat=True), name="associationList"))
    dateFrom = forms.DateField(label="From", required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    dateTo = forms.DateField(label="To", required=False, widget=forms.TextInput(attrs={'type': 'date'}))


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = [
            "name",
            "reportingName",
            "gridRef",
            "county",
            "VC",
            "country",
            "type",
            "remarks"
        ]
        # exclude = [
        #     "dateUpdated",
        #     "creatorFK",
        #     "updaterFK"
        # ]
        widgets = {
            "county": ListTextWidget(dataset=Site.objects.values_list("county", flat=True), name="countyList"),
            "country": ListTextWidget(dataset=Site.objects.values_list("country", flat=True), name="countryList"),
            "type": ListTextWidget(dataset=Site.objects.values_list("type", flat=True), name="typeList")
        }


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