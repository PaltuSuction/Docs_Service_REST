from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Создает и сохраняет пользователя с введенным им email и паролем.
        """
        if not email:
            raise ValueError('email должен быть указан')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email'), unique=True)
    # user_ident = models.CharField(max_length=200, unique=True) # student -> ticket_number, teacher -> email
    # first_name = models.CharField(_('first_name'), max_length=30, blank=True)
    # last_name = models.CharField(_('last_name'), max_length=30, blank=True)
    # middle_name = models.CharField(_('middle_name'), max_length=30, blank=True)

    is_staff = models.BooleanField(_('staff'), default=False)
    is_teacher = models.BooleanField(_('teacher'), default=False)
    is_student = models.BooleanField(_('student'), default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')

    def get_status(self):
        if self.is_teacher:
            return 'teacher'
        elif self.is_staff:
            return 'staff'
        elif self.is_staff:
            return 'student'
        else:
            return None

    def get_username(self):
        return self.email

    def first_name(self):
        if self.is_teacher:
            return self.teacher.first_name
        if self.is_student:
            return self.student.first_name

    def middle_name(self):
        if self.is_teacher:
            return self.teacher.middle_name
        if self.is_student:
            return self.student.middle_name

    def last_name(self):
        if self.is_teacher:
            return self.teacher.last_name
        if self.is_student:
            return self.student.last_name
