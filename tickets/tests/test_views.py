import pytest
from django.urls import reverse

from tickets.models import Ticket, Comment

from users.models import User
from users.tests.factories import ClientFactory, DeveloperFactory, ManagerFactory

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
    def make_ticket(
        creator=user_client,
        assignee=user_developer,
        status=Ticket.Status.NEW,
    ):
        return TicketFactory.create(
            creator=creator,
            status=status,
            assignee=assignee,
            priority=Ticket.Priority.HIGH,
        )

    return make_ticket


@pytest.mark.django_db
class TestTicketListView:
    def test_ticket_list_shows_all_tickets_to_manager(
        self,
        client,
        user_manager,
        ticket_factory,

    ):
        ticket_one = ticket_factory()
        ticket_two = ticket_factory(creator=ClientFactory.create())

        client.force_login(user_manager)

        response = client.get(reverse("tickets:list"))
        tickets = response.context["tickets"]

        assert response.status_code == 200
        assert ticket_one in tickets
        assert ticket_two in tickets

    def test_ticket_list_shows_only_own_tickets_to_client(
        self,
        client,
        user_client,
        ticket_factory
    ):
        client_ticket = ticket_factory()
        other_client_ticket = ticket_factory(creator=ClientFactory.create())

        client.force_login(user_client)

        response = client.get(reverse("tickets:list"))
        tickets = response.context["tickets"]

        assert response.status_code == 200
        assert client_ticket in tickets
        assert other_client_ticket not in tickets

    def test_ticket_list_shows_only_assigned_tickets_to_developer(
        self,
        client,
        user_developer,
        ticket_factory,
    ):

        assigned_ticket = ticket_factory()
        unassigned_ticket = ticket_factory(assignee=DeveloperFactory.create())

        client.force_login(user_developer)

        response = client.get(reverse("tickets:list"))
        tickets = response.context["tickets"]

        assert response.status_code == 200
        assert assigned_ticket in tickets
        assert unassigned_ticket not in tickets

    def test_ticket_list_redirects_unauthenticated_user_to_login(self, client):
        response = client.get(reverse("tickets:list"))

        assert response.status_code == 302
        assert response.url == f'{reverse("users:login")}?next={reverse("tickets:list")}'

@pytest.mark.django_db
class TestTicketDetailView:
    def test_manager_can_view_ticket_detail(
        self,
        client,
        user_manager,
        ticket_factory,
    ):
    
        any_ticket = ticket_factory()

        client.force_login(user_manager)

        response = client.get(reverse("tickets:detail", kwargs={'pk': any_ticket.id}))
        ticket = response.context["ticket"]

        assert response.status_code == 200
        assert any_ticket == ticket

    def test_client_can_view_own_ticket_detail(
        self,
        client,
        user_client,
        ticket_factory,
    ):

        client_ticket = ticket_factory()

        client.force_login(user_client)

        response = client.get(reverse("tickets:detail", kwargs={'pk': client_ticket.id}))
        ticket = response.context["ticket"]

        assert response.status_code == 200
        assert client_ticket == ticket

    def test_developer_can_view_assigned_ticket_detail(
        self,
        client,
        user_developer,
        ticket_factory,
    ):

        assigned_ticket = ticket_factory()

        client.force_login(user_developer)

        response = client.get(reverse("tickets:detail", kwargs={'pk': assigned_ticket.id}))
        ticket = response.context["ticket"]

        assert response.status_code == 200
        assert assigned_ticket == ticket

    def test_client_cannot_view_other_users_ticket_detail(
        self,
        client,
        user_client,
        ticket_factory,
    ):
        other_client_ticket = ticket_factory(creator=ClientFactory.create())
        client.force_login(user_client)

        response = client.get(
            reverse("tickets:detail", kwargs={"pk": other_client_ticket.id})
        )

        assert response.status_code == 404

    def test_developer_cannot_view_not_assigned_ticket_detail(
        self,
        client,
        user_developer,
        ticket_factory,
    ):
        unassigned_ticket = ticket_factory(assignee=DeveloperFactory.create())
        client.force_login(user_developer)

        response = client.get(
            reverse("tickets:detail", kwargs={"pk": unassigned_ticket.id})
        )

        assert response.status_code == 404

    def test_ticket_detail_redirects_unauthenticated_user_to_login(
        self,
        client,
        ticket_factory
    ):
        ticket = ticket_factory()
    
        detail_url = reverse("tickets:detail", kwargs={"pk": ticket.id})

        response = client.get(detail_url)

        assert response.status_code == 302
        assert response.url == f'{reverse("users:login")}?next={detail_url}'

