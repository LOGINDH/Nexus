import time
import json
import base64
import hmac
import hashlib
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from datetime import timedelta

import random
import time
import requests

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import User, Project, Task
from .serializers import (
    UserSerializer,
    TeamLeaderCreateSerializer,
    EmployeeCreateSerializer,
    ProjectSerializer,
    TaskSerializer,
    TaskStatusUpdateSerializer,
)

try:
    import jwt
    HAS_PYJWT = True
except ImportError:
    HAS_PYJWT = False

SECRET_KEY = getattr(settings, 'SECRET_KEY', 'office-manager-secret-key-123456')


# ==========================================
# CUSTOM JWT AUTHENTICATION HELPERS
# ==========================================
def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _hs256_encode(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _base64url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = _base64url_encode(json.dumps(payload).encode('utf-8'))
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = _base64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def _hs256_decode(token: str) -> tuple[dict | None, str | None]:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None, "Invalid token structure"
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
        if _base64url_encode(expected_sig) != sig_b64:
            return None, "Invalid signature"
        
        padding = '=' * (4 - (len(payload_b64) % 4))
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        if 'exp' in payload and time.time() > payload['exp']:
            return None, "Token has expired"
            
        return payload, None
    except Exception as e:
        return None, f"Token decode error: {str(e)}"


def generate_jwt_tokens(user: User) -> dict:
    now = int(time.time())
    access_exp = now + (24 * 3600)
    refresh_exp = now + (7 * 24 * 3600)

    access_payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'token_type': 'access',
        'iat': now,
        'exp': access_exp
    }

    refresh_payload = {
        'user_id': user.id,
        'token_type': 'refresh',
        'iat': now,
        'exp': refresh_exp
    }

    if HAS_PYJWT:
        access_token = jwt.encode(access_payload, SECRET_KEY, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm='HS256')
        if isinstance(access_token, bytes):
            access_token = access_token.decode('utf-8')
            refresh_token = refresh_token.decode('utf-8')
    else:
        access_token = _hs256_encode(access_payload)
        refresh_token = _hs256_encode(refresh_payload)

    return {
        'access': access_token,
        'refresh': refresh_token
    }


def decode_jwt_token(token: str) -> tuple[dict | None, str | None]:
    if HAS_PYJWT:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return payload, None
        except jwt.ExpiredSignatureError:
            return None, "Token has expired"
        except jwt.InvalidTokenError as e:
            return None, f"Invalid token: {str(e)}"
    else:
        return _hs256_decode(token)


