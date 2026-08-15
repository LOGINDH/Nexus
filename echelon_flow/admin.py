from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.formats.base_formats import Format
from import_export.formats.base_formats import DEFAULT_FORMATS
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from xml.etree import ElementTree as ET

from .models import User, Project, Task


# ============================================================
# XML FORMAT
# ============================================================

class XMLFormat(Format):

    CONTENT_TYPE = "application/xml"
    FILE_EXTENSION = "xml"
    CAN_EXPORT = True
    CAN_IMPORT = True

    def get_title(self):
        return "XML"

    def create_dataset(self, in_stream, **kwargs):
        """
        Convert XML file into a Tablib Dataset.
        """

        import tablib

        if hasattr(in_stream, "read"):
            data = in_stream.read()
        else:
            data = in_stream

        if isinstance(data, bytes):
            data = data.decode("utf-8")

        root = ET.fromstring(data)

        dataset = tablib.Dataset()

        items = list(root)

        if not items:
            return dataset

        fields = [
            child.tag
            for child in items[0]
        ]

        dataset.headers = fields

        for item in items:

            row = []

            for field in fields:

                element = item.find(field)

                row.append(
                    element.text
                    if element is not None
                    else ""
                )

            dataset.append(row)

        return dataset

    def export_data(self, dataset, **kwargs):
        """
        Convert Tablib Dataset into XML.
        """

        root = ET.Element("data")

        for row in dataset.dict:

            item = ET.SubElement(
                root,
                "item"
            )

            for key, value in row.items():

                element = ET.SubElement(
                    item,
                    str(key)
                )

                element.text = (
                    ""
                    if value is None
                    else str(value)
                )

        return ET.tostring(
            root,
            encoding="utf-8",
            xml_declaration=True
        )


# ============================================================
# COMMON FORMAT LIST
# ============================================================

FORMATS = [
    XMLFormat,
    *DEFAULT_FORMATS,
]


# ============================================================
# USER RESOURCE
# ============================================================

class UserResource(resources.ModelResource):

    created_by = Field(
        column_name="created_by",
        attribute="created_by",
        widget=ForeignKeyWidget(
            User,
            "username"
        )
    )

    class Meta:
        model = User

        fields = (
            "id",
            "username",
            "password",
            "full_name",
            "role",
            "created_by",
            "is_active",
        )

        import_id_fields = (
            "id",
        )


# ============================================================
# PROJECT RESOURCE
# ============================================================

class ProjectResource(resources.ModelResource):

    assigned_to_tl = Field(
        column_name="assigned_to_tl",
        attribute="assigned_to_tl",
        widget=ForeignKeyWidget(
            User,
            "username"
        )
    )

    created_by = Field(
        column_name="created_by",
        attribute="created_by",
        widget=ForeignKeyWidget(
            User,
            "username"
        )
    )

    class Meta:
        model = Project

        fields = (
            "id",
            "name",
            "description",
            "assigned_to_tl",
            "created_by",
            "start_date",
            "end_date",
            "status",
        )

        import_id_fields = (
            "id",
        )


# ============================================================
# TASK RESOURCE
# ============================================================

class TaskResource(resources.ModelResource):

    project = Field(
        column_name="project",
        attribute="project",
        widget=ForeignKeyWidget(
            Project,
            "name"
        )
    )

    assigned_to_employee = Field(
        column_name="assigned_to_employee",
        attribute="assigned_to_employee",
        widget=ForeignKeyWidget(
            User,
            "username"
        )
    )

    assigned_by = Field(
        column_name="assigned_by",
        attribute="assigned_by",
        widget=ForeignKeyWidget(
            User,
            "username"
        )
    )

    class Meta:
        model = Task

        fields = (
            "id",
            "title",
            "project",
            "assigned_to_employee",
            "assigned_by",
            "start_date",
            "end_date",
            "status",
        )

        import_id_fields = (
            "id",
        )


# ============================================================
# USER ADMIN
# ============================================================

@admin.register(User)
class UserAdmin(ImportExportModelAdmin):

    resource_class = UserResource

    formats = FORMATS

    list_display = (
        "id",
        "username",
        "full_name",
        "role",
        "created_by",
        "is_active",
        "created_at",
    )

    list_filter = (
        "role",
        "is_active",
    )

    search_fields = (
        "username",
        "full_name",
    )

    ordering = (
        "-created_at",
    )


# ============================================================
# PROJECT ADMIN
# ============================================================

@admin.register(Project)
class ProjectAdmin(ImportExportModelAdmin):

    resource_class = ProjectResource

    formats = FORMATS

    list_display = (
        "id",
        "name",
        "assigned_to_tl",
        "created_by",
        "start_date",
        "end_date",
        "status",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "name",
        "description",
        "assigned_to_tl__username",
    )

    ordering = (
        "-created_at",
    )


# ============================================================
# TASK ADMIN
# ============================================================

@admin.register(Task)
class TaskAdmin(ImportExportModelAdmin):

    resource_class = TaskResource

    formats = FORMATS

    list_display = (
        "id",
        "title",
        "project",
        "assigned_to_employee",
        "assigned_by",
        "start_date",
        "end_date",
        "status",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "title",
        "project__name",
        "assigned_to_employee__username",
    )

    ordering = (
        "-created_at",
    )