@pytest.mark.django_db
class TestTicketCreateView:
    def test_client_can_view_ticket_create_form(
        self,
        client,
        user_client,
    ):

        client.force_login(user_client)

        response = client.get(reverse("tickets:create"))
        form = response.context["form"]
        allowed_fields = {"title", "description"}

        assert response.status_code == 200
        assert set(form.fields) == allowed_fields

    def test_client_can_create_ticket_and_redirect_to_detail(
        self,
        client,
        user_client,
    ):

        client.force_login(user_client)

        response = client.post(
            reverse("tickets:create"),
            data={
                "title": "Test ticket",
                "description": "Test description",
            },
        )

        created_ticket = Ticket.objects.get(title="Test ticket")

        assert response.status_code == 302
        assert response.url == reverse("tickets:detail", kwargs={"pk": created_ticket.id})
        assert created_ticket.creator == user_client
        assert created_ticket.description == "Test description"

    @pytest.mark.parametrize("user_fixture", ["user_manager", "user_developer"])
    def test_non_client_cannot_access_ticket_create_view(
        self,
        client,
        request,
        user_fixture,
    ):
        user = request.getfixturevalue(user_fixture)
        client.force_login(user)

        response = client.get(reverse("tickets:create"))

        assert response.status_code == 403

    def test_client_cannot_create_ticket_with_invalid_data(
        self,
        client,
        user_client,
    ):
        client.force_login(user_client)

        response = client.post(
            reverse("tickets:create"),
            data={
                "title": "",
                "description": "",
            },
        )

        assert response.status_code == 200
        assert response.context["form"].errors
        assert Ticket.objects.count() == 0

    def test_ticket_create_redirects_unauthenticated_user_to_login(self, client):
        response = client.get(reverse("tickets:create"))

        assert response.status_code == 302
        assert response.url == f'{reverse("users:login")}?next={reverse("tickets:create")}'

@pytest.mark.django_db
class TestTicketUpdateView:

    CLOSED_STATUSES = [
        Ticket.Status.DONE,
        Ticket.Status.CANCELLED,
    ]

    DEVELOPER_DISALLOWED_STATUSES = [
        Ticket.Status.NEW,
        Ticket.Status.DONE,
        Ticket.Status.CANCELLED,
    ]

    def test_manager_can_access_ticket_update_view(
        self,
        client,
        user_manager,
        ticket_factory
    ):

        any_ticket = ticket_factory()

        client.force_login(user_manager)

        response = client.get(reverse("tickets:update", kwargs={"pk": any_ticket.id}))
        form = response.context["form"]
        allowed_fields = {"status", "assignee", "priority", "manager_notes"}

        assert response.status_code == 200
        assert set(form.fields) == allowed_fields

    def test_developer_can_access_assigned_ticket_update_view(
        self,
        client,
        user_developer,
        ticket_factory,
    ):
        assigned_ticket = ticket_factory(status = Ticket.Status.PENDING_DEVELOPMENT)
        
        
        client.force_login(user_developer)

        response = client.get(reverse("tickets:update", kwargs={"pk": assigned_ticket.id}))
        form = response.context["form"]
        allowed_fields = {"status", 'resolution_notes'}

        assert response.status_code == 200
        assert set(form.fields) == allowed_fields

    def test_manager_can_update_open_ticket(
        self,
        client,
        user_manager,
        user_developer,
        ticket_factory,
    ):
        any_ticket = ticket_factory()

        client.force_login(user_manager)

        response = client.post(
            reverse("tickets:update", kwargs={"pk": any_ticket.id}),
            data ={
                "status": Ticket.Status.PENDING_DEVELOPMENT,
                "assignee": user_developer.id,
                "priority": Ticket.Priority.LOW,
                "manager_notes": "Test manager_notes",               
            }
        )

        any_ticket.refresh_from_db()

        assert response.status_code == 302
        assert response.url == reverse("tickets:detail", kwargs={"pk": any_ticket.id})
        assert any_ticket.status == Ticket.Status.PENDING_DEVELOPMENT
        assert any_ticket.assignee == user_developer
        assert any_ticket.priority == Ticket.Priority.LOW
        assert any_ticket.manager_notes == "Test manager_notes"

    def test_developer_can_update_assigned_ticket_with_allowed_status(
        self,
        client,
        user_developer,
        ticket_factory,
    ):
        assigned_ticket = ticket_factory(status = Ticket.Status.PENDING_DEVELOPMENT)

        client.force_login(user_developer)

        response = client.post(
            reverse("tickets:update", kwargs={"pk": assigned_ticket.id}),
            data ={
                "status": Ticket.Status.IN_PROGRESS,
                "resolution_notes": "Test resolution_notes",
            }
        )

        assigned_ticket.refresh_from_db()

        assert response.status_code == 302
        assert response.url == reverse("tickets:detail", kwargs={"pk": assigned_ticket.id})
        assert assigned_ticket.status == Ticket.Status.IN_PROGRESS
        assert assigned_ticket.resolution_notes == "Test resolution_notes"


    def test_client_cannot_access_ticket_update_view(
        self,
        client,
        user_client,
        ticket_factory
    ):
        ticket = ticket_factory()

        client.force_login(user_client)

        response = client.get(reverse("tickets:update", kwargs={"pk": ticket.id}))

        assert response.status_code == 403

    @pytest.mark.parametrize("status", CLOSED_STATUSES)
    def test_manager_cannot_access_ticket_update_view_for_closed_statuses(
        self,
        client,
        user_manager,
        ticket_factory,
        status,
    ):
        ticket = ticket_factory(status=status)

        client.force_login(user_manager)

        response = client.get(reverse("tickets:update", kwargs={"pk": ticket.id}))

        assert response.status_code == 403

    @pytest.mark.parametrize("status", DEVELOPER_DISALLOWED_STATUSES)
    def test_developer_cannot_access_ticket_update_view_for_disallowed_status(
        self,
        client,
        user_developer,
        ticket_factory,
        status,
    ):
        assigned_ticket = ticket_factory(status=status)

        client.force_login(user_developer)

        response = client.get(reverse("tickets:update", kwargs={"pk": assigned_ticket.id}))

        assert response.status_code == 403

    def test_developer_cannot_access_update_view_for_other_developer_ticket(
        self,
        client,
        user_developer,
        ticket_factory,
    ):
        unassigned_ticket = ticket_factory(
            assignee=DeveloperFactory.create(), 
            status = Ticket.Status.PENDING_DEVELOPMENT
        )

        client.force_login(user_developer)

        response = client.get(reverse("tickets:update", kwargs={"pk": unassigned_ticket.id}))

        assert response.status_code == 404

    def test_ticket_update_redirects_unauthenticated_user_to_login(
        self,
        client,
        ticket_factory
    ):
        ticket = ticket_factory()
    
        update_url = reverse("tickets:update", kwargs={"pk": ticket.id})

        response = client.get(update_url)

        assert response.status_code == 302
        assert response.url == f'{reverse("users:login")}?next={update_url}'

