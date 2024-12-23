from drf_yasg import openapi
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    UserSerializer, ProfileSerializer, SkillSerializer,
    UserRatingSerializer, TokenObtainPairSerializer, UserRegistrationSerializer, CustomTokenObtainPairSerializer
)
from .permissions import IsOwnerOrReadOnly
from .models import Skill, UserRating, User, Profile
from drf_yasg.utils import swagger_auto_schema
from .tasks import send_verification_email
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

from .utils import verify_token


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get current user's details",
        responses={200: UserSerializer}
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)



class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    # permission_classes = (AllowAny,)

    @swagger_auto_schema(
        operation_summary="Login user",
        operation_description="Login with username/email and password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['login', 'password'],
            properties={
                'login': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Username or Email'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='password',
                    description='Password'
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            401: 'Invalid credentials'
        }
    )
    def post(self, request, *args, **kwargs):
        print(f"Received login data: {request.data}")  # Debug print
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            print(f"Validation error: {str(e)}")  # Debug print
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]


class UserRatingViewSet(viewsets.ModelViewSet):
    serializer_class = UserRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserRating.objects.filter(to_user=self.kwargs['user_pk'])

    def perform_create(self, serializer):
        to_user = User.objects.get(pk=self.kwargs['user_pk'])
        serializer.save(from_user=self.request.user, to_user=to_user)

    @action(detail=False, methods=['get'])
    def my_ratings(self, request):
        ratings = UserRating.objects.filter(to_user=request.user)
        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data)

class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Profile.objects.none()
        return Profile.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Create profile with logged-in user
        try:
            # First check if profile already exists
            profile = Profile.objects.filter(user=request.user).first()
            if profile:
                serializer = self.get_serializer(profile, data=request.data, partial=True)
            else:
                serializer = self.get_serializer(data=request.data)

            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    @swagger_auto_schema(
        operation_summary="Register a new user",
        operation_description="Creates a new user account and sends verification email",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="User successfully registered",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'role': openapi.Schema(type=openapi.TYPE_STRING),
                                'is_email_verified': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            }
                        ),
                        'tokens': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                                'access': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    }
                )
            ),
            400: "Bad Request - Invalid data provided",
            500: "Internal Server Error"
        },
        security=[]
    )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()

                # Generate and print token immediately
                from .utils import generate_verification_token
                test_token = generate_verification_token(user)
                print("\n")
                print("=" * 50)
                print("IMMEDIATE TOKEN GENERATION")
                print("=" * 50)
                print(f"Token for {user.email}: {test_token}")
                print("=" * 50)
                print("\n")

                # Send to Celery
                send_verification_email.delay(user.id)

                # Generate tokens
                refresh = RefreshToken.for_user(user)
                access = AccessToken.for_user(user)
                tokens = {
                    'refresh': str(refresh),
                    'access': str(access),
                }

                # Send verification email asynchronously
                send_verification_email.delay(user.id)

                return Response({
                    "message": "Registration successful. Please check your email to verify your account.",
                    "user": UserSerializer(user).data,
                    "tokens": tokens
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({
                    "message": "Registration failed",
                    "error": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, token):
    email = verify_token(token)
    if email:
        try:
            user = User.objects.get(email=email)
            if not user.is_email_verified:
                user.is_email_verified = True
                user.save()
                return Response({
                    "message": "Email verification successful."
                })
            return Response({
                "message": "Email already verified."
            })
        except User.DoesNotExist:
            pass
    return Response({
        "message": "Invalid or expired verification link."
    }, status=status.HTTP_400_BAD_REQUEST)
