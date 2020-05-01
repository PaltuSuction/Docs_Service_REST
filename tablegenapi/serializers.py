from rest_auth.registration.views import RegisterView
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_auth.registration.serializers import RegisterSerializer

from Docs_Service_REST_v2 import settings
from tablegenapi.UserModel import User
from tablegenapi.models import Student, Teacher, Group, StudyDirection, Faculty, Discipline


class StudentSerializer(serializers.ModelSerializer):
    group_number = serializers.CharField(max_length=4)
    ticket_number = serializers.CharField(max_length=6)
    class Meta:
        model = Student
        fields = ('ticket_number', 'group_number', 'first_name', 'middle_name', 'last_name')


class GroupSerializer(serializers.ModelSerializer):
    students_in_group = StudentSerializer('students_in_group', many=True, read_only=True)

    class Meta:
        model = Group
        fields = ('number', 'headman', 'students_in_group', 'studying_direction')


class StudyDirectionSerializer(serializers.ModelSerializer):

    class Meta:
        model = StudyDirection
        fields = ('name', 'faculty', 'all_groups_on_studying_direction', 'all_teachers_on_studying_direction')


class FacultySerializer(serializers.ModelSerializer):

    class Meta:
        model = Faculty
        name = serializers.CharField(source='get_name_display')
        fields = ('name', 'study_directions_in_faculty', 'excel_file')
        # fields = ('name', 'study_directions_in_faculty')

    '''def create(self, validated_data):
        faculty, created = Faculty.objects.update_or_create(
            name=validated_data.get('name', None),
            defaults={'excel_file': validated_data.get('file', None)}
        )
        return faculty'''


class TeacherSerializer(serializers.ModelSerializer):
    studying_directions = StudyDirectionSerializer(many=True)

    class Meta:
        model = Teacher
        fields = ('studying_directions', 'first_name', 'middle_name', 'last_name')


class DisciplineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'middle_name', 'last_name', 'is_teacher', 'is_student', 'password')
        extra_kwargs = {'password': {'required': True, 'write_only': True}}

    '''def create(self, validated_data):
        user = User.objects.create(**validated_data)
        if validated_data['is_teacher']:
            studying_directions_names = validated_data['studying_directions']
            studying_directions = StudyDirection.objects.filter(name__in=studying_directions_names)
            Teacher.objects.create(user=user, studying_directions=studying_directions)
        Token.objects.create(user=user)
        return user'''


'''class CustomRegisterSerializer(RegisterSerializer):
    user_ident = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    middle_name = serializers.CharField(required=True)
    studying_directions = StudyDirectionSerializer(many=True)
    is_staff = serializers.BooleanField(default=False)
    is_teacher = serializers.BooleanField(default=False)
    is_student = serializers.BooleanField(default=False)

    def get_cleaned_data(self):
        super(CustomRegisterSerializer, self).get_cleaned_data()

        return {
            'password': self.validated_data.get('password', ''),
            'username': self.validated_data.get('user_ident', ''),
            'last_name': self.validated_data('last_name', ''),
            'first_name': self.validated_data('first_name', ''),
            'middle_name': self.validated_data('middle_name', ''),
            'is_staff': self.validated_data('is_staff', ''),
            'is_teacher': self.validated_data('is_teacher', ''),
            'is_student': self.validated_data('is_student', ''),
            'studying_directions': self.validated_data('studying_directions', ''),
        }


class CustomUserDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username', 'last_name', 'first_name', 'middle_name', 'is_teacher', 'is_student',)
        read_only_fields = ('email',)'''

