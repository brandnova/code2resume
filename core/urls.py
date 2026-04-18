from django.contrib import admin
from django.urls import path, include
from builder import views as builder_views

urlpatterns = [
    path('admin/',    admin.site.urls),
    path('home/', builder_views.landing, name='landing'),
    path('accounts/', include('allauth.urls')),        # allauth handles /accounts/login/, signup/, etc.
    path('u/',        include('accounts.urls')),        # our profile/resume URLs
    path('',          include('builder.urls')),
]