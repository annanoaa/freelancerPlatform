from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from users.models import User
from projects.models import Project, ProjectBid, Milestone


class MilestoneTests(APITestCase):
    def setUp(self):
        # Create users
        self.client_user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpass123',
            role='CL'
        )

        self.freelancer = User.objects.create_user(
            username='freelancer',
            email='freelancer@example.com',
            password='testpass123',
            role='FR'
        )

        # Create project
        self.project = Project.objects.create(
            title='Test Project',
            description='Test Description',
            client=self.client_user,
            freelancer=self.freelancer,
            budget_min=100.00,
            budget_max=500.00,
            deadline=timezone.now() + timedelta(days=30),
            status='IN_PROGRESS'
        )

        # Base milestone data
        self.milestone_data = {
            'project': self.project.id,
            'title': 'Test Milestone',
            'description': 'Test milestone description',
            'amount': 200.00,
            'due_date': (timezone.now() + timedelta(days=7)).isoformat()
        }

    def test_milestone_creation(self):
        """Test creating a milestone"""
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(reverse('milestone-list'), self.milestone_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], self.milestone_data['title'])

    def test_freelancer_cannot_create_milestone(self):
        """Test that freelancers cannot create milestones"""
        self.client.force_authenticate(user=self.freelancer)
        response = self.client.post(reverse('milestone-list'), self.milestone_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_milestone_completion(self):
        """Test milestone completion process"""
        # Create milestone
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(reverse('milestone-list'), self.milestone_data)
        milestone_id = response.data['id']

        # Start milestone
        milestone = Milestone.objects.get(id=milestone_id)
        milestone.status = 'IN_PROGRESS'
        milestone.save()

        # Complete milestone
        response = self.client.post(
            reverse('milestone-complete-milestone', kwargs={'pk': milestone_id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify milestone status
        response = self.client.get(
            reverse('milestone-detail', kwargs={'pk': milestone_id})
        )
        self.assertEqual(response.data['status'], 'COMPLETED')

    def test_milestone_listing(self):
        """Test listing milestones for a project"""
        # Create multiple milestones
        self.client.force_authenticate(user=self.client_user)
        self.client.post(reverse('milestone-list'), self.milestone_data)

        milestone_data2 = self.milestone_data.copy()
        milestone_data2['title'] = 'Second Milestone'
        self.client.post(reverse('milestone-list'), milestone_data2)

        # Test listing
        response = self.client.get(reverse('milestone-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_invalid_milestone_creation(self):
        """Test creating milestone with invalid data"""
        self.client.force_authenticate(user=self.client_user)

        # Test with past due date
        invalid_data = self.milestone_data.copy()
        invalid_data['due_date'] = (timezone.now() - timedelta(days=1)).isoformat()
        response = self.client.post(reverse('milestone-list'), invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test with amount exceeding project budget
        invalid_data = self.milestone_data.copy()
        invalid_data['amount'] = 1000.00
        response = self.client.post(reverse('milestone-list'), invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_milestone_update(self):
        """Test updating milestone details"""
        self.client.force_authenticate(user=self.client_user)

        # Create milestone
        response = self.client.post(reverse('milestone-list'), self.milestone_data)
        milestone_id = response.data['id']

        # Update milestone
        update_data = {
            'title': 'Updated Milestone',
            'description': 'Updated description'
        }
        response = self.client.patch(
            reverse('milestone-detail', kwargs={'pk': milestone_id}),
            update_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], update_data['title'])

    def test_project_completion_with_milestones(self):
        """Test project completion when all milestones are completed"""
        self.client.force_authenticate(user=self.client_user)

        # Create two milestones
        response1 = self.client.post(reverse('milestone-list'), self.milestone_data)
        milestone1_id = response1.data['id']

        milestone_data2 = self.milestone_data.copy()
        milestone_data2['title'] = 'Second Milestone'
        response2 = self.client.post(reverse('milestone-list'), milestone_data2)
        milestone2_id = response2.data['id']

        # Complete both milestones
        for milestone_id in [milestone1_id, milestone2_id]:
            milestone = Milestone.objects.get(id=milestone_id)
            milestone.status = 'IN_PROGRESS'
            milestone.save()

            response = self.client.post(
                reverse('milestone-complete-milestone', kwargs={'pk': milestone_id})
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify project status is automatically updated
        project = Project.objects.get(id=self.project.id)
        self.assertEqual(project.status, 'COMPLETED')