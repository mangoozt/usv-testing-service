from django import forms

from .models import TestingRecording


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()


class UploadMetaFileForm(forms.Form):
    n_targets = forms.IntegerField()
    metafile = forms.FileField()


class ComparationForm(forms.Form):
    obj1 = forms.ModelChoiceField(queryset=TestingRecording.objects.all(), required=True)
    obj2 = forms.ModelChoiceField(queryset=TestingRecording.objects.all(), required=True)
