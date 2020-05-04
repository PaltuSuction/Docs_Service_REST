from django.urls import path, include
from rest_framework import routers
from .views import *
router = routers.DefaultRouter()
router.register('students', StudentViewSet)
router.register('groups', GroupViewSet)
router.register('groups', GroupViewSet)
router.register('teachers', TeacherViewSet)
router.register('studying_directs', StudyDirectionViewSet)
router.register('faculties', FacultyViewSet)
router.register('users', UserViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('parse_file/', ExcelParserView.as_view()),
    path('faculties_and_directs/', FacultsAndDirectsView.as_view()),
    path('registration/', CustomRegisterView.as_view()),
    path('user_info/', UserInfoView.as_view()),
    path('groups_by_direct/<str:studying_direct_name>/', GroupsByDirectView.as_view()),

    path('table_creator/<int:table_id>/', TableCreatorView.as_view()),
    path('table_creator/', TableCreatorView.as_view()),
]