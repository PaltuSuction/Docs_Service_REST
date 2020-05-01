from django.contrib import admin
from django.utils.safestring import mark_safe

from tablegenapi.UserModel import User
from tablegenapi.models import Student, Teacher, Group, StudyDirection, Faculty, Discipline
# from authentication_part.models import User
# Register your models here.

#admin.site.register(Student)
@admin.register(Student)
class AdminStudent(admin.ModelAdmin):
    #fields = ('lastName', 'firstName', 'middleName', 'ticketNumber')
    list_display = ('ticket_number', 'student_full_name')
    # ordering = ('ticketNumber', 'student_last_name')

    def student_last_name(self, instance):
        try:
            return instance.last_name
        except: 'N/A'

    def student_full_name(self, instance):
        return '{} {} {}'.format(instance.last_name, instance.first_name, instance.middle_name)


admin.site.register(Teacher)
admin.site.register(User)

@admin.register(Group)
class AdminGroup(admin.ModelAdmin):
    list_display = ('number', 'studying_direction')
    ordering = ('studying_direction', 'number')


@admin.register(StudyDirection)
class AdminStudyDirection(admin.ModelAdmin):
    list_display = ('name', 'groups_with_direction')

    def groups_with_direction(self, obj):
        to_return = '<ul>'
        # I'm assuming that there is a name field under the event.Product model. If not change accordingly.
        to_return += '\n'.join('<li>{}</li>'.format(group.number) for group in obj.group_set.all())
        to_return += '</ul>'
        return mark_safe(to_return)


admin.site.register(Faculty)


@admin.register(Discipline)
class AdminDiscipline(admin.ModelAdmin):
    list_display = ('name', 'groups_with_discipline')

    def groups_with_discipline(self, obj):
        to_return = '<ul>'
        # I'm assuming that there is a name field under the event.Product model. If not change accordingly.
        to_return += '\n'.join('<li>{}</li>'.format(group.number) for group in obj.groups.all())
        to_return += '</ul>'
        return mark_safe(to_return)


# admin.site.register(User)