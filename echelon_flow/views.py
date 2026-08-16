from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

import json
from datetime import date

from django.http import JsonResponse

from .models import User, Project, Task


# ============================================================
# LOGIN
# ============================================================

@csrf_exempt
def login(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "POST method required"
            },
            status=405
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid JSON"
            },
            status=400
        )

    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    if not username or not password or not role:
        return JsonResponse(
            {
                "success": False,
                "message": "username, password and role are required"
            },
            status=400
        )

    if role not in ["admin", "tl", "employee"]:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid role"
            },
            status=400
        )

    try:
        user = User.objects.get(
            username=username,
            role=role,
            is_active=True
        )
    except User.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid username or role"
            },
            status=401
        )

    if user.password != password:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid password"
            },
            status=401
        )

    return JsonResponse(
        {
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role
            }
        }
    )


# ============================================================
# ADMIN - CREATE TEAM LEAD
# ============================================================

@csrf_exempt
def create_tl(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "POST method required"
            },
            status=405
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid JSON"
            },
            status=400
        )

    admin_id = data.get("admin_id")
    username = data.get("username")
    password = data.get("password")
    full_name = data.get("full_name")

    if not all([
        admin_id,
        username,
        password,
        full_name
    ]):
        return JsonResponse(
            {
                "success": False,
                "message": "admin_id, username, password and full_name are required"
            },
            status=400
        )

    try:
        admin = User.objects.get(
            id=admin_id,
            role="admin",
            is_active=True
        )
    except User.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Valid admin not found"
            },
            status=403
        )

    if User.objects.filter(username=username).exists():
        return JsonResponse(
            {
                "success": False,
                "message": "Username already exists"
            },
            status=409
        )

    tl = User.objects.create(
        username=username,
        password=password,
        full_name=full_name,
        role="tl",
        created_by=admin
    )

    return JsonResponse(
        {
            "success": True,
            "message": "Team Lead created successfully",
            "tl": {
                "id": tl.id,
                "username": tl.username,
                "full_name": tl.full_name,
                "role": tl.role
            }
        },
        status=201
    )


# ============================================================
# ADMIN - CREATE PROJECT
# ============================================================

@csrf_exempt
def create_project(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "POST method required"
            },
            status=405
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid JSON"
            },
            status=400
        )

    admin_id = data.get("admin_id")
    name = data.get("name")
    description = data.get("description", "")
    tl_id = data.get("assigned_to_tl")
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    if not all([
        admin_id,
        name,
        tl_id,
        start_date,
        end_date
    ]):
        return JsonResponse(
            {
                "success": False,
                "message": "admin_id, name, assigned_to_tl, start_date and end_date are required"
            },
            status=400
        )

    # Check admin
    try:
        admin = User.objects.get(
            id=admin_id,
            role="admin",
            is_active=True
        )
    except User.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Valid admin not found"
            },
            status=403
        )

    # Check TL
    try:
        tl = User.objects.get(
            id=tl_id,
            role="tl",
            is_active=True
        )
    except User.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Valid Team Lead not found"
            },
            status=404
        )

    # Convert dates
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "message": "Date format must be YYYY-MM-DD"
            },
            status=400
        )

    if start > end:
        return JsonResponse(
            {
                "success": False,
                "message": "start_date cannot be after end_date"
            },
            status=400
        )

    project = Project.objects.create(
        name=name,
        description=description,
        assigned_to_tl=tl,
        created_by=admin,
        start_date=start,
        end_date=end
    )

    return JsonResponse(
        {
            "success": True,
            "message": "Project created successfully",
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "assigned_to_tl": tl.username,
                "created_by": admin.username,
                "start_date": str(project.start_date),
                "end_date": str(project.end_date),
                "status": project.status
            }
        },
        status=201
    )


# ============================================================
# ADMIN - VIEW ALL PROJECTS
# ============================================================

@csrf_exempt
def admin_projects(request):

    if request.method != "GET":
        return JsonResponse(
            {
                "success": False,
                "message": "GET method required"
            },
            status=405
        )

    admin_id = request.GET.get("admin_id")

    if not admin_id:
        return JsonResponse(
            {
                "success": False,
                "message": "admin_id is required"
            },
            status=400
        )

    try:
        User.objects.get(
            id=admin_id,
            role="admin",
            is_active=True
        )
    except User.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Valid admin not found"
            },
            status=403
        )

    projects = Project.objects.select_related(
        "assigned_to_tl",
        "created_by"
    ).all()

    result = []

    for project in projects:

        result.append(
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "assigned_to_tl": project.assigned_to_tl.username,
                "created_by": project.created_by.username,
                "start_date": str(project.start_date),
                "end_date": str(project.end_date),
                "status": project.status
            }
        )

    return JsonResponse(
        {
            "success": True,
            "count": len(result),
            "projects": result
        }
    )


