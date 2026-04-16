from django.urls import path
from . import views

app_name = 'builder'

urlpatterns = [
    path('', views.workspace, name='workspace'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
]