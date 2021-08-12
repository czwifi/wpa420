from django.core.management.base import BaseCommand, CommandError
from wifi.models import AccessPoint, WifiImport
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Resets timestamps to align with import times'

    def handle(self, *args, **options):
        access_points = AccessPoint.objects.all()
        for access_point in access_points:
            access_point.wifi_import = None
            access_point.save()
            print(f"Updated {access_point}")
        wifi_imports = WifiImport.objects.all()
        for wifi_import in wifi_imports:
        	wifi_import.delete()
        print("Done")