# ============================================================
# TL - CREATE EMPLOYEE
# ============================================================

@csrf_exempt
def create_employee(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "POST method required"
            },
            status=405
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid JSON"
            },
            status=400
        )

    tl_id = data.get("tl_id")
    username = data.get("username")
    password = data.get("password")
    full_name = data.get("full_name")

    if not all([
        tl_id,
        username,
        password,
        full_name
    ]):
        return JsonResponse(
            {
                "success": False,
                "message": "tl_id, username, password and full_name are required"
            },
            status=400
        )

    try:
        tl = User.objects.get(
            id=tl_id,
            role="tl",
            is_active=True
        )
    except User.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Valid Team Lead not found"
            },
            status=403
        )

    if User.objects.filter(username=username).exists():
        return JsonResponse(
            {
                "success": False,
                "message": "Username already exists"
            },
            status=409
        )

    employee = User.objects.create(
        username=username,
        password=password,
        full_name=full_name,
        role="employee",
        created_by=tl
    )

    return JsonResponse(
        {
            "success": True,
            "message": "Employee created successfully",
            "employee": {
                "id": employee.id,
                "username": employee.username,
                "full_name": employee.full_name,
                "role": employee.role,
                "created_by": tl.username
            }
        },
        status=201
    )


# ============================================================
# TL - VIEW ASSIGNED PROJECTS
# ============================================================

@csrf_exempt
def tl_projects(request):

    if request.method != "GET":
        return JsonResponse(
            {
                "success": False,
                "message": "GET method required"
            },
            status=405
        )

    tl_id = request.GET.get("tl_id")

    if not tl_id:
        return JsonResponse(
            {
                "success": False,
                "message": "tl_id is required"
            },
            status=400
        )

    try:
        User.objects.get(
            id=tl_id,
            role="tl",
            is_active=True
        )
    except User.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Valid Team Lead not found"
            },
            status=403
        )

    projects = Project.objects.filter(
        assigned_to_tl_id=tl_id
    )

    result = []

    for project in projects:

        result.append(
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "start_date": str(project.start_date),
                "end_date": str(project.end_date),
                "status": project.status
            }
        )

    return JsonResponse(
        {
            "success": True,
            "count": len(result),
            "projects": result
        }
    )


# ============================================================
# TL - CREATE TASK
# ============================================================

@csrf_exempt
def create_task(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "POST method required"
            },
            status=405
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid JSON"
            },
            status=400
        )

    tl_id = data.get("tl_id")
    project_id = data.get("project_id")
    title = data.get("title")
    employee_id = data.get("assigned_to_employee")
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    if not all([
        tl_id,
        project_id,
        title,
        employee_id,
        start_date,
        end_date
    ]):
        return JsonResponse(
            {
                "success": False,
                "message": "All task fields are required"
            },
            status=400
        )

    # Check TL
    try:
        tl = User.objects.get(
            id=tl_id,
            role="tl",
            is_active=True
        )
    except User.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Valid Team Lead not found"
            },
            status=403
        )

    # Check project belongs to TL
    try:
        project = Project.objects.get(
            id=project_id,
            assigned_to_tl=tl
        )
    except Project.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Project not assigned to this Team Lead"
            },
            status=404
        )

    # Check employee belongs to TL
    try:
        employee = User.objects.get(
            id=employee_id,
            role="employee",
            created_by=tl,
            is_active=True
        )
    except User.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Employee does not belong to this Team Lead"
            },
            status=404
        )

    # Convert dates
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "message": "Date format must be YYYY-MM-DD"
            },
            status=400
        )

    if start > end:
        return JsonResponse(
            {
                "success": False,
                "message": "start_date cannot be after end_date"
            },
            status=400
        )

    # Task must be inside project period
    if start < project.start_date or end > project.end_date:
        return JsonResponse(
            {
                "success": False,
                "message": "Task period must be inside project period"
            },
            status=400
        )

    task = Task.objects.create(
        project=project,
        title=title,
        assigned_to_employee=employee,
        assigned_by=tl,
        start_date=start,
        end_date=end
    )

    return JsonResponse(
        {
            "success": True,
            "message": "Task created successfully",
            "task": {
                "id": task.id,
                "title": task.title,
                "project": project.name,
                "assigned_to_employee": employee.username,
                "assigned_by": tl.username,
                "start_date": str(task.start_date),
                "end_date": str(task.end_date),
                "status": task.status
            }
        },
        status=201
    )


# ============================================================
# TL - UPDATE PROJECT STATUS
# ============================================================

