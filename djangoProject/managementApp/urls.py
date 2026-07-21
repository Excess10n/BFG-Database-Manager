from django.urls import path, include
from .views import IndexView, RecordBrowseView, RecordEditView, RecordEditSingle, RecordDelete, RecordDelete2, FungusView, SiteView, SiteEditSingle, SiteDelete, SubstrView, SubstrDelete, AssocView, AssocDelete, MemberView, MemberEditSingle, MemberDelete, ExportView
from .jsonViews import fungiSuggestions

urlpatterns = [
    path('', IndexView, name='Index'),
    
    path('record/edit/', RecordEditView, name='RecordEdit'),
    path('record/browse/', RecordBrowseView, name='RecordBrowse'),
    path('record/browse/<int:id>/', RecordEditSingle, name='RecordEditSingle'),
    path('record/browse/<int:id>/delete/', RecordDelete2, name='RecordDelete2'),
    path('record/edit/<int:id>/delete/', RecordDelete, name='RecordDelete'),

    path('fungus/', FungusView, name='Fungus'),

    path('site/', SiteView, name='Site'),
    path('site/<int:id>/', SiteEditSingle, name='SiteEditSingle'),
    path('site/<int:id>/delete/', SiteDelete, name='SiteDelete'),

    path('substrate/', SubstrView, name='Substr'),
    path('substrate/<int:id>/delete/', SubstrDelete, name='SubstrDelete'),

    path('association/', AssocView, name='Assoc'),
    path('association/<int:id>/delete/', AssocDelete, name='AssocDelete'),

    path('member/', MemberView, name='Member'),
    path('member/<int:id>/', MemberEditSingle, name='MemberEditSingle'),
    path('member/<int:id>/delete/', MemberDelete, name='SiteDelete'),

    path('export/', ExportView, name='Export'),

    # json paths
    path('json/ajax/fungi/', fungiSuggestions, name='FungiSuggestions')
]