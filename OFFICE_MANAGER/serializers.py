from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta, datetime, date
from .models import User, Project, Task


def parse_date_obj(val):
    if not val:
        return None
    if isinstance(val, date):
        return val
    if hasattr(val, 'date'):
        return val.date()
    if isinstance(val, str):
        try:
            return datetime.strptime(val.strip(), '%Y-%m-%d').date()
        except ValueError:
            return None
    return None


class UserSerializer(serializers.ModelSerializer):
    team_leader_detail = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'phone', 'address', 'team_leader', 'team_leader_detail', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_team_leader_detail(self, obj):
        if obj.team_leader:
            return {'id': obj.team_leader.id, 'username': obj.team_leader.username, 'email': obj.team_leader.email}
        return None


class TeamLeaderCreateSerializer(serializers.ModelSerializer):
    """
    Admin-only serializer inside Admin Dashboard.
    Creates user with role = TEAM_LEADER.
    """
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'phone', 'address']
        read_only_fields = ['id']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        validated_data['role'] = User.ROLE_TEAM_LEADER
        return User.objects.create(**validated_data)


class EmployeeCreateSerializer(serializers.ModelSerializer):
    """
    Team Leader-only serializer inside Team Leader Dashboard.
    Creates user with role = EMPLOYEE and sets team_leader to request.user.
    """
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'phone', 'address']
        read_only_fields = ['id']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        validated_data['role'] = User.ROLE_EMPLOYEE
        return User.objects.create(**validated_data)


class ProjectSerializer(serializers.ModelSerializer):
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    assigned_to_leader_detail = UserSerializer(source='assigned_to_leader', read_only=True)
    total_task_duration_days = serializers.IntegerField(read_only=True)
    remaining_unallocated_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'original_duration_days',
            'admin_assigned_duration_days', 'created_by', 'created_by_detail',
            'assigned_to_leader', 'assigned_to_leader_detail', 'start_date',
            'end_date', 'status', 'total_task_duration_days',
            'remaining_unallocated_days', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'end_date', 'created_at']

    def validate_assigned_to_leader(self, value):
        if value.role != User.ROLE_TEAM_LEADER:
            raise serializers.ValidationError("Projects can only be assigned to a Team Leader.")
        return value

    def validate(self, data):
        original_duration = data.get('original_duration_days')
        if original_duration is None and self.instance:
            original_duration = self.instance.original_duration_days

        admin_assigned = data.get('admin_assigned_duration_days')
        if admin_assigned is None and self.instance:
            admin_assigned = self.instance.admin_assigned_duration_days

        if original_duration and admin_assigned:
            if admin_assigned > original_duration:
                raise serializers.ValidationError({
                    'admin_assigned_duration_days': f"Admin assigned duration ({admin_assigned} days) cannot exceed original project duration ({original_duration} days)."
                })
        return data


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_employee_detail = UserSerializer(source='assigned_to_employee', read_only=True)
    assigned_by_detail = UserSerializer(source='assigned_by', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'project', 'project_title', 'title', 'description',
            'leader_assigned_duration_days', 'assigned_to_employee',
            'assigned_to_employee_detail', 'assigned_by', 'assigned_by_detail',
            'start_date', 'end_date', 'status', 'submission_notes',
            'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'assigned_by', 'completed_at', 'created_at', 'updated_at']

    def validate_assigned_to_employee(self, value):
        if value.role != User.ROLE_EMPLOYEE:
            raise serializers.ValidationError("Tasks can only be assigned to an Employee.")
        return value

    def validate(self, data):
        project = data.get('project') or (self.instance.project if self.instance else None)
        task_duration = data.get('leader_assigned_duration_days') or (self.instance.leader_assigned_duration_days if self.instance else None)
        raw_start = data.get('start_date') or (self.instance.start_date if self.instance else timezone.now().date())
        raw_end = data.get('end_date')

        task_start = parse_date_obj(raw_start) or timezone.now().date()
        task_end = parse_date_obj(raw_end)

        if project:
            proj_start = parse_date_obj(project.start_date)
            proj_end = parse_date_obj(project.end_date)

            if task_start and task_duration and not task_end:
                task_end = task_start + timedelta(days=task_duration)

            if proj_start and task_start and task_start < proj_start:
                raise serializers.ValidationError({
                    'start_date': f"Task start date ({task_start}) cannot be earlier than project start date ({proj_start})."
                })

            if proj_end and task_end and task_end > proj_end:
                raise serializers.ValidationError({
                    'end_date': f"Task end date ({task_end}) cannot be later than project end date ({proj_end})."
                })

            if task_duration:
                tasks_query = project.tasks.all()
                if self.instance:
                    tasks_query = tasks_query.exclude(pk=self.instance.pk)

                existing_duration_sum = sum(t.leader_assigned_duration_days for t in tasks_query)
                new_total = existing_duration_sum + task_duration

                if new_total > project.admin_assigned_duration_days:
                    remaining_days = project.admin_assigned_duration_days - existing_duration_sum
                    raise serializers.ValidationError({
                        'leader_assigned_duration_days': (
                            f"Task duration ({task_duration} days) exceeds remaining project duration "
                            f"({remaining_days} days remaining out of {project.admin_assigned_duration_days} total project days)."
                        )
                    })
        return data


class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['status', 'submission_notes', 'completed_at']
        read_only_fields = ['completed_at']

    def validate_status(self, value):
        valid_statuses = [Task.STATUS_ASSIGNED, Task.STATUS_IN_PROGRESS, Task.STATUS_COMPLETED]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return value

    def update(self, instance, validated_data):
        new_status = validated_data.get('status', instance.status)
        if new_status == Task.STATUS_COMPLETED and instance.status != Task.STATUS_COMPLETED:
            instance.completed_at = timezone.now()
        instance.status = new_status
        if 'submission_notes' in validated_data:
            instance.submission_notes = validated_data['submission_notes']
        instance.save()
        return instance
