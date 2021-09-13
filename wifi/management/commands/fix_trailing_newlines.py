from django.core.management.base import BaseCommand, CommandError
from wifi.models import AccessPoint
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Resets timestamps to align with import times'

    def handle(self, *args, **options):
        access_points = AccessPoint.objects.all()
        for access_point in access_points:
            if len(access_point.password) > 0 and access_point.password[-1] == '\n':
                print(access_point)
                access_point.password = access_point.password[:-1]
                access_point.save()
        print("Done")