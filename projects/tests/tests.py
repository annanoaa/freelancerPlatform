from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import User
from projects.models import Project, ProjectBid


class ProjectBidTests(APITestCase):
    def setUp(self):
        # Create a client user
        self.client_user = User.objects.create_user(
            username='clientuser',
            email='client@example.com',
            password='testpass123',
            role='CL'
        )

        # Create a freelancer user
        self.freelancer_user = User.objects.create_user(
            username='freelanceruser',
            email='freelancer@example.com',
            password='testpass123',
            role='FR'
        )

        # Create a test project
        self.project = Project.objects.create(
            client=self.client_user,
            title='Test Project',
            description='Test Description',
            budget_min=100,
            budget_max=500,
            deadline='2025-12-31T00:00:00Z',
            status='OPEN'
        )

        # Setup the URL
        self.url = reverse('project-bid-list')  # Make sure this matches your URL name

    def test_freelancer_can_bid(self):
        """Test that freelancers can submit bids"""
        self.client.force_authenticate(user=self.freelancer_user)

        bid_data = {
            'project': self.project.id,
            'amount': '300.00',
            'proposal': 'Test proposal',
            'delivery_time': 7
        }

        response = self.client.post(self.url, bid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProjectBid.objects.count(), 1)
        self.assertEqual(ProjectBid.objects.first().freelancer, self.freelancer_user)

    def test_client_cannot_bid(self):
        """Test that clients cannot submit bids"""
        self.client.force_authenticate(user=self.client_user)

        bid_data = {
            'project': self.project.id,
            'amount': '300.00',
            'proposal': 'Test proposal',
            'delivery_time': 7
        }

        response = self.client.post(self.url, bid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ProjectBid.objects.count(), 0)

    def test_cannot_bid_twice(self):
        """Test that freelancer cannot bid twice on same project"""
        self.client.force_authenticate(user=self.freelancer_user)

        bid_data = {
            'project': self.project.id,
            'amount': '300.00',
            'proposal': 'Test proposal',
            'delivery_time': 7
        }

        # First bid
        first_response = self.client.post(self.url, bid_data, format='json')
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProjectBid.objects.count(), 1)

        # Second bid should fail
        second_response = self.client.post(self.url, bid_data, format='json')
        self.assertEqual(second_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ProjectBid.objects.count(), 1)  # Count should still be 1
        self.assertIn('already submitted', str(second_response.data['detail']))