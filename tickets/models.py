from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db import models



class Ticket(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        PENDING_DEVELOPMENT = "pending_development", "Pending development"
        IN_PROGRESS = "in_progress", "In progress"
        PENDING_REVIEW = "pending_review", "Pending review"
        DONE = "done", "Done"
        CANCELLED = "cancelled", "Cancelled"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"


    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_tickets",
    )

    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets",
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.NEW,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority,
        blank=True,
        default="",
    )

    description = models.TextField(validators=[MaxLengthValidator(10000)])
    manager_notes = models.TextField(validators=[MaxLengthValidator(2500)], blank=True, default="")
    resolution_notes = models.TextField(validators=[MaxLengthValidator(5000)], blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering=["-created_at"]

    def __str__(self):
        return f"Ticket #{self.pk}: {self.title}"
    
    def clean(self):
        super().clean()
        errors = {}
        
        statuses_requiring_assignee_and_priority = {
            self.Status.PENDING_DEVELOPMENT,
            self.Status.IN_PROGRESS,
            self.Status.PENDING_REVIEW,
            self.Status.DONE,
        }

        if self.creator_id and self.creator.role != self.creator.Role.CLIENT:
            errors["creator"] = "Creator must have client role."

        if self.assignee_id and self.assignee.role != self.assignee.Role.DEVELOPER:
            errors["assignee"] = "Assignee must have developer role."

        if self.status in statuses_requiring_assignee_and_priority and self.assignee_id is None:
            errors["assignee"] = "Assignee is required for this status."

        if self.status in statuses_requiring_assignee_and_priority and not self.priority:
            errors["priority"] = "Priority is required for this status."

        if errors:
            raise ValidationError(errors)
