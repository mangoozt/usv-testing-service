import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from .forms import UploadFileForm, UploadMetaFileForm, ComparationForm
from .models import TestingRecording, ScenariosSet, ComparationObject


def main_view(request):
    """
    Plots graphs from info aus DB
    @param request:
    @return:
    """
    recordings = TestingRecording.objects.filter(processed=True)
    s_rec = []
    for rec in recordings:
        s_rec.append({"date": str(rec.date),
                      "n_targ": rec.n_targets,
                      "title": rec.title,
                      "slug": rec.slug})
    return render(request, 'main.html', context={'data': s_rec})


def details(request, slug):
    obj = get_object_or_404(TestingRecording, slug=slug)
    f = lambda arr: [float(a) for a in arr]
    rec = {"date": str(obj.date),
           "code0": f(obj.code0.split(sep='::')),
           "code1": f(obj.code1.split(sep='::')),
           "code2": f(obj.code2.split(sep='::')),
           "code4": f(obj.code4.split(sep='::')),
           "code5": f(obj.code5.split(sep='::')),
           "dists": f(obj.dists.split(sep='::')),
           "n_targ": obj.n_targets,
           "title": obj.title,
           "n_sc": obj.n_scenarios,
           "img": obj.img_stats.url,
           "img_min": obj.img_minister.url}
    return render(request, 'details.html', context=rec)


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            obj = TestingRecording()
            obj.date = datetime.datetime.now()
            obj.file = form.cleaned_data['file']
            obj.title = form.cleaned_data['title']
            obj.save()
            return HttpResponseRedirect(reverse('main'))
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})


def upload_metafile(request):
    if request.method == 'POST':
        form = UploadMetaFileForm(request.POST, request.FILES)
        if form.is_valid():
            obj = ScenariosSet()
            obj.metafile = form.cleaned_data['metafile']
            obj.n_targets = form.cleaned_data['n_targets']
            obj.save()
            return HttpResponseRedirect(reverse('main'))
    else:
        form = UploadMetaFileForm()
    return render(request, 'upload.html', {'form': form})


def create_comparation(request):
    if request.method == 'POST':
        form = ComparationForm(request.POST, request.FILES)
        if form.is_valid():
            obj = ComparationObject()
            obj.obj1 = form.cleaned_data['obj1']
            obj.obj2 = form.cleaned_data['obj2']
            obj.slug = 'q'
            obj.save()
            return HttpResponseRedirect(reverse('main'))
    else:
        form = ComparationForm()
    return render(request, 'upload2.html', {'form': form})


def compare_list(request):
    recordings = ComparationObject.objects.filter()
    s_rec = []
    for rec in recordings:
        s_rec.append({"n_targ": rec.n_targets,
                      "title": rec.title,
                      "slug": rec.slug})
    return render(request, 'comparation.html', context={'data': s_rec})


def compare_details(request, slug):
    obj = get_object_or_404(ComparationObject, slug=slug)
    f = lambda arr: [float(a) for a in arr]
    rec = {"code0": f(obj.code0.split(sep='::')),
           "code1": f(obj.code1.split(sep='::')),
           "code2": f(obj.code2.split(sep='::')),
           "code4": f(obj.code4.split(sep='::')),
           "code5": f(obj.code5.split(sep='::')),
           "dists": f(obj.dists.split(sep='::')),
           "n_targ": obj.n_targets,
           "title": obj.title}
    return render(request, 'details_compare.html', context=rec)
