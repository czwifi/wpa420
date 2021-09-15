from django.core.management.base import BaseCommand, CommandError
from wifi.models import AccessPoint
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Resets timestamps to align with import times'

    def handle(self, *args, **options):
        access_points = AccessPoint.objects.filter(wps_enabled=False).exclude(wps=None).exclude(wps='').exclude(wps='null')
        for access_point in access_points:
            print(access_point.wps)
            print(access_point.wps_enabled)
            access_point.wps_enabled = True
            access_point.save()
        print("Done")