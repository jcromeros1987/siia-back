import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserProfileManager(BaseUserManager):
    def create_user(
        self,
        email: str,
        name: str,
        first_apellido: str = None,
        second_apellido: str = None,
        password: str = None,
    ):
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            name=name,
            first_apellido=first_apellido,
            second_apellido=second_apellido,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        email: str,
        name: str,
        first_apellido: str = None,
        second_apellido: str = None,
        password: str = None,
    ):
        user = self.create_user(
            email=email,
            name=name,
            first_apellido=first_apellido,
            second_apellido=second_apellido,
            password=password,
        )

        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    first_apellido = models.CharField(max_length=255, null=True)
    second_apellido = models.CharField(max_length=255, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserProfileManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def get_full_name(self):
        return f"{self.name} {self.first_apellido} {self.second_apellido}"

    def get_short_name(self):
        return self.name

    def __str__(self):
        return self.email

    class Meta:
        db_table = "cvu_users"
        verbose_name = "User"
        verbose_name_plural = "Users"
