from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    last_heartbeat = models.DateTimeField(default=timezone.now)
    inactivity_days = models.PositiveIntegerField(default=30)
    vault_released = models.BooleanField(default=False)
    released_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s vault profile"


class Secret(models.Model):
    CATEGORY_CHOICES = [
        ("credentials", "Credentials"),
        ("documents", "Documents"),
        ("finance", "Finance"),
        ("recovery", "Recovery"),
        ("personal", "Personal"),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="secrets")
    title = models.CharField(max_length=180)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default="credentials")
    encrypted_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class Nominee(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="nominees")
    name = models.CharField(max_length=160)
    email = models.EmailField()
    relationship = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.email})"


class ReleaseEvent(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="release_events")
    triggered_at = models.DateTimeField(default=timezone.now)
    nominee_count = models.PositiveIntegerField(default=0)
    secret_count = models.PositiveIntegerField(default=0)
    reason = models.CharField(max_length=255)

    class Meta:
        ordering = ["-triggered_at"]

    def __str__(self):
        return f"Release for {self.owner.username} at {self.triggered_at:%Y-%m-%d %H:%M}"
