from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views

router = DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'notifications', views.NotificationViewSet, basename='notification')

conversations_router = routers.NestedSimpleRouter(
    router,
    r'conversations',
    lookup='conversation'
)
conversations_router.register(
    r'messages',
    views.MessageViewSet,
    basename='conversation-messages'
)

urlpatterns = [
    path('', include(router.urls)),
    path('', include(conversations_router.urls)),
]