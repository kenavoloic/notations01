from django.contrib import admin
from django.contrib import admin
from configurations.models import  GroupePage, Page, AssociationUtilisateurGroupe, PageConfig
# Register your models here.
admin.site.register(GroupePage)
admin.site.register(Page)
admin.site.register(PageConfig)
admin.site.register(AssociationUtilisateurGroupe)
