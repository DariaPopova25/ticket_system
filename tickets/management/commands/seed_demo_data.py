from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from tickets.models import Comment, Ticket

User = get_user_model()


class Command(BaseCommand):
    help = "Create demo users and demo ticket data"

    def handle(self, *args, **options):
        client, _ = User.objects.update_or_create(
            email="client_demo@example.com",
            defaults={
                "username": "client_demo",
                "role": User.Role.CLIENT,
            },
        )
        client.set_password("demo12345")
        client.save()

        manager, _ = User.objects.update_or_create(
            email="manager_demo@example.com",
            defaults={
                "username": "manager_demo",
                "role": User.Role.MANAGER,
            },
        )
        manager.set_password("demo12345")
        manager.save()

        developer, _ = User.objects.update_or_create(
            email="developer_demo@example.com",
            defaults={
                "username": "developer_demo",
                "role": User.Role.DEVELOPER,
            },
        )
        developer.set_password("demo12345")
        developer.save()

        ticket, _ = Ticket.objects.update_or_create(
            title="Demo ticket",
            creator=client,
            defaults={
                "assignee": developer,
                "status": Ticket.Status.PENDING_REVIEW,
                "priority": Ticket.Priority.HIGH,
                "description": "Client demo description",
                "manager_notes": "Manager checked and assigned ticket",
                "resolution_notes": "Developer fixed the issue",
            },
        )

        Comment.objects.get_or_create(
            ticket=ticket,
            user=client,
            body="Please help with this bug",
        )
        Comment.objects.get_or_create(
            ticket=ticket,
            user=manager,
            body="Assigned to developer",
        )
        Comment.objects.get_or_create(
            ticket=ticket,
            user=developer,
            body="Fix completed, ready for review",
        )

        self.stdout.write(self.style.SUCCESS("Demo data created"))