@pytest.mark.django_db
class TestCommentCreateView:
    def test_client_can_create_comment(
        self,
        client,
        user_client,
        ticket_factory,
    ):
        client_ticket = ticket_factory()

        client.force_login(user_client)

        response = client.post(
            reverse("tickets:comment_create", kwargs={"pk": client_ticket.id}),
            data={
                "body": "Test body",
            },
        )

        comment = Comment.objects.get(ticket=client_ticket, user=user_client)

        assert response.status_code == 302
        assert response.url == reverse("tickets:detail", kwargs={"pk": client_ticket.id})
        assert comment.body == "Test body"

    def test_manager_can_create_comment(
        self,
        client,
        user_manager,
        ticket_factory,
    ):
        any_ticket = ticket_factory()

        client.force_login(user_manager)

        response = client.post(
            reverse("tickets:comment_create", kwargs={"pk": any_ticket.id}),
            data={
                "body": "Test body",
            },
        )

        comment = Comment.objects.get(ticket=any_ticket, user=user_manager)

        assert response.status_code == 302
        assert response.url == reverse("tickets:detail", kwargs={"pk": any_ticket.id})
        assert comment.body == "Test body"

    def test_developer_can_create_comment(
        self,
        client,
        user_developer,
        ticket_factory,
    ):
        assigned_ticket = ticket_factory()

        client.force_login(user_developer)

        response = client.post(
            reverse("tickets:comment_create", kwargs={"pk": assigned_ticket.id}),
            data={
                "body": "Test body",
            },
        )

        comment = Comment.objects.get(ticket=assigned_ticket, user=user_developer)

        assert response.status_code == 302
        assert response.url == reverse("tickets:detail", kwargs={"pk": assigned_ticket.id})
        assert comment.body == "Test body"

    def test_comment_create_get_redirects_to_ticket_detail(
        self,
        client,
        user_client,
        ticket_factory,
    ):
        client_ticket = ticket_factory(creator=user_client)

        client.force_login(user_client)

        response = client.get(
            reverse("tickets:comment_create", kwargs={"pk": client_ticket.id})
        )

        assert response.status_code == 302
        assert response.url == reverse("tickets:detail", kwargs={"pk": client_ticket.id})

    def test_user_cannot_create_comment_with_invalid_data(
        self,
        client,
        user_client,
        ticket_factory,
    ):
        client_ticket = ticket_factory(creator=user_client)

        client.force_login(user_client)

        response = client.post(
            reverse("tickets:comment_create", kwargs={"pk":  client_ticket.id}),
            data={"body": ""},
        )

        assert response.status_code == 200
        assert response.context["comment_form"].errors
        assert Comment.objects.count() == 0


    def test_comment_create_redirects_unauthenticated_user_to_login(
        self,
        client,
        ticket_factory,
    ):
        ticket = ticket_factory()

        comment_url = reverse("tickets:comment_create", kwargs={"pk": ticket.id})

        response = client.post(
            comment_url,
            data={"body": "Test body"},
        )

        assert response.status_code == 302
        assert response.url == f'{reverse("users:login")}?next={comment_url}'
        assert Comment.objects.count() == 0