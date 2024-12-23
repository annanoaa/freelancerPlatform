from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.throttling import UserRateThrottle

from .models import Project, ProjectBid, ProjectFile, Milestone
from .serializers import (
    ProjectSerializer, ProjectListSerializer, ProjectBidSerializer,
    ProjectFileSerializer, MilestoneSerializer, ProjectCreateSerializer
)
from .permissions import (
    IsProjectOwner, IsProjectParticipant, CanSubmitBid,
    CanManageMilestones
)

import logging
logger = logging.getLogger(__name__)

class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling project-related operations.
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'required_skills__name']
    ordering_fields = ['created_at', 'deadline', 'budget_min', 'budget_max']

    throttle_classes = [UserRateThrottle]

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(
                f"Project created: {response.data['id']} by user {request.user.id}"
            )
            return response
        except Exception as e:
            logger.error(f"Project creation failed: {str(e)}")
            return Response(
                {"error": "Failed to create project"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Project.objects.none()

        queryset = Project.objects.select_related('client', 'freelancer') \
            .prefetch_related('required_skills', 'bids', 'files', 'milestones')

        # Cache handling
        cache_key = f'projects_query_{self.request.user.id}_{str(self.request.query_params)}'
        cached_queryset = cache.get(cache_key)
        if cached_queryset is not None:
            return cached_queryset

        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filter by skills
        skills = self.request.query_params.getlist('skills')
        if skills:
            queryset = queryset.filter(required_skills__id__in=skills)

        # Filter by budget range
        budget_min = self.request.query_params.get('budget_min', None)
        budget_max = self.request.query_params.get('budget_max', None)
        if budget_min:
            queryset = queryset.filter(budget_max__gte=budget_min)
        if budget_max:
            queryset = queryset.filter(budget_min__lte=budget_max)

        # Role-based filtering
        if self.request.user.role == 'FR':
            queryset = queryset.filter(
                Q(status='OPEN') |
                Q(freelancer=self.request.user) |
                Q(bids__freelancer=self.request.user)
            ).distinct()
        elif self.request.user.role == 'CL':
            queryset = queryset.filter(client=self.request.user)

        cache.set(cache_key, queryset, timeout=300)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        elif self.action == 'list':
            return ProjectListSerializer
        return ProjectSerializer

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

    @swagger_auto_schema(
        operation_summary="Submit Bid",
        request_body=ProjectBidSerializer,
        responses={
            201: ProjectBidSerializer,
            400: "Bad Request",
            403: "Forbidden - Not eligible to bid"
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[CanSubmitBid])
    def submit_bid(self, request, pk=None):
        project = self.get_object()
        serializer = ProjectBidSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(project=project, freelancer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Accept Bid",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['bid_id'],
            properties={
                'bid_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        responses={
            200: "Bid accepted successfully",
            400: "Bad Request",
            403: "Forbidden - Not project owner"
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsProjectOwner])
    def accept_bid(self, request, pk=None):
        project = self.get_object()
        bid_id = request.data.get('bid_id')

        try:
            bid = project.bids.get(id=bid_id, status='PENDING')
            bid.status = 'ACCEPTED'
            bid.save()

            project.status = 'IN_PROGRESS'
            project.freelancer = bid.freelancer
            project.save()

            project.bids.exclude(id=bid_id).update(status='REJECTED')

            return Response({'message': 'Bid accepted successfully'})
        except ProjectBid.DoesNotExist:
            return Response(
                {'error': 'Invalid bid ID or bid already processed'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_summary="Complete Project",
        responses={
            200: "Project completed successfully",
            400: "Bad Request - Project not in progress",
            403: "Forbidden - Not project participant"
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsProjectParticipant])
    def complete_project(self, request, pk=None):
        project = self.get_object()

        if project.status != 'IN_PROGRESS':
            return Response(
                {'error': 'Only in-progress projects can be completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        project.status = 'COMPLETED'
        project.save()
        return Response({'message': 'Project marked as completed'})



class ProjectBidViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing project bids.
    """
    serializer_class = ProjectBidSerializer
    permission_classes = [CanSubmitBid]

    def get_queryset(self):

        if getattr(self, 'swagger_fake_view', False):
            return ProjectBid.objects.none()
        return ProjectBid.objects.filter(
            Q(project__client=self.request.user) |
            Q(freelancer=self.request.user)
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get project from validated data
        project = serializer.validated_data.get('project')

        # Check if project exists and is open
        if not project:
            return Response(
                {"detail": "Project not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if project.status != 'OPEN':
            return Response(
                {"detail": "Project is not open for bidding"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for existing bid
        existing_bid = ProjectBid.objects.filter(
            project=project,
            freelancer=request.user
        ).exists()

        if existing_bid:
            return Response(
                {"detail": "You have already submitted a bid for this project"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create new bid
        serializer.save(freelancer=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def withdraw_bid(self, request, pk=None):
        bid = self.get_object()
        if bid.status != 'PENDING':
            return Response(
                {"detail": "Only pending bids can be withdrawn"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if bid.freelancer != request.user:
            return Response(
                {"detail": "You can only withdraw your own bids"},
                status=status.HTTP_403_FORBIDDEN
            )

        bid.status = 'WITHDRAWN'
        bid.save()
        return Response({"detail": "Bid withdrawn successfully"})

class ProjectFileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing project files.
    """
    serializer_class = ProjectFileSerializer
    permission_classes = [IsAuthenticated, IsProjectParticipant]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ProjectFile.objects.none()

        return ProjectFile.objects.filter(
            Q(project__client=self.request.user) |
            Q(project__freelancer=self.request.user)
        ).select_related('project', 'uploaded_by')

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class MilestoneViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing project milestones.
    """
    serializer_class = MilestoneSerializer
    permission_classes = [IsAuthenticated, CanManageMilestones]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Milestone.objects.none()

        return Milestone.objects.filter(
            Q(project__client=self.request.user) |
            Q(project__freelancer=self.request.user)
        ).select_related('project')

    def perform_create(self, serializer):
        project = serializer.validated_data['project']
        if project.client != self.request.user:
            raise PermissionError("Only project owner can create milestones")
        serializer.save()

    @swagger_auto_schema(
        operation_summary="Complete Milestone",
        responses={
            200: "Milestone completed successfully",
            400: "Bad Request - Milestone not in progress",
            403: "Forbidden - Not project participant"
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsProjectParticipant])
    def complete_milestone(self, request, pk=None):
        milestone = self.get_object()

        if milestone.status != 'IN_PROGRESS':
            return Response(
                {'error': 'Only in-progress milestones can be completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        milestone.status = 'COMPLETED'
        milestone.completed_at = timezone.now()
        milestone.save()

        return Response({'message': 'Milestone marked as completed'})