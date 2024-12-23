from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import Project, ProjectBid, Milestone


@receiver(post_save, sender=Project)
def clear_project_cache(sender, instance, **kwargs):
    """Clear project-related cache when a project is saved"""
    cache.delete(f'projects_query_{instance.client.id}_')
    if instance.freelancer:
        cache.delete(f'projects_query_{instance.freelancer.id}_')


@receiver(post_save, sender=ProjectBid)
def handle_bid_status_change(sender, instance, created, **kwargs):
    """Handle actions when a bid status changes"""
    if not created and instance.status == 'ACCEPTED':
        # Update project status and freelancer
        project = instance.project
        project.status = 'IN_PROGRESS'
        project.freelancer = instance.freelancer
        project.save()

        # Reject other bids
        ProjectBid.objects.filter(project=project) \
            .exclude(id=instance.id) \
            .update(status='REJECTED')


@receiver(post_save, sender=Milestone)
def check_project_completion(sender, instance, **kwargs):
    """Check if all milestones are completed to mark project as completed"""
    project = instance.project
    if project.status == 'IN_PROGRESS':
        all_milestones = project.milestones.all()
        if all_milestones and all(m.status == 'COMPLETED' for m in all_milestones):
            project.status = 'COMPLETED'
            project.save()