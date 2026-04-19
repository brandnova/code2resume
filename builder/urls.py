from django.urls import path
from . import views

app_name = 'builder'

urlpatterns = [
    path('',                 views.workspace,      name='workspace'),
    path('export/pdf/',      views.export_pdf,     name='export_pdf'),
    path('session/save/',    views.save_session,   name='save_session'),
    path('session/clear/',   views.clear_session,  name='clear_session'),
    path('resume/save/',     views.save_as_resume, name='save_as_resume'),
    path('r/<slug:slug>/',   views.public_resume,  name='public_resume'),
    path('templates/',                   views.template_library, name='template_library'),
    path('templates/<slug:slug>/load/',  views.load_template,    name='load_template'),
]
