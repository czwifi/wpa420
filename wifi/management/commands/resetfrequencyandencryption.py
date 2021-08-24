from django.core.management.base import BaseCommand, CommandError
from wifi.models import AccessPoint

class Command(BaseCommand):
    help = 'Resets frequency and encryption'

    def handle(self, *args, **options):
        access_points = AccessPoint.objects.exclude(frequency=None).all()
        for access_point in access_points:
            access_point.encryption = None
            access_point.frequency = None
            access_point.save()
            print(f"Updated {access_point}")
        print("Done")