import factory

from users.models import User
from tickets.models import Ticket
from users.tests.factories import UserFactory


class ClientFactory(UserFactory):
    role = User.Role.CLIENT

class DeveloperFactory(UserFactory):
    role = User.Role.DEVELOPER

class TicketFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ticket
    
    title = factory.Faker('sentence', nb_words=4)
    creator = factory.SubFactory(ClientFactory)
    description = factory.Faker('text', max_nb_chars=200)
