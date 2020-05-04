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

    def perform_create(self, serializer):
        file_obj = serializer.validated_data['excel_file']
        faculty, created = Faculty.objects.update_or_create(
            name=serializer.validated_data.get('name', None),
            defaults={'excel_file': file_obj}
        )
        faculties_with_file = Faculty.objects.filter(excel_file__isnull=False)
        return faculties_with_file


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
        # user_data = get_user_data(user=user)
        user_serializer = UserSerializer(user)
        return Response({'result': 'ok', 'params': {'token': token.key, 'user': user_serializer.data}})


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
        serializer = FacultySerializer(faculties, many=True, fields=['name', 'directions_names_on_faculty'])
        data = serializer.data
        # return Response(data, status=status.HTTP_200_OK)
        return Response({'result': 'ok', 'params': {'data': serializer.data}}, status=status.HTTP_200_OK)


class CustomRegisterView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
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
            # user_data = get_user_data(user)
            user_data = UserSerializer(user).data
            token = Token.objects.create(user=user)
            return Response({'result': 'ok', 'params': {'token': token.key, 'user': user_data}}, status=status.HTTP_200_OK)


class UserInfoView(views.APIView):

    def post(self, request, format=None):
        token = request.data['token']
        user = Token.objects.get(key=token).user
        user_data = UserSerializer(user).data
        return Response({'user': user_data})


class GroupsByDirectView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, studying_direct_name):
        direction = StudyDirection.objects.get(name=studying_direct_name)
        groups_with_direction = Group.objects.filter(studying_direction=direction)
        group_numbers = []
        for group in groups_with_direction:
            group_numbers.append(group.number)
        return Response({'result': 'ok', 'params': {'groups_numbers': group_numbers}})


class TableCreatorView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, table_id):
        table = Table.objects.get(id=table_id)
        table_data = TableSerializer(table, fields=['students_w_grades_in_table']).data
        return Response({'result': 'ok', 'params': {'table_data': table_data}})

    def post(self, request, format=None):
        user = request.user
        if request.data['action'] == 'get_directions':
            teacher = Teacher.objects.get(user=user)
            teacher_directs = StudyDirection.objects.filter(teacher=teacher)
            serializer = StudyDirectionSerializer(teacher_directs, many=True, fields=['name'])
            return Response({'result': 'ok', 'params': {'directions_names': serializer.data}})

        if request.data['action'] == 'create_new':
            table_group_number = request.data['params']['group_number']
            table_name = request.data['params']['new_table_name']
            table_author = Teacher.objects.get(user=user)
            table_group = Group.objects.get(number=table_group_number)
            new_table = Table.objects.create(table_name=table_name, table_group=table_group, table_teacher=table_author)
            new_table.save()
            students_in_table = table_group.students_in_group()
            for student in students_in_table:
                final_grade = Grade.objects.create(grade_student=student, grade_table=new_table, grade_type='fin',
                                                   grade_value=None)
            # serializer = StudentSerializer(students_in_table, many=True)
            # return Response({'result': 'ok',
            #                  'params': {'students': serializer.data}})
            table_data = TableSerializer(new_table, fields=['students_w_grades_in_table'])
            # grades_in_table = new_table.grade_set.all()

            return Response({'result': 'ok', 'params': {'table_data': table_data}})

        if request.data['action'] == 'get_all':
            table_author = Teacher.objects.get(user=user)
            all_author_tables = Table.objects.filter(table_teacher=table_author)
            serializer = TableSerializer(all_author_tables, many=True, fields=['id', 'table_name', 'table_group'])
            return Response({'result': 'ok', 'params': {'all_author_tables': serializer.data} })

        if request.data['action'] == 'delete_table':
            table_id = request.data['params']['table_id']
            try:
                table = Table.objects.get(id=table_id)
            except:
                return Response({'result': 'error', 'params': {'message': 'Could not identify table'}})
            table.delete()
            return Response({'result': 'ok'})
