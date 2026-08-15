from django.db import models


class User(models.Model):

    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("tl", "Team Lead"),
        ("employee", "Employee"),
    ]

    username = models.CharField(
        max_length=100,
        unique=True
    )

    password = models.CharField(
        max_length=255
    )

    full_name = models.CharField(
        max_length=150
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


class Project(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    name = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True
    )

    assigned_to_tl = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_projects"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_projects"
    )

    start_date = models.DateField()

    end_date = models.DateField()

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class Task(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks"
    )

    title = models.CharField(
        max_length=200
    )

    assigned_to_employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_tasks"
    )

    assigned_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_tasks"
    )

    start_date = models.DateField()

    end_date = models.DateField()

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title