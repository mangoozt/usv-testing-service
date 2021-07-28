from django.contrib import admin

from .models import TestingRecording, Scenario, ScenariosSet


@admin.action(description='Сохранение выбранного сценария в папку')
def save_folder(modeladmin, request, queryset):
    for obj in queryset:
        obj.generate_folder()


class TestingRecordingAdmin(admin.ModelAdmin):
    list_display = ('date', 'file')


class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('name', 'num_targets', 'dist1', 'dist2')
    ordering = ['dist1']
    actions = [save_folder]


class ScenariosSetAdmin(admin.ModelAdmin):
    list_display = ('n_targets', 'n_cases', 'metafile')


admin.site.register(TestingRecording, TestingRecordingAdmin)
admin.site.register(Scenario, ScenarioAdmin)
admin.site.register(ScenariosSet, ScenariosSetAdmin)
