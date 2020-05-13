import datetime
import os
import xlrd
import xlwt
from xlutils.copy import copy

# from docx import Document
# from docx.enum.section import WD_ORIENTATION, WD_SECTION_START

import pandas as pd
import pdfkit as pdf
from tablegenapi.UserModel import User
from tablegenapi.models import Student, Group, StudyDirection, Faculty, Table
from rest_framework.authtoken.models import Token


class DocumentHandler():

    def parse_excel_file(self, filename):
        print('Парсинг начался для файла: {}'.format(filename))
        faculty = Faculty.objects.get(name=filename)
        path = self.find_path('faculties/' + filename, '.xlsx')
        book = xlrd.open_workbook(path)
        sheet = book.sheet_by_index(0)
        prev_direction = ''
        prev_group = ''
        already_parsed_groups = []
        study_direction = ''
        group = ''

        groups_and_dirs = {}
        students_in_group = {}
        for rownumber in range(1, sheet.nrows, 1):
            row = sheet.row_values(rownumber)

            stud_dir = row[4]
            grp = row[7]

            if stud_dir != prev_direction:
                study_direction, dir_created_now = StudyDirection.objects.get_or_create(name=row[4], faculty=faculty)
                prev_direction = stud_dir
                if not dir_created_now:
                    if not groups_and_dirs.get(stud_dir):
                        groups_and_dirs[stud_dir] = [group.number for group in
                                                     Group.objects.filter(studying_direction=study_direction)]

            if grp != prev_group:
                already_parsed_groups.append(grp)
                group, grp_created_now = Group.objects.get_or_create(number=str(row[7]),
                                                                     studying_direction=study_direction,
                                                                     studying_start_year=str(xlrd.xldate_as_tuple(row[8], 0)[0]))
                if not grp_created_now:
                    groups_and_dirs[stud_dir].remove(group.number)  # Удаляем группу из списка кандидатов на удаление
                    students_in_group[group.number] = group.group_all_students_ids()  # Все студенты в текущей группе - кандидаты на удаление
                prev_group = grp

            try:
                student_middle_name = row[1].split(' ')[2]
            except:
                student_middle_name = ''
            '''new_student_user, user_created_now = User.objects.get_or_create(email=row[0],
                                                                        last_name=row[1].split(' ')[0],
                                                                        first_name=row[1].split(' ')[1],
                                                                        middle_name=student_middle_name,
                                                                        is_student=True,
                                                                        )'''

            # if user_created_now:
            # new_student_user.set_password('testpassword1')
            # new_student_user.save()
            #
            new_student, student_created_now = Student.objects.get_or_create(last_name=row[1].split(' ')[0],
                                                                             first_name=row[1].split(' ')[1],
                                                                             middle_name=student_middle_name,
                                                                             student_group=group,
                                                                             ticket_number=row[0],
                                                                             )
            if student_created_now:
                print('Добавлены данные студента (группа: {})'.format(grp))
            else:
                students_in_group[group.number].remove(new_student.id)
                print('Данные студента не изменены: (группа: {})'.format(grp))

        for direct_name in groups_and_dirs:  # Удаляем все группы, которые были в БД, но отсутствуют в новом списке
            for group_number in groups_and_dirs[direct_name]:
                if group_number not in already_parsed_groups:
                    group_to_delete = Group.objects.get(number=group_number)
                    print('Удалена группа №{}'.format(group_to_delete.number))
                    group_to_delete.delete()

        for group_number in students_in_group:  # Удаляем всех студентов, которые были в БД, но отсутствуют в новом списке
            for student_id in students_in_group[group_number]:
                student_to_delete = Student.objects.get(id=student_id)
                try: # Если у этого студента был аккаунт - удаляем
                    user_to_delete = User.objects.get(student=student_to_delete)
                    user_to_delete.delete()
                except: pass
                print('Студент удален: № {}'.format(student_to_delete.ticket_number))
                student_to_delete.delete()

        print('Парсинг прошел успешно')
        print(groups_and_dirs)
        print(students_in_group)

    def generate_excel_document(self, table_id):
        template_file_name = 'doc_template'
        table = Table.objects.get(id=table_id)

        new_file_name = '{}_{}'.format(table.table_name, table.table_group.number)
        doc_table_headers_types = table.grades_types()
        students = table.students_and_grades()
        doc_table_headers = self.get_short_headers(doc_table_headers_types)
        student_number = 1
        all_students_data = []
        for student in students:
            student_data = [student_number, student['fio']]
            for grade_type in student['grades']:
                for grade in student['grades'][grade_type]:
                    student_data.append(grade['grade_value'])
            all_students_data.append(student_data)
            student_number += 1

        path = self.find_path('docs_templates/' + template_file_name, '.xls')
        template_book = xlrd.open_workbook(path, on_demand=True, formatting_info=True)
        new_book = copy(template_book)
        write_sheet = new_book.get_sheet(0)
        write_sheet.set_portrait(False)

        # Заголовок документа
        write_sheet.write(4, 2, table.table_department, self.get_style('department_name'))
        write_sheet.write(5, 2, table.table_name, self.get_style('discipline_name'))
        write_sheet.write(6, 2, table.table_group.number, self.get_style('group_number'))
        write_sheet.write(7, 1, self.group_semester_and_year(table.table_group)[0], self.get_style('sem_number'))
        write_sheet.write(8, 1, self.group_semester_and_year(table.table_group)[1], self.get_style('teacher_fio'))
        # Заголовки таблицы
        for i in range(len(doc_table_headers)):
            # short_header = self.get_short_header(doc_table_headers[i])
            write_sheet.write(10, i + 4, doc_table_headers[i], self.get_style('table_header'))

        # Тело таблицы - данные студентов
        for i in range(len(all_students_data)):
            write_sheet.merge(i + 11, i + 11, 1, 3, self.get_style('student_info'))
            for j in range(0, 2):
                write_sheet.write(i + 11, j, all_students_data[i][j], self.get_style('student_info'))
            for j in range(2, len(all_students_data[i])):
                write_sheet.write(i + 11, j + 2, all_students_data[i][j], self.get_style('grades_info'))

        # Футер таблицы - информация о преподавателе
        footer_row = len(all_students_data) + 11 + 2
        # footer_row = 38
        write_sheet.write(footer_row, 1, 'Преподаватель', self.get_style('teacher_title'))
        write_sheet.write(footer_row, 2, '', self.get_style('sign_field'))
        write_sheet.write(footer_row, 3, self.get_teacher_fio(table.table_teacher), self.get_style('teacher_fio'))
        write_sheet.write(footer_row + 1, 2, '(подпись)', self.get_style('sign_footer'))
        write_sheet.write(footer_row + 1, 3, '(Фамилия И.О.)', self.get_style('sign_footer'))
        new_book.save(self.find_path('generated_docs/' + new_file_name, '.xls'))

        return new_file_name

    def find_path(self, filename, format):
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + '/files/' + filename + format
        return path

    def get_short_headers(self, all_header_types):
        doc_table_headers = []
        for type in all_header_types:
            if type == '\u05C4Итог':
                doc_table_headers.append(type)
            else:
                short_type = ''
                words_in_type = type.split()

                if len(words_in_type) == 1:  # Если заголовок однословный - оставляем аббревиатуры,
                    if type.upper() == type:  # иначе сокращаем до 3 букв при длинне больше 6
                        for n in range(all_header_types[type]):
                            doc_table_headers.append('{} {}'.format(type, n + 1))
                    else:
                        if len(type) > 6:
                            short_type = type[0:3:1] + '.'
                        else:
                            short_type = type
                        for n in range(all_header_types[type]):
                            doc_table_headers.append('{} {}'.format(short_type, n + 1))

                if len(words_in_type) > 1:
                    for word in words_in_type:
                        short_type = short_type + word[0].upper() + '. '
                    for n in range(all_header_types[type]):
                        doc_table_headers.append('{}{}'.format(short_type, n + 1))

        return doc_table_headers

    def get_teacher_fio(self, teacher):
        last_name = teacher.last_name
        first_name_short = teacher.first_name[0].upper() + '.'
        if teacher.middle_name == '':
            return last_name + ' ' + first_name_short
        else:
            middle_name_short = teacher.middle_name[0].upper() + '.'
            return last_name + '\n' + first_name_short + middle_name_short

    def group_semester_and_year(self, group):
        now = datetime.datetime.now()
        current_study_year = ''
        study_year = int(now.year) - int(group.studying_start_year)
        if now.month >= 9 and now.month < 12:  # Семестр нечётный
            sem_number = study_year * 2 - 1
            current_study_year = str(now.year) + '/' + str(int(now.year) + 1)
        else:  # Семестр чётный
            sem_number = study_year * 2
            current_study_year = str(int(now.year) - 1) + '/' + str(now.year)
        return (sem_number, current_study_year)


    def get_style(self, text_type):
        style = xlwt.XFStyle()
        al = xlwt.Alignment()
        al.vert = xlwt.Alignment.VERT_CENTER
        if text_type == 'discipline_name':
            al.horz = xlwt.Alignment.HORZ_LEFT
            style.font.height = 280
            style.font.bold = True
        if text_type == 'group_number':
            al.horz = xlwt.Alignment.HORZ_CENTER
            style.font.height = 280
            style.font.bold = True
        if text_type == 'department_name':
            al.horz = xlwt.Alignment.HORZ_LEFT
            style.font.height = 240
            style.font.italic = True
        if text_type == 'sem_number':
            al.horz = xlwt.Alignment.HORZ_RIGHT
            style.font.height = 240
            style.font.bold = True
            style.font.name = 'Times New Roman'
        if text_type == 'student_info':
            al.horz = xlwt.Alignment.HORZ_LEFT
            style.font.height = 180
            borders = xlwt.Borders()
            borders.bottom = 1
            borders.left = 1
            borders.right = 1
            borders.top = 1
            style.borders = borders
        if text_type == 'grades_info':
            al.horz = xlwt.Alignment.HORZ_CENTER
            style.font.height = 180
            borders = xlwt.Borders()
            borders.bottom = 1
            borders.left = 1
            borders.right = 1
            borders.top = 1
            style.borders = borders
        if text_type == 'table_header':
            al.horz = xlwt.Alignment.HORZ_CENTER
            style.font.height = 200
            borders = xlwt.Borders()
            borders.bottom = 1
            borders.left = 1
            borders.right = 1
            borders.top = 1
            style.borders = borders
        if text_type == 'teacher_fio':
            al.wrap = xlwt.Alignment.WRAP_AT_RIGHT
            al.horz = xlwt.Alignment.HORZ_RIGHT
            al.vert = xlwt.Alignment.VERT_BOTTOM
            style.font.height = 280
            borders = xlwt.Borders()
            borders.bottom = 1
            style.borders = borders
        if text_type == 'teacher_title':
            al.horz = xlwt.Alignment.HORZ_RIGHT
            style.font.height = 240
            style.font.name = 'Times New Roman'
        if text_type == 'sign_field':
            borders = xlwt.Borders()
            borders.bottom = 1
            style.borders = borders
        if text_type == 'sign_footer':
            al.horz = xlwt.Alignment.HORZ_CENTER
            style.font.italic = True
            style.font.height = 200
            style.font.name = 'Times New Roman'
        style.alignment = al
        return style
