from django.db import models

# Create your models here.
from django.db.models import Count
from django.utils import timezone

from Docs_Service_REST_v2 import settings
from tablegenapi.UserModel import User


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    student_group = models.ForeignKey('Group', on_delete=models.SET_NULL, verbose_name='Группа', null=True)
    ticket_number = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'
        ordering = ['user__last_name']

    def group_number(self):
        group_number = self.student_group.number
        return group_number

    def first_name(self):
        return self.user.first_name

    def middle_name(self):
        return self.user.middle_name

    def last_name(self):
        return self.user.last_name


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    studying_directions = models.ManyToManyField('StudyDirection', verbose_name='Направления подготовки',
                                                 help_text='Направления подготовки', blank=True)

    class Meta:
        verbose_name = 'Преподаватель'
        verbose_name_plural = 'Преподаватели'
        abstract = False

    def first_name(self):
        return self.user.first_name

    def middle_name(self):
        return self.user.middle_name

    def last_name(self):
        return self.user.last_name

    def directions_names(self):
        names = []
        directions = StudyDirection.objects.filter(teacher=self)
        for direction in directions:
            names.append(direction.name)
        return names


class Group(models.Model):
    number = models.CharField(max_length=4, verbose_name='Номер группы', help_text='Введите номер группы', unique=True)
    headman = models.OneToOneField('Student', verbose_name='Староста', help_text='Староста группы',
                                   null=True, blank=True, on_delete=models.SET_NULL)
    studying_direction = models.ForeignKey('StudyDirection', null=True, blank=True, on_delete=models.SET_NULL)
    studying_start_year = models.CharField(max_length=4, verbose_name='Год начала обучения', null=True)

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['number']

    def __str__(self):
        return 'Группа: {}'.format(self.number)

    def students_in_group(self):
        students = Student.objects.filter(student_group=self)
        return students

    def group_all_students_ids(self):
        group_students_ids = []
        students = Student.objects.filter(student_group=self)
        for student in students:
            group_students_ids.append(student.id)
        return group_students_ids


class StudyDirection(models.Model):
    name = models.CharField(max_length=300, verbose_name='Название направления', help_text='Название направления',
                            unique=True)
    faculty = models.ForeignKey('Faculty', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Направление подготовки'
        verbose_name_plural = 'Направления подготовки'
        ordering = ['name']

    def __str__(self):
        return 'Кафедра: {}'.format(self.name)

    def groups_numbers_on_direction(self):
        groups = Group.objects.filter(studying_direction=self)
        groups_list = []
        for group in groups:
            groups_list.append(group.number)
        return groups_list

    def teachers_names_on_direction(self):
        teachers = Teacher.objects.filter(studying_directions__in=[self])
        teachers_list = []
        for teacher in teachers:
            teachers_list.append({'first_name': teacher.first_name,
                                  'middle_name': teacher.middle_name,
                                  'last_name': teacher.last_name})
        return teachers_list

    def groups_on_direction(self):
        groups = Group.objects.filter(studying_direction=self)
        return groups

    def teachers_on_direction(self):
        teachers = Teacher.objects.filter(studying_directions__in=[self])
        return teachers


class Faculty(models.Model):
    name = models.CharField(max_length=300, verbose_name='Факультет', help_text='Факультет')
    excel_file = models.FileField(upload_to='files/faculties', blank=True, null=True, verbose_name='Файл - список студентов')

    class Meta:
        verbose_name = 'Факультет'
        verbose_name_plural = 'Факультеты'

    def __str__(self):
        return 'Факультет: {}'.format(self.name)

    def directions_names_on_faculty(self):
        study_directions = StudyDirection.objects.filter(faculty=self)
        directions_list = []
        for direction in study_directions:
            directions_list.append({'name': direction.name})
        return directions_list

    def directions_on_faculty(self):
        study_directions = StudyDirection.objects.filter(faculty=self)
        return study_directions


class Table(models.Model):
    table_name = models.CharField(max_length=300, verbose_name='Название таблицы', help_text='Название таблицы', default='Без названия')
    table_group = models.ForeignKey('Group', on_delete=models.CASCADE, verbose_name='Группа для таблицы')
    # table_discipline = models.ForeignKey('Discipline', on_delete=models.CASCADE, verbose_name='Дисциплина для таблицы',
    #                                      null=True)
    table_teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, verbose_name='Создатель таблицы')
    table_created_at = models.DateTimeField(editable=False)
    table_updated_at = models.DateTimeField()

    class Meta:
        verbose_name = 'Таблица для группы'
        verbose_name_plural = 'Таблицы'

    def __str__(self):
        return 'Таблица группы {}, {}'.format(self.table_group.number, self.table_name)

    def save(self, *args, **kwargs):
        if not self.id:
            self.table_created_at = timezone.now()
        self.table_updated_at = timezone.now()
        return super(Table, self).save(*args, **kwargs)

    def table_group_number(self):
        return self.table_group.number

    def table_direction(self):
        return self.table_group.studying_direction.name

    def students_and_grades(self):
        data = []
        students_in_table = self.table_group.students_in_group()
        grades_types = self.grades_types()
        for student in students_in_table:
            student_grades_data = {}
            student_grades = self.grade_set.filter(grade_student=student, grade_table=self)
            for grade_type in grades_types:
                student_grades_data[grade_type] = []
                for grade in student_grades:
                    if grade_type == grade.grade_type:
                        student_grades_data[grade_type].append({'id': grade.id, 'grade_value': grade.grade_value})

            data.append({'id': student.id,
                         'fio': student.user.last_name + ' ' + student.user.first_name + ' ' + student.user.middle_name,
                         'grades': student_grades_data})
        return data

    def grades_types(self):
        grades_in_table = self.grade_set
        grades_types = grades_in_table.values('grade_type').order_by('grade_type').annotate(Count('grade_type'))
        students_num_in_group = self.table_group.student_set.count()
        for type in grades_types:
            type['grade_type__count'] = type['grade_type__count'] / students_num_in_group

        grades_types_dict = {type['grade_type'] : int(type['grade_type__count']) for type in grades_types}
        grades_types_dict = dict(sorted(grades_types_dict.items()))
        return grades_types_dict


class Grade(models.Model):
    '''
    grade_type:
    test, idz, lab, report, ref, own, fin
    '''
    grade_student = models.ForeignKey('Student', on_delete=models.CASCADE, verbose_name='Студент с оценкой')
    grade_table = models.ForeignKey('Table', on_delete=models.CASCADE, verbose_name='Таблица для оценки')
    grade_type = models.CharField(max_length=100, verbose_name='Тип оценки', help_text='Укажите тип оценки',
                                  default='test')
     # grade_type_order = models.IntegerField(verbose_name='Число для определения порядка сортировки', null=True)
    grade_value = models.CharField(max_length=20, verbose_name='Значение оценки', help_text='Укажите значение оценки', null=True)

    class Meta:
        verbose_name = 'Оценка студента'
        verbose_name_plural = 'Оценки студента'
        ordering = ['grade_type', 'id']

    '''def save(self, *args, **kwargs):
        if not self.id:
            order_id = 0
            if self.grade_type == 'Итог':
                self.grade_type_order = 999999999
            else:
                for chr in self.grade_type:
                    order_id += ord(chr)
                self.grade_type_order = order_id
        return super(Grade, self).save(*args, **kwargs)'''
