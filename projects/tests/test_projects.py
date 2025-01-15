from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from users.models import User, Skill
from projects.models import Project, ProjectBid


class ProjectManagementTests(APITestCase):
    def setUp(self):
        # Create client user
        self.client_user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpass123',
            role='CL'
        )

        # Create freelancer user
        self.freelancer = User.objects.create_user(
            username='testfreelancer',
            email='freelancer@example.com',
            password='testpass123',
            role='FR'
        )

        # Create some skills
        self.skill1 = Skill.objects.create(name='Python', category='Programming')
        self.skill2 = Skill.objects.create(name='Django', category='Web Development')

        # Base project data
        self.project_data = {
            'title': 'Test Project',
            'description': 'Test project description',
            'budget_min': '100.00',
            'budget_max': '500.00',
            'deadline': (timezone.now() + timedelta(days=30)).isoformat(),
            'required_skills': [self.skill1.id, self.skill2.id]
        }

    def test_project_creation(self):
        """Test project creation with valid data"""
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(reverse('project-list'), self.project_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], self.project_data['title'])
        self.assertEqual(response.data['status'], 'OPEN')

    def test_project_creation_as_freelancer(self):
        """Test that freelancers cannot create projects"""
        self.client.force_authenticate(user=self.freelancer)
        response = self.client.post(reverse('project-list'), self.project_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_project_update(self):
        """Test project update functionality"""
        # Create a project first
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(reverse('project-list'), self.project_data)
        project_id = response.data['id']

        # Update the project
        update_data = {
            'title': 'Updated Project Title',
            'description': 'Updated description'
        }
        response = self.client.patch(
            reverse('project-detail', kwargs={'pk': project_id}),
            update_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], update_data['title'])

    def test_project_deletion(self):
        """Test project deletion"""
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(reverse('project-list'), self.project_data)
        project_id = response.data['id']

        response = self.client.delete(
            reverse('project-detail', kwargs={'pk': project_id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify project is deleted
        response = self.client.get(
            reverse('project-detail', kwargs={'pk': project_id})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_project_listing_and_filtering(self):
        """Test project listing with filters"""
        self.client.force_authenticate(user=self.client_user)

        # Create multiple projects
        self.client.post(reverse('project-list'), self.project_data)

        project_data2 = self.project_data.copy()
        project_data2['title'] = 'Python Project'
        project_data2['budget_min'] = '200.00'
        project_data2['budget_max'] = '800.00'
        self.client.post(reverse('project-list'), project_data2)

        # Test filtering by budget
        response = self.client.get(reverse('project-list'), {'budget_min': '150.00'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Test searching by title
        response = self.client.get(reverse('project-list'), {'search': 'Python'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Python Project')

    def test_project_complete_lifecycle(self):
        """Test complete project lifecycle from creation to completion"""
        # 1. Create project as client
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(reverse('project-list'), self.project_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project_id = response.data['id']

        # 2. Submit bid as freelancer
        self.client.force_authenticate(user=self.freelancer)
        bid_data = {
            'project': project_id,
            'amount': '300.00',
            'proposal': 'I can do this project',
            'delivery_time': 14
        }
        response = self.client.post(
            reverse('project-submit-bid', kwargs={'pk': project_id}),
            bid_data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        bid_id = response.data['id']

        # 3. Accept bid as client
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(
            reverse('project-accept-bid', kwargs={'pk': project_id}),
            {'bid_id': bid_id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. Complete project
        response = self.client.post(
            reverse('project-complete-project', kwargs={'pk': project_id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 5. Verify final project status
        response = self.client.get(
            reverse('project-detail', kwargs={'pk': project_id})
        )
        self.assertEqual(response.data['status'], 'COMPLETED')