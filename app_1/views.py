from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Student
import json



# GET - Fetch all students
@csrf_exempt
def get_students(request):
    if request.method == "GET":
        students = Student.objects.all()
        data = list(students.values())
        return JsonResponse(data, safe=False)

    return JsonResponse({"error": "Method Not Allowed"}, status=405)


# POST - Add a new student
@csrf_exempt
def add_student(request):
    if request.method == "POST":
        data = json.loads(request.body)

        Student.objects.create(
            name=data["name"],
            age=data["age"],
            course=data["course"]
        )

        return JsonResponse(
            {"message": "Student Added Successfully"},
            status=201
        )

    return JsonResponse({"error": "Method Not Allowed"}, status=405)

# PUT - Update an existing student
@csrf_exempt
def update_student(request, id):
    if request.method == "PUT":
        student = Student.objects.get(id=id)

        data = json.loads(request.body)

        student.name = data["name"]
        student.age = data["age"]
        student.course = data["course"]

        student.save()

        return JsonResponse({"message": "Updated Successfully"})


#DELETE - Delete an existing student
@csrf_exempt
def delete_student(request, id):
    if request.method == "DELETE":
        student = Student.objects.get(id=id)
        student.delete()

        return JsonResponse({"message": "Deleted Successfully"})