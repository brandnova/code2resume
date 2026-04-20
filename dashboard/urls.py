from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('',          views.overview,       name='overview'),
    path('exports/',  views.exports,        name='exports'),
    path('templates/',views.templates,      name='templates'),
    path('users/',    views.users,          name='users'),
]

