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

    def generate_excel_document(self, table_id):
        template_file_name = 'doc_template'
        new_file_name = 'doc_result'
        table = Table.objects.get(id=table_id)
        doc_table_headers_types = table.grades_types()
        students = table.students_and_grades()
        doc_table_headers = self.get_short_headers(doc_table_headers_types)
        student_number = 1
        all_students_data = []
        for student in students:
            '''
            student_fio_words = student['fio'].split()
            try:
                student_middle_name = student_fio_words[2]
            except:
                student_middle_name = ''
            student_data = [student_number, student_fio_words[0], student_fio_words[1], student_middle_name]
            '''
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
        write_sheet.write(4, 2, 'НЕТ', self.get_style('department_name')) # TODO
        write_sheet.write(5, 2, table.table_name, self.get_style('discipline_name'))
        write_sheet.write(6, 2, table.table_group.number, self.get_style('group_number'))
        write_sheet.write(7, 1, 'НЕТ', self.get_style('sem_number')) # TODO

        # Заголовки таблицы
        for i in range(len(doc_table_headers)):
            # short_header = self.get_short_header(doc_table_headers[i])
            write_sheet.write(10, i + 4, doc_table_headers[i], self.get_style('table_header'))

        # Тело таблицы - данные студентов
        for i in range(len(all_students_data)):
            write_sheet.merge(i + 11, i + 11, 1, 3, self.get_style('student_info'))
            # write_sheet.write(i + 11, 0, all_students_data[i][0])
            # write_sheet.write(i + 11, 1, all_students_data[i][1])
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
        write_sheet.write(footer_row + 1, 2, '(подпись)', self.get_style('sign_footer' ))
        write_sheet.write(footer_row + 1, 3, '(Фамилия И.О.)', self.get_style('sign_footer'))
        new_book.save(self.find_path('generated_docs/' + new_file_name, '.xls'))

        return self.find_path('generated_docs/' + new_file_name, '.xls')

    def find_path(self, filename, format):
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + '/files/' + filename + format
        return path

    def get_short_headers(self, all_header_types):
        doc_table_headers = []
        for type in all_header_types:
            if type == 'Итог':
                doc_table_headers.append(type)
            else:
                short_type = ''
                words_in_type = type.split()

                if len(words_in_type) == 1:     # Если заголовок однословный - оставляем аббревиатуры,
                    if type.upper() == type:    # иначе сокращаем до 3 букв при длинне больше 6
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
        last_name = teacher.user.last_name
        first_name_short = teacher.user.first_name[0].upper() + '.'
        if teacher.user.middle_name == '':
            return last_name + ' ' + first_name_short
        else:
            middle_name_short = teacher.user.middle_name[0].upper() + '.'
            return last_name + '\n' + first_name_short + middle_name_short

    def get_style(self, text_type):
        style = ''

        if text_type == 'discipline_name':
            style = xlwt.easyxf("font: color black, name Times New Roman, bold on, height 280;"
                                "align: horiz left, vert centre;")
        if text_type == 'group_number':
            style = xlwt.easyxf("font: color black, name Times New Roman, bold on, height 280;"
                                "align: horiz centre, vert centre;")
        if text_type == 'department_name':
            style = xlwt.easyxf("font: color black, name Times New Roman, italic on, height 240;"
                                "align: horiz left, vert centre")
        if text_type == 'sem_number':
            style = xlwt.easyxf("font: color black, name Times New Roman, bold on, height 240;"
                                "align: horiz right, vert centre")
        if text_type == 'student_info':
            style = xlwt.easyxf("font: color black, name Arial, height 180;"
                                "align: horiz left, vert centre;"
                                "borders: left thin, top thin, right thin, bottom thin;")
        if text_type == 'grades_info':
            style = xlwt.easyxf("font: color black, name Arial, height 180;"
                                "align: horiz centre, vert centre;"
                                "borders: left thin, top thin, right thin, bottom thin;")
        if text_type == 'table_header':
            style = xlwt.easyxf("font: color black, name Times New Roman, height 200;"
                                "align: horiz centre, vert centre;"
                                "borders: left thin, top thin, right thin, bottom thin;")
        if text_type == 'teacher_fio':
            style = xlwt.XFStyle()
            al = xlwt.Alignment()
            al.wrap = xlwt.Alignment.WRAP_AT_RIGHT
            al.horz = xlwt.Alignment.HORZ_RIGHT
            style.font.height = 280
            style.alignment = al
            borders = xlwt.Borders()
            borders.bottom = 1
            style.borders = borders

        if text_type == 'teacher_title':
            style = xlwt.easyxf("font: color black, name Times New Roman, height 240;"
                                "align: horiz right, vert centre;")
        if text_type == 'sign_field':
            style = xlwt.easyxf("border: bottom thin")
        if text_type == 'sign_footer':
            style = xlwt.easyxf("font: color black, name Times New Roman, italic on, height 200;"
                                "align: horiz centre;")
        return style