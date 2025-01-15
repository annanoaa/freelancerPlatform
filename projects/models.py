from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils import timezone

from users.models import User, Skill

class Project(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open for Bids'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    freelancer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_projects'
    )
    required_skills = models.ManyToManyField(Skill, related_name='required_for_projects')
    budget_min = models.DecimalField(max_digits=10, decimal_places=2)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2)
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.budget_min > self.budget_max:
            raise ValidationError("Minimum budget cannot exceed maximum budget")
        if self.deadline and self.deadline < timezone.now():
            raise ValidationError("Deadline cannot be in the past")

    def can_submit_bid(self, user):
        return (
                self.status == 'OPEN' and
                user.role == 'FR' and
                user != self.client and
                not self.bids.filter(freelancer=user).exists()
        )

    def award_to_freelancer(self, freelancer):
        if self.status != 'OPEN':
            raise ValidationError("Can only award open projects")
        self.freelancer = freelancer
        self.status = 'IN_PROGRESS'
        self.save()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['client']),
            models.Index(fields=['freelancer']),
            models.Index(fields=['created_at']),
        ]

class ProjectBid(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn')
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='bids')
    freelancer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    proposal = models.TextField()
    delivery_time = models.IntegerField(help_text="Delivery time in days")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['project', 'freelancer']
        ordering = ['amount']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

class ProjectFile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='project_files/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

class Milestone(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['due_date']