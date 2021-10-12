from django.contrib import admin

from .models import TestingRecording, Scenario, ScenariosSet


@admin.action(description='Recalculate statistics from file')
def recalculate_statistics(modeladmin, request, queryset):
    for o in queryset:
        if o.file.storage.exists(o.file.name):
            o.processed=False
            o.save()


class TestingRecordingAdmin(admin.ModelAdmin):
    list_display = ('date', 'title', 'commit_sha1', 'file')
    actions = [recalculate_statistics]


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
