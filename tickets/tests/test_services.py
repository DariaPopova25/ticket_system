import pytest
from django.core.exceptions import ValidationError

from tickets.models import Ticket
from users.models import User
from tickets.services import create_ticket, manager_update_ticket, developer_update_ticket, create_comment
from users.tests.factories import ClientFactory, ManagerFactory, DeveloperFactory
from .factories import TicketFactory


@pytest.fixture
def user_client():
    return ClientFactory.create()

@pytest.fixture
def user_developer():
    return DeveloperFactory.create()

@pytest.fixture
def user_manager():
    return ManagerFactory.create()


@pytest.fixture
def ticket_factory(user_client, user_developer):
    def make_ticket(creator = user_client, assignee = user_developer, status=Ticket.Status.NEW):
        return TicketFactory.create(
            creator=creator,
            status=status,
            assignee=assignee,
            priority=Ticket.Priority.HIGH,
        )

    return make_ticket


CLOSED_STATUSES = [
    Ticket.Status.DONE,
    Ticket.Status.CANCELLED,
]

@pytest.mark.django_db
class TestCreateTicket:
    def test_client_can_create_ticket(self, user_client):

        ticket = create_ticket(
            actor = user_client,
            title = 'Test title',
            description = 'Test description',
        )

        assert ticket.creator == user_client
        assert ticket.creator.role == User.Role.CLIENT
        assert ticket.title == 'Test title'
        assert ticket.description == 'Test description'

    @pytest.mark.parametrize("user_fixture", ["user_developer", "user_manager"])
    def test_raises_error_if_actor_is_not_client(self, request, user_fixture):
        user = request.getfixturevalue(user_fixture)
        
        with pytest.raises(ValidationError) as excinfo:
            create_ticket(
                actor = user,
                title = 'Test title',
                description = 'Test description'
            )

        assert excinfo.value.messages == ["Only client can create ticket."]

@pytest.mark.django_db
class TestManagerUpdateTicket:

    MANAGER_ALLOWED_STATUSES = [
        Ticket.Status.NEW,
        Ticket.Status.PENDING_DEVELOPMENT,
        Ticket.Status.IN_PROGRESS,
        Ticket.Status.PENDING_REVIEW,
        Ticket.Status.DONE,
        Ticket.Status.CANCELLED,
    ]

    NON_NEW_OPEN_STATUSES = [
        Ticket.Status.PENDING_DEVELOPMENT,
        Ticket.Status.IN_PROGRESS,
        Ticket.Status.PENDING_REVIEW,
    ]

    @pytest.mark.parametrize("status", MANAGER_ALLOWED_STATUSES)
    def test_manager_can_update_ticket(self, status, user_manager, user_developer, ticket_factory):
        ticket = ticket_factory()

        updated_ticket = manager_update_ticket(
            actor = user_manager,
            ticket = ticket,
            status=status,
            assignee=user_developer,
            priority=Ticket.Priority.LOW,
            manager_notes='Test manager_notes',
        )

        assert updated_ticket.id == ticket.id
        assert updated_ticket.status == status
        assert updated_ticket.assignee == user_developer
        assert updated_ticket.priority == Ticket.Priority.LOW
        assert updated_ticket.manager_notes == 'Test manager_notes'

    def test_manager_can_remove_assignee_in_new_status(self, user_manager, ticket_factory):
        ticket = ticket_factory(status=Ticket.Status.IN_PROGRESS)

        updated_ticket = manager_update_ticket(
            actor = user_manager,
            ticket = ticket,
            status=Ticket.Status.NEW,
            assignee=None,
        )

        assert updated_ticket.id == ticket.id
        assert updated_ticket.status == Ticket.Status.NEW
        assert updated_ticket.assignee is None

    @pytest.mark.parametrize("user_fixture", ["user_developer", "user_client"])
    def test_raises_error_if_actor_is_not_manager(self, request, ticket_factory, user_fixture):
        ticket = ticket_factory()
        user = request.getfixturevalue(user_fixture)
        
        with pytest.raises(ValidationError) as excinfo:
            manager_update_ticket(
                actor = user,
                ticket = ticket,
                status=Ticket.Status.PENDING_DEVELOPMENT,
            )
        
        assert excinfo.value.messages == ["Only manager can update ticket."]

    @pytest.mark.parametrize("status", CLOSED_STATUSES)
    def test_raises_error_if_manager_updates_closed_ticket(self, status, ticket_factory, user_manager):
        ticket = ticket_factory(status = status)

        with pytest.raises(ValidationError) as excinfo:
            manager_update_ticket(
                actor = user_manager,
                ticket = ticket,
                status = Ticket.Status.NEW
            )

        assert excinfo.value.message_dict["status"] == [
            "Closed tickets cannot be changed."
        ]

    @pytest.mark.parametrize("status", NON_NEW_OPEN_STATUSES)
    def test_raises_error_if_manager_removes_assignee_outside_new(self, status, ticket_factory, user_manager):
        ticket = ticket_factory(status = status)

        with pytest.raises(ValidationError) as excinfo:
            manager_update_ticket(
                actor = user_manager,
                ticket = ticket,
                assignee = None
            )

        assert excinfo.value.message_dict["assignee"] == [
            "Assignee can be removed only in new status."
        ]

    def test_raises_error_if_manager_assigns_non_developer(self, user_manager, user_client, ticket_factory):
        ticket = ticket_factory()

        with pytest.raises(ValidationError) as excinfo:
            manager_update_ticket(
                actor=user_manager,
                ticket=ticket,
                assignee=user_client,
            )

        assert excinfo.value.message_dict["assignee"] == [
            "Assignee must have developer role."
        ]

