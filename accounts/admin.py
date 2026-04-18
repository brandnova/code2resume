from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Resume


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