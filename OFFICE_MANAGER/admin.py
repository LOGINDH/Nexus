from django.contrib import admin
from .models import User, Project, Task


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'role', 'phone', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('username', 'email', 'phone', 'address')
    ordering = ('-created_at',)
    fields = ('username', 'email', 'password', 'role', 'phone', 'address')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'status', 'original_duration_days',
        'admin_assigned_duration_days', 'created_by', 'assigned_to_leader',
        'start_date', 'end_date', 'created_at'
    )
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'project', 'status', 'leader_assigned_duration_days',
        'assigned_to_employee', 'assigned_by', 'start_date', 'end_date',
        'completed_at'
    )
    list_filter = ('status', 'project', 'start_date', 'end_date')
    search_fields = ('title', 'description', 'submission_notes')
    ordering = ('-created_at',)