@pytest.mark.django_db
class TestDeveloperUpdateTicket:
    DEVELOPER_ALLOWED_STATUSES = [
        Ticket.Status.PENDING_DEVELOPMENT,
        Ticket.Status.IN_PROGRESS,
        Ticket.Status.PENDING_REVIEW,
    ]

    DEVELOPER_DISALLOWED_STATUSES = [
        Ticket.Status.NEW,
        Ticket.Status.DONE,
        Ticket.Status.CANCELLED,
    ]

    @pytest.mark.parametrize("status", DEVELOPER_ALLOWED_STATUSES)
    def test_developer_can_update_assigned_ticket(self, status, user_developer, ticket_factory):
        ticket = ticket_factory(status=status)

        updated_ticket = developer_update_ticket(
            actor = user_developer,
            ticket = ticket,
            status=status,
            resolution_notes='Test resolution_notes',
        )

        assert updated_ticket.id == ticket.id
        assert updated_ticket.status == status
        assert updated_ticket.resolution_notes == 'Test resolution_notes'

    @pytest.mark.parametrize("user_fixture", ["user_manager", "user_client"])
    def test_raises_error_if_actor_is_not_developer(self, request, ticket_factory, user_fixture):
        ticket = ticket_factory(status=Ticket.Status.PENDING_DEVELOPMENT)
        user = request.getfixturevalue(user_fixture)
        
        with pytest.raises(ValidationError) as excinfo:
            developer_update_ticket(
                actor = user,
                ticket = ticket,
                status=Ticket.Status.IN_PROGRESS,
            )
        
        assert excinfo.value.messages == ["Only developer can update ticket."]

    def test_raises_error_if_developer_updates_ticket_assigned_to_another_developer(self, ticket_factory, user_developer):
        other_developer = DeveloperFactory.create()
        other_ticket = ticket_factory(assignee = other_developer, status=Ticket.Status.PENDING_DEVELOPMENT)
        
        with pytest.raises(ValidationError) as excinfo:
            developer_update_ticket(
                actor = user_developer,
                ticket = other_ticket,
                status=Ticket.Status.IN_PROGRESS,
            )
        
        assert excinfo.value.message_dict["assignee"] == [
            "Developer can update only assigned tickets."
        ]

    @pytest.mark.parametrize("status", DEVELOPER_ALLOWED_STATUSES)
    def test_raises_error_if_developer_updates_ticket_in_new_status(self, status, ticket_factory, user_developer):
        ticket = ticket_factory(status=Ticket.Status.NEW)
        
        with pytest.raises(ValidationError) as excinfo:
            developer_update_ticket(
                actor = user_developer,
                ticket = ticket,
                status=status,
            )
        
        assert excinfo.value.message_dict["status"] == [
            "Developer can update ticket only after pending_development."
        ]

    @pytest.mark.parametrize("status", DEVELOPER_DISALLOWED_STATUSES)
    def test_raises_error_if_developer_sets_disallowed_status(self, status, ticket_factory, user_developer):
        ticket = ticket_factory(status=Ticket.Status.PENDING_DEVELOPMENT)
        
        with pytest.raises(ValidationError) as excinfo:
            developer_update_ticket(
                actor = user_developer,
                ticket = ticket,
                status=status,
            )
        
        assert excinfo.value.message_dict["status"] == [
            "Developer can change status only within working area."
        ]

    @pytest.mark.parametrize("status", CLOSED_STATUSES)
    def test_raises_error_if_developer_updates_closed_ticket(self, status, user_developer, ticket_factory):
        ticket = ticket_factory(status = status)

        with pytest.raises(ValidationError) as excinfo:
            developer_update_ticket(
                actor = user_developer,
                ticket = ticket,
                status = Ticket.Status.IN_PROGRESS
            )

        assert excinfo.value.message_dict["status"] == [
            "Closed tickets cannot be changed."
        ]

