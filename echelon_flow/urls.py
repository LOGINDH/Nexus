from django.urls import path

from . import views


urlpatterns = [

    # =========================
    # LOGIN
    # =========================

    path("login/",views.login),


    # =========================
    # ADMIN
    # =========================

    path("admin/create-tl/",views.create_tl),
    path("admin/projects/create/",views.create_project),
    path("admin/projects/",views.admin_projects),


    # =========================
    # TEAM LEAD
    # =========================

    path("tl/create-employee/",views.create_employee),
    path("tl/projects/",views.tl_projects),
    path("tl/tasks/create/",views.create_task),
    path("tl/tasks/",views.tl_tasks),
    path("tl/projects/<int:project_id>/status/",views.update_project_status),

    # =========================
    # EMPLOYEE
    # =========================

    path("employee/tasks/",views.employee_tasks),
    path("employee/tasks/<int:task_id>/status/",views.update_task_status),

]