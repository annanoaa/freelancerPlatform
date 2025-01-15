from django.contrib import admin
from .models import Project, ProjectBid, ProjectFile, Milestone

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'freelancer', 'status', 'budget_min', 'budget_max', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'client__email', 'freelancer__email')
    raw_id_fields = ('client', 'freelancer', 'required_skills')
    date_hierarchy = 'created_at'

@admin.register(ProjectBid)
class ProjectBidAdmin(admin.ModelAdmin):
    list_display = ('project', 'freelancer', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('project__title', 'freelancer__email', 'proposal')
    raw_id_fields = ('project', 'freelancer')

@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    list_display = ('project', 'uploaded_by', 'description', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('project__title', 'description', 'uploaded_by__email')
    raw_id_fields = ('project', 'uploaded_by')

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('project', 'title', 'amount', 'status', 'due_date', 'completed_at')
    list_filter = ('status', 'due_date', 'completed_at')
    search_fields = ('project__title', 'title', 'description')
    raw_id_fields = ('project',)
    date_hierarchy = 'due_date'