def get_authenticated_user(request) -> tuple[User | None, Response | None]:
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, Response(
            {'detail': 'Authentication credentials were not provided. Authorization header with Bearer token is required.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token = auth_header.split(' ')[1].strip()
    payload, error = decode_jwt_token(token)

    if error:
        return None, Response({'detail': error}, status=status.HTTP_401_UNAUTHORIZED)

    if payload.get('token_type') != 'access':
        return None, Response({'detail': 'Invalid token type. Access token expected.'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        user = User.objects.get(id=payload.get('user_id'))
        return user, None
    except User.DoesNotExist:
        return None, Response({'detail': 'User specified in token does not exist in custom User table.'}, status=status.HTTP_401_UNAUTHORIZED)


def check_role(user: User, allowed_roles: list[str]) -> Response | None:
    if user.role not in allowed_roles:
        return Response(
            {'detail': f'Permission denied. Action requires one of roles: {", ".join(allowed_roles)}. Your role is {user.role}.'},
            status=status.HTTP_403_FORBIDDEN
        )
    return None


# ==========================================
# 0. DASHBOARD VIEW (Renders Web UI)
# ==========================================
def dashboard_view(request):
    return render(request, 'OFFICE_MANAGER/dashboard.html')


# ==========================================
# 1. AUTHENTICATION ENDPOINTS (FBV)
# ==========================================
@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def login_user(request):
    """
    POST /login/ or /api/login/
    Authenticates custom User using plain text password comparison (NO check_password).
    """
    username_or_email = request.data.get('username') or request.data.get('email')
    password = request.data.get('password')

    if not username_or_email or not password:
        return Response(
            {'detail': 'Please provide both username/email and password.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        if '@' in username_or_email:
            user = User.objects.get(email=username_or_email)
        else:
            user = User.objects.get(username=username_or_email)
    except User.DoesNotExist:
        return Response(
            {'detail': 'Invalid credentials. User not found.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if user.password != password:
        return Response(
            {'detail': 'Invalid credentials. Wrong password.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    tokens = generate_jwt_tokens(user)
    return Response({
        'message': 'Login successful',
        'tokens': tokens,
        'user': UserSerializer(user).data
    }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def refresh_token(request):
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({'detail': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)

    payload, error = decode_jwt_token(refresh_token)
    if error:
        return Response({'detail': error}, status=status.HTTP_401_UNAUTHORIZED)

    if payload.get('token_type') != 'refresh':
        return Response({'detail': 'Invalid token type. Refresh token expected.'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        user = User.objects.get(id=payload.get('user_id'))
    except User.DoesNotExist:
        return Response({'detail': 'User does not exist.'}, status=status.HTTP_401_UNAUTHORIZED)

    new_tokens = generate_jwt_tokens(user)
    return Response({
        'access': new_tokens['access'],
        'refresh': new_tokens['refresh']
    }, status=status.HTTP_200_OK)


# ==========================================
# 2. ADMIN ENDPOINTS (FBV)
# ==========================================
@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def create_team_leader(request):
    """
    POST /office-admin/create-team-leader/ or /api/admin/create-team-leader/
    Admin creates Team Leader accounts from inside Admin Dashboard.
    """
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_ADMIN])
    if role_err:
        return role_err

    serializer = TeamLeaderCreateSerializer(data=request.data)
    if serializer.is_valid():
        team_leader = serializer.save()
        return Response({
            'message': 'Team Leader created successfully',
            'user': UserSerializer(team_leader).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def create_project(request):
    """
    POST /projects/create/ or /api/projects/create/
    Only Admin can create a Project and assign it to a Team Leader.
    """
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_ADMIN])
    if role_err:
        return role_err

    serializer = ProjectSerializer(data=request.data)
    if serializer.is_valid():
        project = serializer.save(created_by=user)
        return Response({
            'message': 'Project created successfully',
            'project': ProjectSerializer(project).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def list_projects(request):
    """
    GET /projects/ or /api/projects/
    Admin views all projects (read-only). Team Leader views assigned projects. Employees have zero project access.
    """
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    if user.role == User.ROLE_EMPLOYEE:
        return Response(
            {'detail': 'Permission denied. Employees do not have access to project listing.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if user.role == User.ROLE_ADMIN:
        projects = Project.objects.all()
    else:  # TEAM_LEADER
        projects = Project.objects.filter(assigned_to_leader=user)

    for p in projects:
        p.check_overdue()

    serializer = ProjectSerializer(projects, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['PUT', 'PATCH'])
@authentication_classes([])
@permission_classes([])
def update_project(request, pk):
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_ADMIN])
    if role_err:
        return role_err

    try:
        project = Project.objects.get(pk=pk)
    except Project.DoesNotExist:
        return Response({'detail': f'Project with ID {pk} not found.'}, status=status.HTTP_404_NOT_FOUND)

    partial = request.method == 'PATCH'
    serializer = ProjectSerializer(project, data=request.data, partial=partial)

    if serializer.is_valid():
        updated_project = serializer.save()
        return Response({
            'message': 'Project updated successfully',
            'project': ProjectSerializer(updated_project).data
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['PUT', 'PATCH'])
@authentication_classes([])
@permission_classes([])
def update_project_status(request, pk):
    """
    PUT/PATCH /projects/<id>/status-update/
    Allows assigned Team Leader (or Admin) to update project status (PENDING, IN_PROGRESS, COMPLETED).
    """
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_TEAM_LEADER, User.ROLE_ADMIN])
    if role_err:
        return role_err

    try:
        project = Project.objects.get(pk=pk)
    except Project.DoesNotExist:
        return Response({'detail': f'Project with ID {pk} not found.'}, status=status.HTTP_404_NOT_FOUND)

    if user.role == User.ROLE_TEAM_LEADER and project.assigned_to_leader.id != user.id:
        return Response(
            {'detail': 'Permission denied. You can only update status for projects assigned to you.'},
            status=status.HTTP_403_FORBIDDEN
        )

    new_status = request.data.get('status')
    valid_statuses = [Project.STATUS_PENDING, Project.STATUS_IN_PROGRESS, Project.STATUS_COMPLETED]
    if not new_status or new_status not in valid_statuses:
        return Response(
            {'detail': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    project.status = new_status
    project.save()

    return Response({
        'message': 'Project status updated successfully',
        'project': ProjectSerializer(project).data
    }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['DELETE'])
@authentication_classes([])
@permission_classes([])
def delete_project(request, pk):
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_ADMIN])
    if role_err:
        return role_err

    try:
        project = Project.objects.get(pk=pk)
    except Project.DoesNotExist:
        return Response({'detail': f'Project with ID {pk} not found.'}, status=status.HTTP_404_NOT_FOUND)

    project.delete()
    return Response({'message': 'Project deleted successfully'}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def list_admin_tasks(request):
    """
    GET /api/tasks/all/
    Read-only oversight endpoint for Admin to view all tasks across the system.
    """
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_ADMIN])
    if role_err:
        return role_err

    tasks = Task.objects.all()
    for t in tasks:
        t.check_overdue()

    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def list_users(request):
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_ADMIN, User.ROLE_TEAM_LEADER])
    if role_err:
        return role_err

    role_filter = request.query_params.get('role')
    if role_filter:
        users = User.objects.filter(role=role_filter)
    elif user.role == User.ROLE_ADMIN:
        users = User.objects.filter(role=User.ROLE_TEAM_LEADER)
    else:
        users = User.objects.all()

    serializer = UserSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def list_employees(request):
    """
    GET /employees/
    Team Leaders and Admins list registered Employees.
    For Team Leader, returns employees assigned to their team OR unassigned employees.
    """
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_TEAM_LEADER, User.ROLE_ADMIN])
    if role_err:
        return role_err

    if user.role == User.ROLE_TEAM_LEADER:
        employees = User.objects.filter(role=User.ROLE_EMPLOYEE).filter(models.Q(team_leader=user) | models.Q(team_leader__isnull=True))
    else:
        employees = User.objects.filter(role=User.ROLE_EMPLOYEE)

    serializer = UserSerializer(employees, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['PUT', 'PATCH'])
@authentication_classes([])
@permission_classes([])
def update_user(request, pk):
    """
    PUT/PATCH /users/<id>/update/
    Allows Admin to edit any user's profile details.
    """
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_ADMIN])
    if role_err:
        return role_err

    try:
        target_user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'detail': f'User with ID {pk} not found.'}, status=status.HTTP_404_NOT_FOUND)

    partial = request.method == 'PATCH'
    serializer = UserSerializer(target_user, data=request.data, partial=partial)

    if serializer.is_valid():
        updated_user = serializer.save()
        if 'password' in request.data and request.data['password']:
            updated_user.password = request.data['password']
            updated_user.save()
        return Response({
            'message': 'User updated successfully',
            'user': UserSerializer(updated_user).data
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['DELETE'])
@authentication_classes([])
@permission_classes([])
def delete_user(request, pk):
    """
    DELETE /users/<id>/delete/
    Allows Admin to delete any user.
    """
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_ADMIN])
    if role_err:
        return role_err

    try:
        target_user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'detail': f'User with ID {pk} not found.'}, status=status.HTTP_404_NOT_FOUND)

    if target_user.id == user.id:
        return Response({'detail': 'You cannot delete your own admin account.'}, status=status.HTTP_400_BAD_REQUEST)

    target_user.delete()
    return Response({'message': 'User deleted successfully'}, status=status.HTTP_200_OK)


# ==========================================
# 3. TEAM LEADER ENDPOINTS (FBV)
# ==========================================
@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def create_employee(request):
    """
    POST /team-leader/create-employee/ or /api/team-leader/create-employee/
    Team Leader creates Employee accounts and links employee.team_leader = user.
    """
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_TEAM_LEADER])
    if role_err:
        return role_err

    serializer = EmployeeCreateSerializer(data=request.data)
    if serializer.is_valid():
        employee = serializer.save(team_leader=user)
        return Response({
            'message': 'Employee created successfully',
            'user': UserSerializer(employee).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def assigned_projects(request):
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_TEAM_LEADER])
    if role_err:
        return role_err

    projects = Project.objects.filter(assigned_to_leader=user)
    for p in projects:
        p.check_overdue()

    serializer = ProjectSerializer(projects, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def create_task(request):
    """
    POST /tasks/create/ or /api/tasks/create/
    ONLY assigned Team Leader can create tasks for their employees. Admin CANNOT create tasks.
    """
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    # Admin is strictly forbidden from creating tasks
    if user.role != User.ROLE_TEAM_LEADER:
        return Response(
            {'detail': 'Permission denied. Only Team Leaders can create tasks.'},
            status=status.HTTP_403_FORBIDDEN
        )

    project_id = request.data.get('project')
    if not project_id:
        return Response({'detail': 'Project ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return Response({'detail': f'Project with ID {project_id} was not found.'}, status=status.HTTP_404_NOT_FOUND)

    if project.assigned_to_leader.id != user.id:
        return Response(
            {'detail': 'Permission denied. Only the assigned Team Leader can create tasks for this project.'},
            status=status.HTTP_403_FORBIDDEN
        )

    emp_id = request.data.get('assigned_to_employee')
    if not emp_id:
        return Response({'detail': 'assigned_to_employee is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        employee = User.objects.get(pk=emp_id)
    except User.DoesNotExist:
        return Response({'detail': f'Employee with ID {emp_id} was not found.'}, status=status.HTTP_404_NOT_FOUND)

    if employee.role != User.ROLE_EMPLOYEE:
        return Response({'detail': 'Tasks can only be assigned to an Employee.'}, status=status.HTTP_400_BAD_REQUEST)

    if employee.team_leader is None:
        employee.team_leader = user
        employee.save()
    elif employee.team_leader != user:
        return Response(
            {'detail': 'You can only assign tasks to employees you created.'},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = TaskSerializer(data=request.data)
    if serializer.is_valid():
        try:
            task = serializer.save(assigned_by=user)
            return Response({
                'message': 'Task created and assigned successfully',
                'task': TaskSerializer(task).data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': f'Task creation failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def list_leader_tasks(request):
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_TEAM_LEADER])
    if role_err:
        return role_err

    tasks = Task.objects.filter(project__assigned_to_leader=user)
    for t in tasks:
        t.check_overdue()

    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['PUT', 'PATCH'])
@authentication_classes([])
@permission_classes([])
def update_task(request, pk):
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_TEAM_LEADER])
    if role_err:
        return role_err

    try:
        task = Task.objects.get(pk=pk)
    except Task.DoesNotExist:
        return Response({'detail': f'Task with ID {pk} not found.'}, status=status.HTTP_404_NOT_FOUND)

    if task.project.assigned_to_leader.id != user.id:
        return Response(
            {'detail': 'Permission denied. You can only update tasks under your assigned projects.'},
            status=status.HTTP_403_FORBIDDEN
        )

    partial = request.method == 'PATCH'
    serializer = TaskSerializer(task, data=request.data, partial=partial)

    if serializer.is_valid():
        updated_task = serializer.save()
        return Response({
            'message': 'Task updated successfully',
            'task': TaskSerializer(updated_task).data
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['DELETE'])
@authentication_classes([])
@permission_classes([])
def delete_task(request, pk):
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_TEAM_LEADER])
    if role_err:
        return role_err

    try:
        task = Task.objects.get(pk=pk)
    except Task.DoesNotExist:
        return Response({'detail': f'Task with ID {pk} not found.'}, status=status.HTTP_404_NOT_FOUND)

    if task.project.assigned_to_leader.id != user.id:
        return Response(
            {'detail': 'Permission denied. You can only delete tasks under your assigned projects.'},
            status=status.HTTP_403_FORBIDDEN
        )

    task.delete()
    return Response({'message': 'Task deleted successfully'}, status=status.HTTP_200_OK)


# ==========================================
# 4. EMPLOYEE ENDPOINTS (FBV)
# ==========================================
@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def my_tasks(request):
    """
    GET /tasks/my-tasks/ or /api/tasks/my-tasks/
    Returns strictly tasks assigned to the logged-in employee: Task.objects.filter(assigned_to_employee=user)
    """
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_EMPLOYEE])
    if role_err:
        return role_err

    tasks = Task.objects.filter(assigned_to_employee=user)
    for t in tasks:
        t.check_overdue()

    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['PUT', 'PATCH'])
@authentication_classes([])
@permission_classes([])
def update_task_status(request, pk):
    """
    PUT/PATCH /tasks/<id>/status-update/ or /api/tasks/<id>/status-update/
    Only the assigned Employee can update status to COMPLETED, recording completed_at.
    """
    user, err_resp = get_authenticated_user(request)
    if err_resp:
        return err_resp

    role_err = check_role(user, [User.ROLE_EMPLOYEE])
    if role_err:
        return role_err

    try:
        task = Task.objects.get(pk=pk)
    except Task.DoesNotExist:
        return Response({'detail': f'Task with ID {pk} not found.'}, status=status.HTTP_404_NOT_FOUND)

    if task.assigned_to_employee.id != user.id:
        return Response(
            {'detail': 'Permission denied. Only the assigned Employee can update task status.'},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = TaskStatusUpdateSerializer(task, data=request.data, partial=True)
    if serializer.is_valid():
        updated_task = serializer.save()
        return Response({
            'message': 'Task status updated successfully',
            'task': TaskSerializer(updated_task).data
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



