from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from builder import views as builder_views

admin.site.site_header = "Code2Resume Admin"
admin.site.site_title  = "Code2Resume"
admin.site.index_title = "App Management"

urlpatterns = [
    path('admin/',    admin.site.urls),
    path('home/', builder_views.landing, name='landing'),
    path('accounts/', include('allauth.urls')),
    path('u/',        include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('',          include('builder.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
