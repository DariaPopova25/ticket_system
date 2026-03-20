import factory

from users.models import User

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("user_name")
    email = email = factory.Faker("email")
    role = User.Role.CLIENT
    password = factory.django.Password("example_password")
