from django.contrib import admin

from .models import TestingRecording, Scenario, ScenariosSet


@admin.action(description='Сохранение выбранного сценария в папку')
def save_folder(modeladmin, request, queryset):
    for obj in queryset:
        obj.generate_folder()


class TestingRecordingAdmin(admin.ModelAdmin):
    list_display = ('date', 'file')


class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('name', 'num_targets')
    actions = [save_folder]


class ScenariosSetAdmin(admin.ModelAdmin):
    list_display = ('n_targets', 'n_cases', 'metafile')


class CompareAdmin(admin.ModelAdmin):
    list_display = ('obj1', 'obj2', 'n_targets')


admin.site.register(TestingRecording, TestingRecordingAdmin)
admin.site.register(Scenario, ScenarioAdmin)
admin.site.register(ScenariosSet, ScenariosSetAdmin)
