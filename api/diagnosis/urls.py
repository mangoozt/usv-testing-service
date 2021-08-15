from django.urls import path

from . import views

urlpatterns = [
    path('', views.main_view, name='main'),
    path('upload/', views.upload_file, name='upload'),
    path('upload/meta/', views.upload_metafile, name='upload_meta'),
    path('<slug:slug>', views.details, name='details'),
    path('<slug:slug>/plot/<type>', views.testing_result_plot, name='testing_result_plot'),
    path('<slug:slug>/plot', views.testing_result_plot, name='testing_result_plot'),
    path('compare/', views.create_comparation, name='compare'),
]
