from django.urls import path
from . import views

urlpatterns = [
    # Dashboard Web UI
    path('', views.dashboard_view, name='dashboard'),

    # Auth
    path('login/', views.login_user, name='api-login'),
    path('token/refresh/', views.refresh_token, name='api-token-refresh'),

    # Admin
    path('office-admin/create-team-leader/', views.create_team_leader, name='api-admin-create-team-leader'),
    path('projects/create/', views.create_project, name='api-project-create'),
    path('projects/', views.list_projects, name='api-project-list'),
    path('projects/<int:pk>/update/', views.update_project, name='api-project-update'),
    path('projects/<int:pk>/status-update/', views.update_project_status, name='api-project-status-update'),
    path('projects/<int:pk>/delete/', views.delete_project, name='api-project-delete'),
    path('tasks/all/', views.list_admin_tasks, name='api-task-all'),

    # Team Leader
    path('team-leader/create-employee/', views.create_employee, name='api-team-leader-create-employee'),
    path('projects/assigned/', views.assigned_projects, name='api-project-assigned'),
    path('tasks/create/', views.create_task, name='api-task-create'),
    path('tasks/', views.list_leader_tasks, name='api-task-list'),
    path('tasks/<int:pk>/update/', views.update_task, name='api-task-update'),
    path('tasks/<int:pk>/delete/', views.delete_task, name='api-task-delete'),

    # Employee
    path('tasks/my-tasks/', views.my_tasks, name='api-task-my-tasks'),
    path('tasks/<int:pk>/status-update/', views.update_task_status, name='api-task-status-update'),

    # Utility & User Management
    path('users/', views.list_users, name='api-user-list'),
    path('users/<int:pk>/update/', views.update_user, name='api-user-update'),
    path('users/<int:pk>/delete/', views.delete_user, name='api-user-delete'),
    path('employees/', views.list_employees, name='api-employees-list'),

]
