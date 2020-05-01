from django.db import models

# Create your models here.
from Docs_Service_REST_v2 import settings
from tablegenapi.UserModel import User


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    student_group = models.ForeignKey('Group', on_delete=models.CASCADE, verbose_name='Группа')
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
    studying_directions = models.ManyToManyField('StudyDirection', verbose_name='Направления подготовки', help_text='Направления подготовки', blank=True)

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


class Group(models.Model):
    number = models.CharField(max_length=4, verbose_name='Номер группы', help_text='Введите номер группы', unique=True)
    headman = models.OneToOneField('Student', verbose_name='Староста', help_text='Староста группы',
                                   null=True, blank=True, on_delete=models.SET_NULL)
    studying_direction = models.ForeignKey('StudyDirection', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['number']


    def __str__(self):
        return 'Группа: {}'.format(self.number)

    def students_in_group(self):
        students = Student.objects.filter(student_group=self)
        return students


class StudyDirection(models.Model):
    '''APP_MATH_AND_COM_SCI = '01.03.02'
    COM_SCI_AND_ENG = '09.03.01'
    INF_SYS_AND_TECH = '09.03.02'
    SOFTWARE_ENG = '09.03.04'
    RADIO_ENG = '11.03.01'
    INFOCOM_TECH_AND_COM_SYS = '11.03.02'
    DES_AND_TECH_OF_ELEC_TOOLS = '11.03.03'
    ELEC_AND_NANOELEC = '11.03.04'
    INST_MAKING_INF = '12.03.01'
    BIOTECH_SYS_AND_TECH = '12.03.04'
    ELEC_AND_ELEC_ENG = '13.03.02'
    TECHNOSPHERE_SAFETY = '20.03.01'
    QUALITY_MANAGEMENT = '27.03.02'
    SYS_ANAL_AND_MANAGEMENT = '27.03.03'
    MANAG_IN_TECH_SYS = '27.03.04'
    INNOVATION = '27.03.05'
    NANOTECH_AND_MICROSYS_TECH = '28.03.01'
    AD_AND_PUB_RELATIONS = '42.03.01'
    LINGUISTICS = '45.03.02'

    COM_SCI_AND_ENG_M = '09.04.01'
    INF_SYS_AND_TECH_M = '09.04.02'
    SOFTWARE_ENG_M = '09.04.04'
    APP_MATH_AND_COM_SCI_M = '01.04.02'
    SYS_ANAL_AND_MANAGEMENT_M = '27.04.03'
    MANAG_IN_TECH_SYS_M = '27.04.04'

    STUDYING_DIRECTIONS_UNDERGRADUATE = (
        (APP_MATH_AND_COM_SCI, 'Прикладная математика и информатика'),
        (COM_SCI_AND_ENG, 'Информатика и вычислительная техника'),
        (INF_SYS_AND_TECH, 'Информационные системы и технологии'),
        (SOFTWARE_ENG, 'Программная инженерия'),
        (RADIO_ENG, 'Радиотехника'),
        (INFOCOM_TECH_AND_COM_SYS, 'Инфокоммуникационные технологии и системы связи'),
        (DES_AND_TECH_OF_ELEC_TOOLS, 'Конструирование и технология электронных средств'),
        (ELEC_AND_NANOELEC, 'Электроника и наноэлектроника'),
        (INST_MAKING_INF, 'Приборостроение. Информационно-измерительная техника и технологии'),
        (BIOTECH_SYS_AND_TECH, 'Биотехнические системы и технологии'),
        (ELEC_AND_ELEC_ENG, 'Электроэнергетика и электротехника'),
        (TECHNOSPHERE_SAFETY, 'Техносферная безопасность'),
        (QUALITY_MANAGEMENT, 'Управление качеством'),
        (SYS_ANAL_AND_MANAGEMENT, 'Системный анализ и управление'),
        (MANAG_IN_TECH_SYS, 'Управление в технических системах'),
        (INNOVATION, 'Инноватика'),
        (NANOTECH_AND_MICROSYS_TECH, 'Нанотехнологии и микросистемная техника'),
        (AD_AND_PUB_RELATIONS, 'Реклама и связи с общественностью'),
        (LINGUISTICS, 'Лингвистика'),

        (COM_SCI_AND_ENG_M, 'Информатика и вычислительная техника (Маг)'),
        (INF_SYS_AND_TECH_M, 'Информационные системы и технологии (Маг)'),
        (SOFTWARE_ENG_M, 'Программная инженерия (Маг)'),
        (APP_MATH_AND_COM_SCI_M, 'Прикладная математика и информатика (Маг)'),
        (SYS_ANAL_AND_MANAGEMENT_M, 'Системный анализ и управление (Маг)'),
        (MANAG_IN_TECH_SYS_M, 'Управление в технических системах (Маг)')

    ) '''
    name = models.CharField(max_length=300, verbose_name='Название направления', help_text='Название направления', unique=True)
    faculty = models.ForeignKey('Faculty', null=True, blank = True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Направление подготовки'
        verbose_name_plural = 'Направления подготовки'
        ordering = ['name']

    def __str__(self):
        return 'Кафедра: {}'.format(self.name)

    def all_groups_on_studying_direction(self):
        groups = Group.objects.filter(studying_direction=self)
        groups_list = []
        for group in groups:
            groups_list.append({'number': group.number,
                                'headman': group.headman})
        return groups_list

    def all_teachers_on_studying_direction(self):
        teachers = Teacher.objects.filter(studying_directions__in=[self])
        teachers_list = []
        for teacher in teachers:
            teachers_list.append({'first_name': teacher.first_name,
                                  'middle_name': teacher.middle_name,
                                  'last_name': teacher.last_name})
        return teachers_list


class Faculty(models.Model):
    FKTI = 'FKTI'
    INPROTECH = 'INPROTECH'
    FRT = 'FRT'
    FEL = 'FEL'
    IFIO = 'IFIO'
    FEA = 'FEA'
    FIBS = 'FIBS'
    GF = 'GF'
    RY = 'RY'
    all_faculty_names = (
        (FKTI, 'ФКТИ'),
        (INPROTECH, 'ИНПРОТЕХ'),
        (FRT, 'ФРТ'),
        (FEL, 'ФЭЛ'),
        (IFIO, 'ИФИО'),
        (FEA, 'ФЭА'),
        (FIBS, 'ФИБС'),
        (GF, 'ГФ'),
        (RY, 'РЯ')
    )

    name = models.CharField(max_length=300, verbose_name='Факультет', choices=all_faculty_names, help_text='Факультет')
    excel_file = models.FileField(upload_to='files', blank=True, null=True, verbose_name='Файл - список студентов')

    class Meta:
        verbose_name = 'Факультет'
        verbose_name_plural = 'Факультеты'

    def __str__(self):
        return 'Факультет: {}'.format(self.name)

    def study_directions_in_faculty(self):
        study_directions = StudyDirection.objects.filter(faculty=self)
        directions_list = []
        for direction in study_directions:
            directions_list.append({'name': direction.name})
        return directions_list


class Discipline(models.Model):
    name = models.CharField(max_length=300, verbose_name='Название дисциплины', help_text='Название дисциплины')
    teachers = models.ManyToManyField(Teacher, verbose_name='Преподаватели', help_text='Преподаватели с этой дисциплиной')
    groups = models.ManyToManyField(Group, verbose_name='Группы', help_text='Группы с этой дисциплиной')

    class Meta:
        verbose_name = 'Дисциплина'
        verbose_name_plural = 'Дисциплины'

    def __str__(self):
        return 'Дисциплина: {}'.format(self.name)