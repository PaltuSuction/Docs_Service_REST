from rest_framework import viewsets, status, views
# Create your views here.
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from rest_framework.authtoken.views import ObtainAuthToken

from Docs_Service_REST_v2.ExcelParser import ExcelParser
from tablegenapi.serializers import *


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        response = {'message': 'Нельзя удалять студентов таким способом'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = (IsAuthenticated,)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated,)


class StudyDirectionViewSet(viewsets.ModelViewSet):
    queryset = StudyDirection.objects.all()
    serializer_class = StudyDirectionSerializer
    permission_classes = (AllowAny,)


class FacultyViewSet(viewsets.ModelViewSet):
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser)

    ''' def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = FacultySerializer(queryset, many=True)
        return Response(serializer.data)'''

    def perform_create(self, serializer):
        file_obj = serializer.validated_data['excel_file']
        faculty, created = Faculty.objects.update_or_create(
            name=serializer.validated_data.get('name', None),
            defaults={'excel_file': file_obj}
        )
        faculties_with_file = Faculty.objects.filter(excel_file__isnull=False)
        return faculties_with_file


class DisciplineViewSet(viewsets.ModelViewSet):
    queryset = Discipline.objects.all()
    serializer_class = DisciplineSerializer
    permission_classes = (IsAuthenticated,)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


class CustomObtainAuthToken(ObtainAuthToken):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response({'result': 'error', 'params': {'message': 'Incorrect data'}})
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        user_data = get_user_data(user=user)
        return Response({'result': 'ok', 'params': {'token': token.key, 'user': user_data}})


class ExcelParserView(views.APIView):
    permission_classes = [AllowAny, ]

    def post(self, request, format=None):
        excelparser = ExcelParser()
        excelparser.parse_excel_file(request.data['faculty_name'])
        return Response({'message': 'success'})


class FacultsAndDirectsView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        faculties = Faculty.objects.all()
        serializer = FacultySerializer(faculties, many=True)
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)


class CustomRegisterView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        try:
            user = User.objects.create(username=request.data['username'],
                                       first_name=request.data['first_name'],
                                       last_name=request.data['last_name'],
                                       middle_name=request.data['middle_name'],
                                       is_student=request.data['is_student'],
                                       is_teacher=request.data['is_teacher'],
                                       is_staff=request.data['is_staff'])
            user.set_password(request.data['password'])
            user.save()

            if request.data['is_teacher']:
                studying_directions_names = request.data['studying_directions']
                studying_directions = StudyDirection.objects.filter(name__in=studying_directions_names)
                teacher = Teacher.objects.create(user=user)
                teacher.save()
                for direction in studying_directions:
                    teacher.studying_directions.add(direction)
            elif request.data['is_student']:
                group = Group.objects.get(number=request.data['group_number'])
                student = Student.objects.create(ticket_number=request.data['username'], student_group=group)

            user_data = get_user_data(user)
            token = Token.objects.create(user=user)
            return Response({'result': 'ok', 'params': {'token': token.key, 'user': user_data}}, status=status.HTTP_200_OK)
        except:
            return Response({'result': 'error', 'params': {'message': 'succ'}}, status=status.HTTP_400_BAD_REQUEST)


class UserInfoView(views.APIView):

    def post(self, request, format=None):
        token = request.data['token']
        user = Token.objects.get(key=token).user
        user_serializer = UserSerializer(user)
        user_data = get_user_data(user)
        return Response({'user': user_data})


def get_user_data(user):
    user_data = {}
    user_data['username'] = user.username
    user_data['first_name'] = user.first_name
    user_data['middle_name'] = user.middle_name
    user_data['last_name'] = user.last_name
    if user.is_teacher:
        user_data['studying_directions'] = []
        user_data['is_teacher'] = True
        teacher = Teacher.objects.get(user=user)
        teacher = TeacherSerializer(teacher)
        for direction in teacher.data['studying_directions']:
            user_data['studying_directions'].append(direction['name'])
        # user_data['studying_directions'] = teacher.data.studying_directions
    if user.is_student:
        student = Student.objects.get(user=user)
        student = StudentSerializer(student)
        user_data['student_group'] = student.data['group_number']
        user_data['ticket_number'] = student.data['ticket_number']
        user_data['is_student'] = True
    return user_data


class GroupsByDirectView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, studying_direct_name):
        direction = StudyDirection.objects.get(name=studying_direct_name)
        # groups_with_direction = StudyDirection.all_groups_on_studying_direction(direction)
        # serializer = GroupSerializer(groups_with_direction, many=True)
        groups_with_direction = Group.objects.filter(studying_direction=direction)
        serializer = GroupSerializer(groups_with_direction, many=True)
        return Response(serializer.data)


class TableCreatorView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        pass

    def post(self, request, format=None):
        if request.data['action'] == 'create_new':
            group_number = request.data['group_number']
            group = Group.objects.get(number=group_number)
            students_in = group.students_in_group()
            serializer = StudentSerializer(students_in, many=True)
            return Response({'result': 'ok', 'params': {'students': serializer.data}})


