from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = "client", "Client"
        MANAGER = "manager", "Manager"
        DEVELOPER = "developer", "Developer"

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=Role,
        default=Role.CLIENT,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email
