from django.contrib import admin

from .models import TestingRecording, Scenario, ScenariosSet


class TestingRecordingAdmin(admin.ModelAdmin):
    list_display = ('date', 'file')


class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('name', 'num_targets')
    actions = []


class ScenariosSetAdmin(admin.ModelAdmin):
    list_display = ('n_targets', 'n_cases', 'metafile')


class CompareAdmin(admin.ModelAdmin):
    list_display = ('obj1', 'obj2', 'n_targets')


admin.site.register(TestingRecording, TestingRecordingAdmin)
admin.site.register(Scenario, ScenarioAdmin)
admin.site.register(ScenariosSet, ScenariosSetAdmin)
