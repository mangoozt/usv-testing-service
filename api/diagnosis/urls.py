from django.urls import path

from . import views

urlpatterns = [
    path('', views.main_view, name='main'),
    path('upload/', views.upload_file, name='upload'),
    path('upload/meta/', views.upload_metafile, name='upload_meta'),
    path('<slug:slug>', views.details, name='details'),
    path('compare/', views.create_comparation, name='compare'),
    path('list/', views.compare_list, name='list'),
    path('list/<slug:slug>', views.compare_details_view, name='comp_det')
]
