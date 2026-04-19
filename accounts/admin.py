from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Resume, ResumeTemplate


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('email', 'display_name', 'is_staff', 'date_joined')
    search_fields = ('email', 'display_name')
    fieldsets     = BaseUserAdmin.fieldsets + (
        ('Profile', {'fields': ('display_name', 'avatar_url', 'bio', 'website')}),
    )

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display  = ('title', 'user', 'framework', 'paper_size', 'is_public', 'updated_at')
    search_fields = ('title', 'user__email')
    list_filter   = ('framework', 'paper_size', 'is_public')

@admin.register(ResumeTemplate)
class ResumeTemplateAdmin(admin.ModelAdmin):
    list_display  = ('title', 'framework', 'paper_size', 'is_premium', 'is_active', 'order')
    list_editable = ('is_premium', 'is_active', 'order')
    list_filter   = ('is_premium', 'is_active', 'framework', 'paper_size')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'preview_image', 'is_premium', 'is_active', 'order')
        }),
        ('Content', {
            'fields': ('html_content', 'css_content', 'framework', 'paper_size'),
            'classes': ('wide',),
        }),
    )

