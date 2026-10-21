from django.contrib import admin

from .encryption import decrypt_text
from .models import Nominee, ReleaseEvent, Secret, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "last_heartbeat", "inactivity_days", "vault_released", "released_at")
    list_filter = ("vault_released",)
    search_fields = ("user__username", "user__email")


@admin.register(Secret)
class SecretAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "category", "decrypted_preview", "updated_at")
    list_filter = ("category",)
    search_fields = ("title", "owner__username")
    readonly_fields = ("decrypted_content",)

    def decrypted_preview(self, obj):
        value = self.decrypted_content(obj)
        return value[:80] + ("..." if len(value) > 80 else "")

    def decrypted_content(self, obj):
        try:
            return decrypt_text(obj.encrypted_content)
        except Exception:
            return "Unable to decrypt with the current vault key."


@admin.register(Nominee)
class NomineeAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "relationship", "owner", "is_verified")
    search_fields = ("name", "email", "owner__username")


@admin.register(ReleaseEvent)
class ReleaseEventAdmin(admin.ModelAdmin):
    list_display = ("owner", "triggered_at", "nominee_count", "secret_count", "reason")
    search_fields = ("owner__username", "reason")
