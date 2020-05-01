import os
import xlrd as xlrd

from tablegenapi.UserModel import User
from tablegenapi.models import Student, Group, StudyDirection, Faculty
from rest_framework.authtoken.models import Token


class ExcelParser():

    def parse_excel_file(self, filename):
        print('Парсинг начался для файла: {}'.format(filename))
        faculty = Faculty.objects.get(name=filename)

        path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + '/files/' + filename + '.xlsx'
        book = xlrd.open_workbook(path)
        sheet = book.sheet_by_index(0)
        prev_stud_dir = ''
        prev_grp = ''
        study_direction = ''
        group = ''
        for rownumber in range(1, sheet.nrows, 1):
            row = sheet.row_values(rownumber)

            stud_dir = row[4]
            grp = row[7]

            if stud_dir != prev_stud_dir:
                study_direction, created = StudyDirection.objects.get_or_create(name=row[4], faculty=faculty)
                prev_stud_dir = stud_dir

            if grp != prev_grp:
                group, created = Group.objects.get_or_create(number=str(row[7]), studying_direction=study_direction)
                prev_grp = grp

            try:
                student_middle_name = row[1].split(' ')[2]
            except:
                student_middle_name = ''

            new_student_user = User.objects.create(username=row[0],
                                                   last_name=row[1].split(' ')[0],
                                                   first_name=row[1].split(' ')[1],
                                                   middle_name=student_middle_name,
                                                   is_student=True,
                                                   )
            new_student_user.set_password('testpassword1')
            new_student_user.save()
            new_student = Student.objects.create(user=new_student_user,
                                                 student_group=group,
                                                 ticket_number=row[0],
                                                 )
            Token.objects.create(user=new_student_user)
            print('Студент добавлен (группа: {})'.format(grp))

        print('Парсинг прошел успешно')
