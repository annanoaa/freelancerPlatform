from rest_framework import serializers
from .models import Project, ProjectBid, ProjectFile, Milestone
from users.serializers import UserSerializer, SkillSerializer


class ProjectFileSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = ProjectFile
        fields = '__all__'
        read_only_fields = ('uploaded_by',)


class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = '__all__'
        read_only_fields = ('created_at', 'completed_at')


class ProjectBidSerializer(serializers.ModelSerializer):
    freelancer = UserSerializer(read_only=True)

    class Meta:
        model = ProjectBid
        fields = '__all__'
        read_only_fields = ('status', 'created_at', 'updated_at', 'freelancer')

    def validate(self, data):
        project = data['project']
        if data['amount'] < project.budget_min or data['amount'] > project.budget_max:
            raise serializers.ValidationError({
                "amount": "Bid amount must be within the project's budget range"
            })
        return data


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('title', 'description', 'required_skills', 'budget_min',
                  'budget_max', 'deadline')

    def validate(self, data):
        if data['budget_min'] > data['budget_max']:
            raise serializers.ValidationError({
                "budget": "Minimum budget cannot be greater than maximum budget"
            })
        return data


class ProjectSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    freelancer = UserSerializer(read_only=True)
    required_skills = SkillSerializer(many=True, read_only=True)
    bids = ProjectBidSerializer(many=True, read_only=True)
    files = ProjectFileSerializer(many=True, read_only=True)
    milestones = MilestoneSerializer(many=True, read_only=True)
    total_bids = serializers.SerializerMethodField()
    average_bid = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ('status', 'created_at', 'updated_at', 'client',
                            'freelancer')

    def get_total_bids(self, obj):
        return obj.bids.count()

    def get_average_bid(self, obj):
        bids = obj.bids.all()
        if not bids:
            return 0
        return sum(bid.amount for bid in bids) / len(bids)


class ProjectListSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    required_skills = SkillSerializer(many=True, read_only=True)
    total_bids = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'title', 'status', 'budget_min', 'budget_max',
                  'created_at', 'deadline', 'total_bids', 'client',
                  'required_skills')

    def get_total_bids(self, obj):
        return obj.bids.count()