@csrf_exempt
def update_project_status(request, project_id):

    if request.method != "PATCH":
        return JsonResponse(
            {
                "success": False,
                "message": "PATCH method required"
            },
            status=405
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid JSON"
            },
            status=400
        )

    tl_id = data.get("tl_id")
    status = data.get("status")

    if not tl_id or not status:
        return JsonResponse(
            {
                "success": False,
                "message": "tl_id and status are required"
            },
            status=400
        )

    if status not in [
        "pending",
        "in_progress",
        "completed"
    ]:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid project status"
            },
            status=400
        )

    try:
        tl = User.objects.get(
            id=tl_id,
            role="tl",
            is_active=True
        )
    except User.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Valid Team Lead not found"
            },
            status=403
        )

    try:
        project = Project.objects.get(
            id=project_id,
            assigned_to_tl=tl
        )
    except Project.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Project not found"
            },
            status=404
        )

    project.status = status
    project.save(update_fields=["status"])

    return JsonResponse(
        {
            "success": True,
            "message": "Project status updated successfully",
            "project": {
                "id": project.id,
                "name": project.name,
                "status": project.status
            }
        }
    )


# ============================================================
# TL - VIEW THEIR TASKS
# ============================================================

@csrf_exempt
def tl_tasks(request):

    if request.method != "GET":
        return JsonResponse(
            {
                "success": False,
                "message": "GET method required"
            },
            status=405
        )

    tl_id = request.GET.get("tl_id")

    if not tl_id:
        return JsonResponse(
            {
                "success": False,
                "message": "tl_id is required"
            },
            status=400
        )

    try:
        tl = User.objects.get(
            id=tl_id,
            role="tl",
            is_active=True
        )
    except User.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Valid Team Lead not found"
            },
            status=403
        )

    tasks = Task.objects.filter(
        assigned_by=tl
    ).select_related(
        "project",
        "assigned_to_employee"
    )

    result = []

    for task in tasks:

        result.append(
            {
                "id": task.id,
                "title": task.title,
                "project": task.project.name,
                "employee": task.assigned_to_employee.username,
                "start_date": str(task.start_date),
                "end_date": str(task.end_date),
                "status": task.status
            }
        )

    return JsonResponse(
        {
            "success": True,
            "count": len(result),
            "tasks": result
        }
    )


# ============================================================
# EMPLOYEE - VIEW TASKS
# ============================================================

@csrf_exempt
def employee_tasks(request):

    if request.method != "GET":
        return JsonResponse(
            {
                "success": False,
                "message": "GET method required"
            },
            status=405
        )

    employee_id = request.GET.get("employee_id")

    if not employee_id:
        return JsonResponse(
            {
                "success": False,
                "message": "employee_id is required"
            },
            status=400
        )

    try:
        employee = User.objects.get(
            id=employee_id,
            role="employee",
            is_active=True
        )
    except User.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Valid employee not found"
            },
            status=403
        )

    tasks = Task.objects.filter(
        assigned_to_employee=employee
    ).select_related(
        "project",
        "assigned_by"
    )

    result = []

    for task in tasks:

        result.append(
            {
                "id": task.id,
                "title": task.title,
                "project": task.project.name,
                "assigned_by": task.assigned_by.username,
                "start_date": str(task.start_date),
                "end_date": str(task.end_date),
                "status": task.status
            }
        )

    return JsonResponse(
        {
            "success": True,
            "count": len(result),
            "tasks": result
        }
    )


# ============================================================
# EMPLOYEE - UPDATE TASK STATUS
# ============================================================

@csrf_exempt
def update_task_status(request, task_id):

    if request.method != "PATCH":
        return JsonResponse(
            {
                "success": False,
                "message": "PATCH method required"
            },
            status=405
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid JSON"
            },
            status=400
        )

    employee_id = data.get("employee_id")
    status = data.get("status")

    if not employee_id or not status:
        return JsonResponse(
            {
                "success": False,
                "message": "employee_id and status are required"
            },
            status=400
        )

    if status not in [
        "pending",
        "in_progress",
        "completed"
    ]:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid task status"
            },
            status=400
        )

    try:
        employee = User.objects.get(
            id=employee_id,
            role="employee",
            is_active=True
        )
    except User.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Valid employee not found"
            },
            status=403
        )

    try:
        task = Task.objects.get(
            id=task_id,
            assigned_to_employee=employee
        )
    except Task.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Task not found"
            },
            status=404
        )

    task.status = status
    task.save(update_fields=["status"])

    return JsonResponse(
        {
            "success": True,
            "message": "Task status updated successfully",
            "task": {
                "id": task.id,
                "title": task.title,
                "status": task.status
            }
        }
    )

def dashboard(request):
    return render(
        request,
        "dashboard.html"
    )    