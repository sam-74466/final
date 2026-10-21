from django.core.management.base import BaseCommand

from vault.services import check_all_inactive_profiles


class Command(BaseCommand):
    help = "Checks inactive vault profiles and releases eligible vaults to nominees."

    def handle(self, *args, **options):
        results = check_all_inactive_profiles()
        if not results:
            self.stdout.write(self.style.SUCCESS("No inactive vaults found."))
            return

        for result in results:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Released {result['username']}: "
                    f"{result['secret_count']} secret(s), "
                    f"{result['nominee_count']} nominee(s), "
                    f"{result['emails_sent']} email(s)."
                )
            )
