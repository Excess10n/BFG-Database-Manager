from django.urls import path, include
from .views import IndexView, RecordBrowseView, RecordEditView, RecordDelete, FungusView, SiteView, SubstrView, SubstrDelete, AssocView, AssocDelete, ExportView
from.jsonViews import fungiSuggestions

urlpatterns = [
    path('', IndexView, name='Index'),
    
    path('record/edit/', RecordEditView, name='RecordEdit'),
    path('record/browse/', RecordBrowseView, name='RecordBrowse'),
    path('record/edit/<int:id>/delete/', RecordDelete, name='RecordDelete'),

    path('fungus/', FungusView, name='Fungus'),

    path('site/', SiteView, name='Site'),

    path('substrate/', SubstrView, name='Substr'),
    path('substrate/<int:id>/delete/', SubstrDelete, name='SubstrDelete'),

    path('association/', AssocView, name='Assoc'),
    path('association/<int:id>/delete/', AssocDelete, name='AssocDelete'),

    path('export/', ExportView, name='Export'),

    # json paths
    path('json/ajax/fungi/', fungiSuggestions, name='FungiSuggestions')
]