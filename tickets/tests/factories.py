import factory

from tickets.models import Comment, Ticket
from users.models import User
from users.tests.factories import UserFactory


class ClientFactory(UserFactory):
    role = User.Role.CLIENT


class DeveloperFactory(UserFactory):
    role = User.Role.DEVELOPER


class TicketFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ticket

    title = factory.Faker("sentence", nb_words=4)
    creator = factory.SubFactory(ClientFactory)
    description = factory.Faker("text", max_nb_chars=200)


# TODO: improve CommentFactory when role-based comment restrictions are added.
class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    ticket = factory.SubFactory(TicketFactory)
    user = factory.SubFactory(ClientFactory)
    body = factory.Faker("text", max_nb_chars=200)
