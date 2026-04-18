from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/',                    views.profile,      name='profile'),
    path('profile/edit/',               views.profile_edit, name='profile_edit'),
    path('resume/<slug:slug>/delete/',  views.resume_delete, name='resume_delete'),
    path('resume/<slug:slug>/open/',    views.resume_open,   name='resume_open'),
    path('resume/<slug:slug>/toggle-public/', views.resume_toggle_public, name='resume_toggle_public'),
]