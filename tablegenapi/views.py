import os

from rest_framework import viewsets, status, views
# Create your views here.
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from rest_framework.authtoken.views import ObtainAuthToken

from Docs_Service_REST_v2.DocumentHandler import DocumentHandler
from tablegenapi.serializers import *

from rest_framework import generics
from django.http import HttpResponse
from wsgiref.util import FileWrapper


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

    def list(self, request, *args, **kwargs):
        try:
            all_faculties = Faculty.objects.all()
            faculty_serializer = FacultySerializer(all_faculties, many=True, fields=['name', 'excel_file'])
            return Response({'result': 'ok', 'params': {'faculties': faculty_serializer.data}})
        except:
            return Response({'result': 'error', 'params': {'message': 'Faculty list creation error'}})

    def perform_create(self, serializer):
        docs_handler = DocumentHandler()
        file_obj = serializer.validated_data['excel_file']
        file_obj.name = serializer.validated_data['name'] + '.xlsx'
        try:
            os.remove(docs_handler.find_path('faculties/' + file_obj.name, ''))
        except:
            pass
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
        serializer = AuthCustomTokenSerializer(data=request.data,
                                               context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            print(e)
            return Response({'result': 'error', 'params': {'message': 'Incorrect data'}})
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        user_serializer = UserSerializer(user)
        return Response({'result': 'ok', 'params': {'token': token.key, 'user': user_serializer.data}})


class ExcelParserView(views.APIView):
    permission_classes = [AllowAny, ]

    def post(self, request, format=None):
        docs_handler = DocumentHandler()
        docs_handler.parse_excel_file(request.data['faculty_name'])
        return Response({'message': 'success'})


class FacultsAndDirectsView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        faculties = Faculty.objects.all()
        serializer = FacultySerializer(faculties, many=True, fields=['name', 'directions_names_on_faculty'])
        return Response({'result': 'ok', 'params': {'data': serializer.data}}, status=status.HTTP_200_OK)


class CustomRegisterView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        user = User.objects.create(email=request.data['email'],
                                   # first_name=request.data['first_name'],
                                   # last_name=request.data['last_name'],
                                   # middle_name=request.data['middle_name'],
                                   is_student=request.data['is_student'],
                                   is_teacher=request.data['is_teacher'],
                                   is_staff=request.data['is_staff'])
        user.set_password(request.data['password'])

        if request.data['is_teacher']:
            studying_directions_names = request.data['studying_directions']
            studying_directions = StudyDirection.objects.filter(name__in=studying_directions_names)
            user.save()
            teacher = Teacher.objects.create(user=user,
                                             first_name=request.data['first_name'],
                                             last_name=request.data['last_name'],
                                             middle_name=request.data['middle_name'],
                                             departments=[])
            teacher.save()
            for direction in studying_directions:
                teacher.studying_directions.add(direction)

        elif request.data['is_student']:
            # Студент уже создан - осталось привязать к нему нового пользователя
            ticket_number = request.data['ticket_number']
            try:
                student = Student.objects.get(ticket_number=ticket_number,
                                              first_name=request.data['first_name'],
                                              last_name=request.data['last_name'],
                                              middle_name=request.data['middle_name'])
                user.save()
                student.user = user
                student.save()
            except:
                return Response({'result': 'error', 'params': {'message': 'Нет студента с такими данными'}})

        user_data = UserSerializer(user).data
        token = Token.objects.create(user=user)
        return Response({'result': 'ok', 'params': {'token': token.key, 'user': user_data}})


class UserInfoView(views.APIView):

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            old_password = serializer.data.get("old_password")
            new_password = serializer.data.get('new_password')
            new_password_2 = serializer.data.get('new_password_2')
            if not old_password or not new_password or not new_password_2:
                return Response({'result': 'error', 'params': {'message': 'Не все поля заполнены'}})
            if not user.check_password(old_password):
                return Response({'result': 'error', 'params': {'message': 'Старый пароль указан неверно'}})
            if not (new_password == new_password_2):
                return Response({'result': 'ok', 'params': {'message': 'Пароли не совпадают'}})
            user.set_password(serializer.data.get("new_password"))
            user.save()
            return Response({'result': 'ok'})
        return Response({'result': 'error', 'params': {'message': serializer.errors}})

    def post(self, request, format=None):
        try:
            user = request.user
        except:
            return Response({'result': 'error', 'params': {'message': 'User with this token does not exist'}})

        if request.data['action'] == 'fetch_user_data':
            user_data = UserSerializer(user).data
            return Response({'result': 'ok', 'params': {'user': user_data}})

        if request.data['action'] == 'get_info_for_edit':
            if user.is_student:
                student = user.student
                group_number = student.group_number()
                return Response({'result': 'ok', 'params': {'status': 'student', 'group_number': group_number}})
            if user.is_teacher:
                teacher = user.teacher
                teacher_departments = teacher.departments
                all_faculties_data = FacultySerializer(Faculty.objects.all(), many=True,
                                                       fields=['id', 'name', 'directions_names_on_faculty']).data
                return Response({'result': 'ok', 'params': {'status': 'teacher',
                                                            'teacher_departments': teacher_departments,
                                                            'all_faculties': all_faculties_data}})

        if request.data['action'] == 'add_department':
            teacher = user.teacher
            department_to_add = request.data['params']['department_name']
            if department_to_add not in teacher.departments:
                teacher.departments.append(department_to_add)
            teacher.save()
            return Response({'result': 'ok', 'params': {'teacher_departments': teacher.departments}})

        if request.data['action'] == 'delete_department':
            teacher = user.teacher
            department_to_delete = request.data['params']['department_name']
            if department_to_delete in teacher.departments:
                teacher.departments.remove(department_to_delete)
            teacher.save()
            return Response({'result': 'ok', 'params': {'teacher_departments': teacher.departments}})

        if request.data['action'] == 'update_profile':
            teacher = user.teacher
            update_type = request.data['params']['type']
            teacher.studying_directions.clear()
            if update_type == 'change_faculty':
                faculty_name = request.data['params']['faculty_name']
                new_directions = StudyDirection.objects.filter(faculty__name=faculty_name)
            if update_type == 'change_directions':
                studying_directions = request.data['params']['directions_names']
                directions_names = [direction['name'] for direction in studying_directions]
                new_directions = StudyDirection.objects.filter(name__in=directions_names)
            for direction in new_directions:
                teacher.studying_directions.add(direction)
            teacher.save()
            return Response({'result': 'ok'})


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
        table_data = TableSerializer(table, fields=['id', 'students_and_grades', 'grades_types']).data
        return Response({'result': 'ok', 'params': {'table_data': table_data}})

    def post(self, request, format=None):
        user = request.user
        if request.data['action'] == 'get_directs_and_departments':
            try:
                teacher = Teacher.objects.get(user=user)
            except:
                Response({'result': 'error', 'params': {'message': 'Ошибка авторизации'}})
            try:
                teacher_directs = StudyDirection.objects.filter(teacher=teacher)
            except:
                Response({'result': 'error', 'params': {'message': 'Не указаны направления подготовки'}})
            serializer = StudyDirectionSerializer(teacher_directs, many=True, fields=['name'])
            all_group_numbers = [group.number for group in Group.objects.all()]
            return Response(
                {'result': 'ok', 'params': {'directions_names': serializer.data, 'all_group_numbers': all_group_numbers,
                                            'teacher_departments': teacher.departments}})

        if request.data['action'] == 'create_new':
            table_group_number = request.data['params']['group_number']
            table_name = request.data['params']['new_table_name']
            table_department = request.data['params']['table_department']
            table_author = user.teacher
            table_group = Group.objects.get(number=table_group_number)
            new_table = Table.objects.create(table_name=table_name, table_group=table_group, table_teacher=table_author,
                                             table_department=table_department)
            if table_department not in table_author.departments:
                table_author.departments.append(table_department)
            table_author.save()
            new_table.save()
            students_in_table = table_group.students_in_group()
            for student in students_in_table:
                final_grade = Grade.objects.create(grade_student=student, grade_table=new_table,
                                                   grade_type='\u05C4Итог',
                                                   grade_value=None)
            table_data = TableSerializer(new_table, fields=['id', 'students_and_grades', 'grades_types']).data
            return Response({'result': 'ok', 'params': {'table_data': table_data}})

        if request.data['action'] == 'get_all':
            table_author = user.teacher
            all_author_tables = Table.objects.filter(table_teacher=table_author)
            serializer = TableSerializer(all_author_tables, many=True, fields=['id', 'table_name', 'table_direction',
                                                                               'table_group_number', 'table_created_at',
                                                                               'table_updated_at', 'table_department'])
            return Response({'result': 'ok', 'params': {'all_author_tables': serializer.data}})

        if request.data['action'] == 'delete_table':
            table_id = request.data['params']['table_id']
            try:
                table = Table.objects.get(id=table_id)
            except:
                return Response({'result': 'error', 'params': {'message': 'Could not identify table'}})
            table.delete()
            return Response({'result': 'ok'})

        if request.data['action'] == 'add_column':
            table_id = request.data['params']['table_id']
            if not table_id: return Response({'result': 'error', 'params': {'message': 'No ID'}})
            new_column_type = request.data['params']['column_type']
            if not new_column_type: return Response({'result': 'error', 'params': {'message': 'No column type'}})
            table = Table.objects.get(id=table_id)
            if not table: return Response({'result': 'error', 'params': {'message': 'No table with such ID'}})
            students_in_table = table.table_group.students_in_group()
            new_grades = {}
            for student in students_in_table:
                new_grade = Grade.objects.create(grade_student=student, grade_table=table, grade_type=new_column_type,
                                                 grade_value=None)
                new_grades[student.id] = {'id': new_grade.id, 'grade_value': new_grade.grade_value}
            table.save()  # Обновить дату обновления таблицы
            return Response({'result': 'ok', 'params': {'new_grades': new_grades}})

        if request.data['action'] == 'delete_column':
            table_id = request.data['params']['table_id']
            if not table_id: return Response({'result': 'error', 'params': {'message': 'No ID'}})
            grades_ids = request.data['params']['grades_ids']
            if not grades_ids: return Response({'result': 'error', 'params': {'message': 'No grades IDs'}})
            table = Table.objects.get(id=table_id)
            grades_in_table = table.grade_set
            grades_to_delete = grades_in_table.filter(id__in=grades_ids)
            for grade in grades_to_delete:
                grade.delete()
            table.save()  # Обновить дату обновления таблицы
            return Response({'result': 'ok'})

        if request.data['action'] == 'save_table':
            table_id = request.data['params']['table_id']
            grades_to_save = request.data['params']['all_grades']
            if not table_id: return Response({'result': 'error', 'params': {'message': 'No ID'}})
            table = Table.objects.get(id=table_id)
            grades_in_table = Grade.objects.filter(grade_table=table)
            for grade in grades_in_table:
                try:
                    grade.grade_value = grades_to_save[str(grade.id)]
                except KeyError:
                    grade.delete()
                grade.save()
            table.save()  # Обновить дату обновления таблицы
            return Response({'result': 'ok'})

        if request.data['action'] == 'create_document':
            table_id = request.data['params']['table_id']
            if not table_id: return Response({'result': 'error', 'params': {'message': 'No ID'}})
            docs_handler = DocumentHandler()
            new_document_name = docs_handler.generate_excel_document(table_id)
            document = open(docs_handler.find_path('generated_docs/' + new_document_name, '.xls'), 'rb')
            response = HttpResponse(FileWrapper(document), content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename="{}.xls"'.format(new_document_name)
            return response


class TableViewerView(views.APIView):

    def post(self, request, *args, **kwargs):
        user = request.user
        if request.data['action'] == 'get_all_group_tables':
            student_group = user.student.student_group
            all_group_tables = Table.objects.filter(table_group=student_group)
            serializer = TableSerializer(all_group_tables, many=True, fields=['id', 'table_name', 'table_teacher',
                                                                              'table_updated_at'])
            return Response(
                {'result': 'ok', 'params': {'group_number': student_group.number, 'all_group_tables': serializer.data}})

        if request.data['action'] == 'get_group_table_instance':
            table_id = request.data['params']['table_id']
            table = Table.objects.get(id=table_id)
            table_data = TableSerializer(table, fields=['id', 'table_name', 'students_and_grades', 'grades_types']).data
            return Response({'result': 'ok', 'params': {'table_data': table_data}})
