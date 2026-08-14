from django.db import models
from django.utils import timezone
from datetime import timedelta


def get_current_date():
    return timezone.now().date()


class User(models.Model):
    ROLE_ADMIN = 'ADMIN'
    ROLE_TEAM_LEADER = 'TEAM_LEADER'
    ROLE_EMPLOYEE = 'EMPLOYEE'

    ROLE_CHOICES = (
        (ROLE_ADMIN, 'Admin'),
        (ROLE_TEAM_LEADER, 'Team Leader'),
        (ROLE_EMPLOYEE, 'Employee'),
    )

    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_EMPLOYEE)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    team_leader = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_employees'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'office_manager_users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.role})"


class Project(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_OVERDUE = 'OVERDUE'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_OVERDUE, 'Overdue'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    original_duration_days = models.PositiveIntegerField()
    admin_assigned_duration_days = models.PositiveIntegerField()
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_projects'
    )
    assigned_to_leader = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='assigned_projects'
    )
    start_date = models.DateField(default=get_current_date)
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'office_manager_projects'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.status}"

    def save(self, *args, **kwargs):
        start = self.start_date
        if hasattr(start, 'date'):
            start = start.date()

        if start and self.admin_assigned_duration_days and not self.end_date:
            self.end_date = start + timedelta(days=self.admin_assigned_duration_days)

        self.check_overdue(save=False)
        super().save(*args, **kwargs)

    def check_overdue(self, save=True):
        if self.status != self.STATUS_COMPLETED and self.end_date:
            end = self.end_date
            if hasattr(end, 'date'):
                end = end.date()
            if timezone.now().date() > end:
                self.status = self.STATUS_OVERDUE
                if save and self.pk:
                    super().save(update_fields=['status'])

    @property
    def total_task_duration_days(self):
        aggregate = self.tasks.aggregate(total=models.Sum('leader_assigned_duration_days'))
        return aggregate['total'] or 0

    @property
    def remaining_unallocated_days(self):
        return self.admin_assigned_duration_days - self.total_task_duration_days


class Task(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_ASSIGNED = 'ASSIGNED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_OVERDUE = 'OVERDUE'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_OVERDUE, 'Overdue'),
    )

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='tasks'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    leader_assigned_duration_days = models.PositiveIntegerField()
    assigned_to_employee = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='assigned_tasks'
    )
    assigned_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_tasks'
    )
    start_date = models.DateField(default=get_current_date)
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ASSIGNED)
    submission_notes = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'office_manager_tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.project.title}) - {self.status}"

    def save(self, *args, **kwargs):
        start = self.start_date
        if hasattr(start, 'date'):
            start = start.date()

        if start and self.leader_assigned_duration_days and not self.end_date:
            self.end_date = start + timedelta(days=self.leader_assigned_duration_days)

        self.check_overdue(save=False)
        super().save(*args, **kwargs)

    def check_overdue(self, save=True):
        if self.status != self.STATUS_COMPLETED and self.end_date:
            end = self.end_date
            if hasattr(end, 'date'):
                end = end.date()
            if timezone.now().date() > end:
                self.status = self.STATUS_OVERDUE
                if save and self.pk:
                    super().save(update_fields=['status'])
