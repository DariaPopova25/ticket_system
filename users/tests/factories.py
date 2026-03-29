import factory

from users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("user_name")
    email = factory.Faker("email")
    password = factory.django.Password("example_password")

class ClientFactory(UserFactory):
    role = User.Role.CLIENT

class DeveloperFactory(UserFactory):
    role = User.Role.DEVELOPER

class ManagerFactory(UserFactory):
    role = User.Role.MANAGER
