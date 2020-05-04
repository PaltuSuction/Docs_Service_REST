from rest_auth.registration.views import RegisterView
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from Docs_Service_REST_v2 import settings
from tablegenapi.UserModel import User
from tablegenapi.models import Student, Teacher, Group, StudyDirection, Faculty, Table, Grade


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        exclude = kwargs.pop('exclude', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        if exclude is not None:
            not_allowed = set(exclude)
            for exclude_name in not_allowed:
                self.fields.pop(exclude_name)


class StudentSerializer(serializers.ModelSerializer):
    group_number = serializers.CharField(max_length=4)
    ticket_number = serializers.CharField(max_length=6)

    class Meta:
        model = Student
        fields = ('ticket_number', 'group_number', 'first_name', 'middle_name', 'last_name')


class TeacherSerializer(DynamicFieldsModelSerializer):
    # studying_directions = StudyDirectionSerializer(many=True)

    class Meta:
        model = Teacher
        fields = ('id', 'first_name', 'middle_name', 'last_name', 'directions_names')


class GroupSerializer(DynamicFieldsModelSerializer):
    students_in_group = StudentSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ('id', 'number', 'headman', 'students_in_group')


class StudyDirectionSerializer(DynamicFieldsModelSerializer):
    groups_on_direction = GroupSerializer(many=True)
    teachers_on_direction = TeacherSerializer(many=True)

    class Meta:
        model = StudyDirection
        fields = ('id', 'name', 'faculty', 'groups_numbers_on_direction', 'teachers_names_on_direction',
                  'groups_on_direction', 'teachers_on_direction')


class FacultySerializer(DynamicFieldsModelSerializer):
    directions_on_faculty = StudyDirectionSerializer(many=True)

    class Meta:
        model = Faculty
        fields = ('id', 'name', 'directions_names_on_faculty', 'directions_on_faculty', 'excel_file')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'middle_name', 'last_name', 'is_teacher', 'is_student', 'password')
        extra_kwargs = {'password': {'required': True, 'write_only': True}}


class GradeSerializer(DynamicFieldsModelSerializer):
    grade_student = StudentSerializer()
    # grade_table = TableSerializer()

    class Meta:
        model = Grade
        fields = ('id', 'grade_student', 'grade_table', 'grade_type', 'grade_value')


class CustomTableGradesSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    fio = serializers.CharField(max_length=300)
    grades = GradeSerializer(many=True, fields=['grade_type', 'grade_value'])


class TableSerializer(DynamicFieldsModelSerializer):
    table_group = GroupSerializer()
    table_teacher = TeacherSerializer(fields=['first_name', 'middle_name', 'last_name'])
    # table_teacher = TeacherSerializer(fields=['first_name', 'middle_name', 'last_name'])
    students_w_grades_in_table = CustomTableGradesSerializer(many=True)

    class Meta:
        model = Table
        fields = ('id', 'table_name', 'table_group', 'table_teacher', 'students_w_grades_in_table')

