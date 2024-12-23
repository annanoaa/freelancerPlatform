from os import access

from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from django.db.models import Avg
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Profile, Skill, UserRating


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_email_verified')
        read_only_fields = ('is_email_verified',)


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_email_verified']
        read_only_fields = ['id', 'is_email_verified']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserInfoSerializer(read_only=True)
    class Meta:
        model = Profile
        fields = [
            'user',
            'bio',
            'location',
            'hourly_rate',
            'experience_years',
            'linkedin_url',
            'github_url',
            'portfolio_website',
            'skills'
        ]

        extra_kwargs = {
            'bio': {'required': False},
            'location': {'required': False},
            'hourly_rate': {'required': False},
            'experience_years': {'required': False},
            'linkedin_url': {'required': False},
            'github_url': {'required': False},
            'portfolio_website': {'required': False},
            'skills': {'required': False},
        }


class UserRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRating
        fields = '__all__'
        read_only_fields = ('from_user',)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    #username_field = 'login'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login'] = serializers.CharField(write_only=True)
        self.fields['password'] = serializers.CharField(write_only=True, style={'input_type': 'password'})
        if 'username' in self.fields:
            del self.fields['username']

    def validate(self, attrs):
        login = attrs.get('login')
        password = attrs.get('password')

        if not login or not password:
            raise serializers.ValidationError({
                'detail': 'Both login and password are required.'
            })

            # Try to find the user
        if '@' in login:
            user = User.objects.filter(email=login).first()
        else:
            user = User.objects.filter(username=login).first()

        if not user:
            raise serializers.ValidationError({
                'detail': 'No active account found with the given credentials.'
            })

            # Authenticate the user
        authenticated_user = authenticate(
            username=user.username,
            password=password
        )

        if not authenticated_user:
            raise serializers.ValidationError({
                'detail': 'Invalid credentials.'
            })

        # Create the token
        refresh = self.get_token(authenticated_user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        return token


class UserDetailSerializer(UserSerializer):
    profile = ProfileSerializer(read_only=True)
    average_rating = serializers.SerializerMethodField()
    total_ratings = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role',
                 'profile', 'average_rating', 'total_ratings')

    def get_average_rating(self, obj):
        return obj.ratings_received.aggregate(
            avg_rating=Avg('quality_rating')
        )['avg_rating']or 0.0

    def get_total_ratings(self, obj):
        return obj.ratings_received.count()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        validators=[validate_password]
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    username = serializers.CharField(
        required=True,
        min_length=3,
        max_length=150
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password',
            'password2',
            'first_name',
            'last_name',
            'role',
            'phone_number'
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'role': {'required': True},
            'email': {'required': True}
        }

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value.lower()  # Convert username to lowercase for consistency

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value.lower()  # Convert email to lowercase for consistency

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user