from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .encryption import decrypt_text
from .models import Nominee, ReleaseEvent, Secret, UserProfile


def profile_is_inactive(profile):
    deadline = profile.last_heartbeat + timedelta(days=profile.inactivity_days)
    return timezone.now() >= deadline


def release_vault_for_profile(profile, reason="Inactivity threshold reached"):
    owner = profile.user
    secret_count = Secret.objects.filter(owner=owner).count()
    nominee_count = Nominee.objects.filter(owner=owner).count()

    if profile.vault_released:
        return {
            "released": False,
            "reason": "Vault was already released.",
            "emails_sent": 0,
            "secret_count": secret_count,
            "nominee_count": nominee_count,
        }

    if not profile_is_inactive(profile):
        return {
            "released": False,
            "reason": "User is still inside the heartbeat window.",
            "emails_sent": 0,
            "secret_count": secret_count,
            "nominee_count": nominee_count,
        }

    secrets = list(Secret.objects.filter(owner=owner))
    nominees = list(Nominee.objects.filter(owner=owner))
    vault_body = _build_release_message(owner, secrets)
    emails_sent = 0

    with transaction.atomic():
        for nominee in nominees:
            send_mail(
                subject=f"Digital Vault Released: {owner.username}",
                message=(
                    f"Hello {nominee.name},\n\n"
                    f"You were named as a nominee for {owner.username}'s Digital Inheritance Vault.\n"
                    "The vault has been released because the account passed its inactivity threshold.\n\n"
                    f"{vault_body}\n\n"
                    "Security note: this MVP emails contents for demonstration. A production version "
                    "should send a verified one-time access link instead."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[nominee.email],
                fail_silently=False,
            )
            emails_sent += 1

        profile.vault_released = True
        profile.released_at = timezone.now()
        profile.save(update_fields=["vault_released", "released_at", "updated_at"])
        ReleaseEvent.objects.create(
            owner=owner,
            nominee_count=len(nominees),
            secret_count=len(secrets),
            reason=reason,
        )

    return {
        "released": True,
        "reason": reason,
        "emails_sent": emails_sent,
        "secret_count": len(secrets),
        "nominee_count": len(nominees),
    }


def check_all_inactive_profiles():
    results = []
    for profile in UserProfile.objects.select_related("user").filter(vault_released=False):
        if profile_is_inactive(profile):
            result = release_vault_for_profile(profile)
            result["username"] = profile.user.username
            results.append(result)
    return results


def _build_release_message(owner, secrets):
    if not secrets:
        return "No secrets were stored in the vault."

    lines = [f"Vault contents for {owner.username}:"]
    for index, secret in enumerate(secrets, start=1):
        lines.extend(
            [
                "",
                f"{index}. {secret.title}",
                f"Category: {secret.get_category_display()}",
                decrypt_text(secret.encrypted_content),
            ]
        )
    return "\n".join(lines)
