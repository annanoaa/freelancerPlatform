from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from users.models import User, Skill
from projects.models import Project, ProjectBid


class BiddingSystemTests(APITestCase):
    def setUp(self):
        # Create client user
        self.client_user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpass123',
            role='CL'
        )

        # Create freelancer users
        self.freelancer1 = User.objects.create_user(
            username='freelancer1',
            email='freelancer1@example.com',
            password='testpass123',
            role='FR'
        )

        self.freelancer2 = User.objects.create_user(
            username='freelancer2',
            email='freelancer2@example.com',
            password='testpass123',
            role='FR'
        )

        # Create project
        self.project = Project.objects.create(
            title='Test Project',
            description='Test Description',
            client=self.client_user,
            budget_min=100.00,
            budget_max=500.00,
            deadline=timezone.now() + timedelta(days=30)
        )

        # Base bid data
        self.bid_data = {
            'project': self.project.id,
            'amount': 300.00,
            'proposal': 'Test proposal',
            'delivery_time': 14
        }

    def test_valid_bid_submission(self):
        """Test submitting a valid bid"""
        self.client.force_authenticate(user=self.freelancer1)
        response = self.client.post(reverse('project-bid-list'), self.bid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'PENDING')

    def test_bid_outside_budget_range(self):
        """Test bid with amount outside project budget range"""
        self.client.force_authenticate(user=self.freelancer1)

        # Test bid below minimum
        invalid_bid = self.bid_data.copy()
        invalid_bid['amount'] = 50.00
        response = self.client.post(reverse('project-bid-list'), invalid_bid)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test bid above maximum
        invalid_bid['amount'] = 600.00
        response = self.client.post(reverse('project-bid-list'), invalid_bid)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_multiple_bids_same_freelancer(self):
        """Test that a freelancer cannot submit multiple bids for the same project"""
        self.client.force_authenticate(user=self.freelancer1)

        # Submit first bid
        response = self.client.post(reverse('project-bid-list'), self.bid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Try to submit second bid
        response = self.client.post(reverse('project-bid-list'), self.bid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bid_on_closed_project(self):
        """Test bidding on a closed project"""
        # Close the project
        self.project.status = 'COMPLETED'
        self.project.save()

        self.client.force_authenticate(user=self.freelancer1)
        response = self.client.post(reverse('project-bid-list'), self.bid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bid_withdrawal(self):
        """Test bid withdrawal functionality"""
        self.client.force_authenticate(user=self.freelancer1)

        # Submit bid
        response = self.client.post(reverse('project-bid-list'), self.bid_data)
        bid_id = response.data['id']

        # Withdraw bid
        response = self.client.post(
            reverse('project-bid-withdraw-bid', kwargs={'pk': bid_id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify bid status
        response = self.client.get(
            reverse('project-bid-detail', kwargs={'pk': bid_id})
        )
        self.assertEqual(response.data['status'], 'WITHDRAWN')

    def test_client_cannot_bid(self):
        """Test that clients cannot submit bids"""
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(reverse('project-bid-list'), self.bid_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bid_acceptance(self):
        """Test bid acceptance process"""
        # Submit bid as freelancer
        self.client.force_authenticate(user=self.freelancer1)
        response = self.client.post(reverse('project-bid-list'), self.bid_data)
        bid_id = response.data['id']

        # Accept bid as client
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(
            reverse('project-accept-bid', kwargs={'pk': self.project.id}),
            {'bid_id': bid_id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify project and bid status
        project = Project.objects.get(id=self.project.id)
        self.assertEqual(project.status, 'IN_PROGRESS')
        self.assertEqual(project.freelancer, self.freelancer1)

        bid = ProjectBid.objects.get(id=bid_id)
        self.assertEqual(bid.status, 'ACCEPTED')