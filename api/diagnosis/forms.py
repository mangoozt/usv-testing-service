from django import forms

from .models import TestingRecording


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=500)
    file = forms.FileField()


class UploadMetaFileForm(forms.Form):
    n_targets = forms.IntegerField()
    metafile = forms.FileField()


class ComparationForm(forms.Form):
    prev = forms.ModelChoiceField(queryset=TestingRecording.objects.order_by('-pk'), required=True)
    obj = forms.ModelChoiceField(queryset=TestingRecording.objects.order_by('-pk'), required=True)
