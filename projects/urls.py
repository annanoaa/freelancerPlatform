from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'bids', views.ProjectBidViewSet, basename='project-bid')
router.register(r'files', views.ProjectFileViewSet, basename='project-file')
router.register(r'milestones', views.MilestoneViewSet, basename='milestone')

urlpatterns = [
    path('', include(router.urls)),
]