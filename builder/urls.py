from django.urls import path
from . import views

app_name = 'builder'

urlpatterns = [
    path('',                views.workspace,      name='workspace'),
    path('export/pdf/',     views.export_pdf,      name='export_pdf'),
    path('session/save/',   views.save_session,    name='save_session'),
    path('resume/save-as/', views.save_as_resume,  name='save_as_resume'),
    path('resume/update/',  views.update_resume,   name='update_resume'),
    path('resume/new/',     views.new_resume,     name='new_resume'),
    path('r/<slug:slug>/', views.public_resume, name='public_resume'),
]