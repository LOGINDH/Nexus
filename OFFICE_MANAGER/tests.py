from django.test import TestCase
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import io

from .models import User, Project, Task
from .views import generate_jwt_tokens


class OfficeManagerStrictWorkflowTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Create Admin
        self.admin = User.objects.create(
            username='admin_user',
            email='admin@test.com',
            password='password123',
            role=User.ROLE_ADMIN
        )

        # Create Team Leader 1
        self.leader1 = User.objects.create(
            username='leader_user_1',
            email='leader1@test.com',
            password='password123',
            role=User.ROLE_TEAM_LEADER
        )

        # Create Team Leader 2
        self.leader2 = User.objects.create(
            username='leader_user_2',
            email='leader2@test.com',
            password='password123',
            role=User.ROLE_TEAM_LEADER
        )

        # Create Employee under Team Leader 1
        self.employee1 = User.objects.create(
            username='emp_under_tl1',
            email='emp1@test.com',
            password='password123',
            role=User.ROLE_EMPLOYEE,
            team_leader=self.leader1
        )

        # Create Employee under Team Leader 2
        self.employee2 = User.objects.create(
            username='emp_under_tl2',
            email='emp2@test.com',
            password='password123',
            role=User.ROLE_EMPLOYEE,
            team_leader=self.leader2
        )

        # Generate tokens
        self.admin_token = generate_jwt_tokens(self.admin)['access']
        self.leader1_token = generate_jwt_tokens(self.leader1)['access']
        self.leader2_token = generate_jwt_tokens(self.leader2)['access']
        self.employee1_token = generate_jwt_tokens(self.employee1)['access']

    def auth_header(self, token):
        return {'HTTP_AUTHORIZATION': f'Bearer {token}'}

    # 1. Admin creates Project, assigns to Team Leader → succeeds
    def test_admin_creates_project_assigned_to_team_leader_succeeds(self):
        resp = self.client.post('/projects/create/', {
            'title': 'Core Infrastructure Project',
            'description': 'Description',
            'original_duration_days': 30,
            'admin_assigned_duration_days': 20,
            'assigned_to_leader': self.leader1.id
        }, format='json', **self.auth_header(self.admin_token))

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['project']['assigned_to_leader'], self.leader1.id)

    # 2. Admin attempts to create Task → fails (403)
    def test_admin_attempts_to_create_task_fails(self):
        today = timezone.now().date()
        project = Project.objects.create(
            title='Project X',
            description='Desc',
            original_duration_days=30,
            admin_assigned_duration_days=20,
            start_date=today,
            end_date=today + timedelta(days=20),
            created_by=self.admin,
            assigned_to_leader=self.leader1
        )

        resp = self.client.post('/tasks/create/', {
            'project': project.id,
            'title': 'Admin Direct Task Creation',
            'description': 'Desc',
            'leader_assigned_duration_days': 5,
            'assigned_to_employee': self.employee1.id
        }, format='json', **self.auth_header(self.admin_token))

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # 3. Admin attempts to assign Project to an Employee-role user → fails (400)
    def test_admin_attempts_to_assign_project_to_employee_fails(self):
        resp = self.client.post('/projects/create/', {
            'title': 'Direct Employee Project Fail',
            'description': 'Description',
            'original_duration_days': 30,
            'admin_assigned_duration_days': 20,
            'assigned_to_leader': self.employee1.id  # Role is EMPLOYEE, not TEAM_LEADER
        }, format='json', **self.auth_header(self.admin_token))

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('assigned_to_leader', resp.data)
        self.assertIn('Projects can only be assigned to a Team Leader.', str(resp.data['assigned_to_leader']))

    # 4. Team Leader creates Task, assigns to their own Employee → succeeds & appears in GET /tasks/my-tasks/
    def test_team_leader_creates_task_for_own_employee_succeeds(self):
        today = timezone.now().date()
        project = Project.objects.create(
            title='Project Y',
            description='Desc',
            original_duration_days=30,
            admin_assigned_duration_days=20,
            start_date=today,
            end_date=today + timedelta(days=20),
            created_by=self.admin,
            assigned_to_leader=self.leader1
        )

        task_resp = self.client.post('/tasks/create/', {
            'project': project.id,
            'title': 'Valid Team Task',
            'description': 'Desc',
            'leader_assigned_duration_days': 5,
            'assigned_to_employee': self.employee1.id
        }, format='json', **self.auth_header(self.leader1_token))

        self.assertEqual(task_resp.status_code, status.HTTP_201_CREATED)

        # Check Employee 1's my-tasks endpoint
        my_tasks_resp = self.client.get('/tasks/my-tasks/', **self.auth_header(self.employee1_token))
        self.assertEqual(my_tasks_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(my_tasks_resp.data), 1)
        self.assertEqual(my_tasks_resp.data[0]['title'], 'Valid Team Task')

    # 5. Team Leader attempts to assign Task to an Employee NOT created by them → fails (403)
    def test_team_leader_assigns_task_to_other_tl_employee_fails(self):
        today = timezone.now().date()
        project = Project.objects.create(
            title='Project Z',
            description='Desc',
            original_duration_days=30,
            admin_assigned_duration_days=20,
            start_date=today,
            end_date=today + timedelta(days=20),
            created_by=self.admin,
            assigned_to_leader=self.leader1
        )

        # Leader 1 attempts to assign task to Employee 2 (who belongs to Leader 2)
        task_resp = self.client.post('/tasks/create/', {
            'project': project.id,
            'title': 'Cross-Team Assignment Attempt',
            'description': 'Desc',
            'leader_assigned_duration_days': 5,
            'assigned_to_employee': self.employee2.id  # Employee belongs to leader2
        }, format='json', **self.auth_header(self.leader1_token))

        self.assertEqual(task_resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('You can only assign tasks to employees you created.', task_resp.data['detail'])
