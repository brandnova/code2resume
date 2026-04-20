from django.contrib import admin
from .models import SiteVisit, PDFExport, TemplateLoad, DailyStat


@admin.register(SiteVisit)
class SiteVisitAdmin(admin.ModelAdmin):
    list_display  = ('date', 'session_hash_short', 'is_authed', 'created_at')
    list_filter   = ('date', 'is_authed')
    date_hierarchy = 'created_at'

    def session_hash_short(self, obj):
        return obj.session_hash[:12] + '…'
    session_hash_short.short_description = 'Session'


@admin.register(PDFExport)
class PDFExportAdmin(admin.ModelAdmin):
    list_display  = ('created_at', 'paper_size', 'framework', 'success', 'duration_ms', 'user')
    list_filter   = ('success', 'paper_size', 'framework')
    date_hierarchy = 'created_at'


@admin.register(TemplateLoad)
class TemplateLoadAdmin(admin.ModelAdmin):
    list_display  = ('created_at', 'template', 'user')
    list_filter   = ('template',)
    date_hierarchy = 'created_at'


@admin.register(DailyStat)
class DailyStatAdmin(admin.ModelAdmin):
    list_display  = (
        'date', 'unique_visitors', 'authed_visitors',
        'new_users', 'resumes_created', 'pdfs_exported',
        'pdf_failures', 'template_loads'
    )
    date_hierarchy = 'date'
    ordering       = ('-date',)

