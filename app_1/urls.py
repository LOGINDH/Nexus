from django.urls import path
from .views import*


urlpatterns = [
    path("students/", get_students, name="get_students"),
    path("students/add/",add_student, name="add_student"),
    path("students/update/<int:id>/", update_student, name="update_student"),
    path("students/delete/<int:id>/", delete_student, name="delete_student"),
]

