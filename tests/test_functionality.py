from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, Profile
from projects.models import Project, ProjectBid

class UserAuthenticationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.test_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'FR'
        }
        self.login_data = {
            'login': 'test@example.com',
            'password': 'testpass123'
        }

    def test_user_registration(self):
        """Test user registration"""
        url = reverse('register')
        response = self.client.post(url, self.test_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.test_user_data['email']).exists())

    def test_user_login(self):
        """Test user login"""
        # First create a user
        User.objects.create_user(
            username=self.test_user_data['username'],
            email=self.test_user_data['email'],
            password=self.test_user_data['password'],
            role=self.test_user_data['role']
        )

        # Then try to login
        url = reverse('token_obtain_pair')
        response = self.client.post(url, self.login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

class ProfileTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='FR'
        )
        # Force authenticate the user
        self.client.force_authenticate(user=self.user)

    def test_profile_update(self):
        """Test profile update"""
        url = reverse('profile-list')  # Or use your actual URL name
        profile_data = {
            'bio': 'Test bio',
            'location': 'Test City',
            'hourly_rate': '25.00',
            'experience_years': 5
        }
        response = self.client.post(url, profile_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['bio'], 'Test bio')

class ProjectTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a test client user
        self.user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpass123',
            role='CL'
        )
        self.client.force_authenticate(user=self.user)

    def test_project_creation(self):
        """Test project creation"""
        url = reverse('project-list')  # Or use your actual URL name
        project_data = {
            'title': 'Test Project',
            'description': 'Test project description',
            'budget_min': '100.00',
            'budget_max': '500.00',
            'deadline': '2025-12-31T00:00:00Z'
        }
        response = self.client.post(url, project_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Project')