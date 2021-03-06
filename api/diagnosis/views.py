import datetime
import io
import json

from django.http import HttpResponseRedirect, FileResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from matplotlib import pyplot as plt

from .forms import UploadFileForm, UploadMetaFileForm, ComparationForm
from .models import TestingRecording, ScenariosSet


def main_view(request):
    """
    Plots graphs from info aus DB
    @param request:
    @return:
    """
    recordings = TestingRecording.objects.filter(processed=True).order_by('-pk')
    s_rec = []
    for rec in recordings:
        title = rec.title
        if rec.commit_sha1:
            title = (rec.commit_sha1[:7] if len(rec.commit_sha1) > 7 else rec.commit_sha1) + ' - ' + title
        s_rec.append({"date": str(rec.date),
                      "n_targ": rec.n_targets,
                      "title": title,
                      "slug": rec.slug,
                      })
    return render(request, 'main.html', context={'data': s_rec})


def details(request, slug):
    obj = get_object_or_404(TestingRecording, slug=slug)

    df = obj.to_dataframe().reset_index()
    chart_data = [list(map(str, df.columns.tolist()))] + df.values.tolist()
    scenarios_pivot_table = obj.pivot_scenario_types()
    if scenarios_pivot_table is not None:
        scenarios_pivot_table = scenarios_pivot_table.to_html()
    else:
        scenarios_pivot_table = "Report file is missing"

    rec = {"chart_data": json.dumps(list(chart_data), ensure_ascii=False),
           "date": str(obj.date),
           "n_targ": obj.n_targets,
           "title": obj.title,
           "n_sc": obj.n_scenarios,
           "statistics_file": obj.file,
           "img": reverse('testing_result_plot', kwargs={'slug': obj.slug}),
           "img_min": reverse('testing_result_plot', kwargs={'slug': obj.slug, 'graph_type': 'minister'}),
           "scenarios_pivot_table": scenarios_pivot_table,
           "sha1": obj.commit_sha1}
    return render(request, 'details.html', context=rec)


def testing_result_plot(request, slug, graph_type='normal'):
    obj = get_object_or_404(TestingRecording, slug=slug)
    fig: plt.Figure = obj.gen_plot(graph_type)
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    response = FileResponse(buf, content_type="image/png", filename=f'{obj.slug}_{type}.png')
    return response


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            obj = TestingRecording()
            obj.date = datetime.datetime.now()
            obj.file = form.cleaned_data['file']
            obj.title = form.cleaned_data['title']
            obj.commit_sha1 = form.cleaned_data['commit_sha1']
            obj.build_number = form.cleaned_data['build_number']
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


def create_comparation(request, obj_slug=None, prev_slug=None):
    form = ComparationForm(request.GET, request.FILES)
    if form.is_valid():
        obj: TestingRecording = form.cleaned_data['obj']
        prev: TestingRecording = form.cleaned_data['prev']
        cmp_result = obj.compare(prev).reset_index()
        chart_data = [list(map(str, cmp_result.columns.tolist()))] + cmp_result.values.tolist()
        rec = {
            "chart_data": json.dumps(list(chart_data), ensure_ascii=False),
            "title": "?????????????????? ??????????????????????",
            "form": ComparationForm(initial={'prev': prev, 'obj': obj})
            # "form": ComparationForm()
        }
        return render(request, 'details_compare.html', context=rec)
    else:
        form = ComparationForm()
        return render(request, 'details_compare.html', {'form': form, "title": "?????????????????? ??????????????????????", })
