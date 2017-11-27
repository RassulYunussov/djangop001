from django.contrib import admin
from .models import *

class PostVilavi(admin.ModelAdmin):
    list_display = ['ul', 'un']
    ordering = ['ul']
    action = []
    list_filter = []

class PostProfile(admin.ModelAdmin):
    list_display = ['user', 'phone' ]
    ordering = ['user']
    action = []
    list_filter = []

class PostCountry(admin.ModelAdmin):
    list_display = ['name']
    ordering = ['name']
    action = []
    list_filter = []

class PostCity(admin.ModelAdmin):
    list_display = ['name', 'country']
    ordering = ['country']
    action = []
    list_filter = []

class PostUsefulLink(admin.ModelAdmin):
    list_display = ['name', 'url']
    ordering = ['name']
    action = []
    list_filter = []

class PostTree(admin.ModelAdmin):
    list_display = ['ul', 'profile']
    ordering = ['profile']
    action = []
    list_filter = []

class PostAdminSettings(admin.ModelAdmin):
    list_display = ['registrationTime', 'inactiveTime', 'crawlEmail', 'crawlPassword', 'problems', 'date']
    ordering = ['date']
    action = []
    list_filter = []

admin.site.register(Profile, PostProfile)
admin.site.register(VilaviFetch, PostVilavi)
admin.site.register(Country, PostCountry)
admin.site.register(City, PostCity)
admin.site.register(UsefulLink, PostUsefulLink)
admin.site.register(Tree, PostTree)
admin.site.register(SuperAdminSettings, PostAdminSettings)
# Register your models here.