@pytest.mark.django_db
class TestCreateComment:
    def test_client_can_comment_on_own_ticket(self, user_client, ticket_factory):
        ticket = ticket_factory()

        comment = create_comment(
            actor=user_client,
            ticket=ticket,
            body='Test body',
        )

        assert comment.user == user_client
        assert comment.ticket.creator == user_client
        assert comment.user.role == User.Role.CLIENT
        assert comment.ticket == ticket
        assert comment.body == 'Test body'

    def test_developer_can_comment_on_assigned_ticket(self, user_developer, ticket_factory):
        ticket = ticket_factory()

        comment = create_comment(
            actor=user_developer,
            ticket=ticket,
            body='Test body',
        )

        assert comment.user == user_developer
        assert comment.ticket.assignee == user_developer
        assert comment.user.role == User.Role.DEVELOPER
        assert comment.ticket == ticket
        assert comment.body == 'Test body'

    def test_manager_can_comment_on_ticket(self, user_manager, ticket_factory):
        ticket = ticket_factory()

        comment = create_comment(
            actor=user_manager,
            ticket=ticket,
            body='Test body',
        )

        assert comment.user == user_manager
        assert comment.user.role == User.Role.MANAGER
        assert comment.ticket == ticket
        assert comment.body == 'Test body'

    def test_raises_error_if_client_comments_on_another_users_ticket(self, user_client, ticket_factory):
        other_creator = ClientFactory.create()
        other_ticket = ticket_factory(creator = other_creator, status=Ticket.Status.PENDING_DEVELOPMENT)
        
        with pytest.raises(ValidationError) as excinfo:
            create_comment(
                actor=user_client,
                ticket=other_ticket,
                body='Test body',
            )

        assert excinfo.value.messages == ["Client can comment only on own tickets."]

    def test_raises_error_if_developer_comments_on_ticket_assigned_to_another_developer(self, user_developer, ticket_factory):
        other_developer = DeveloperFactory.create()
        other_ticket = ticket_factory(assignee = other_developer, status=Ticket.Status.PENDING_DEVELOPMENT)
        
        with pytest.raises(ValidationError) as excinfo:
            create_comment(
                actor=user_developer,
                ticket=other_ticket,
                body='Test body',
            )

        assert excinfo.value.messages == ["Developer can comment only on assigned tickets."]
