from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from builder import views as builder_views

urlpatterns = [
    path('admin/',    admin.site.urls),
    path('home/', builder_views.landing, name='landing'),
    path('accounts/', include('allauth.urls')),        # allauth handles /accounts/login/, signup/, etc.
    path('u/',        include('accounts.urls')),        # our profile/resume URLs
    path('',          include('builder.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
