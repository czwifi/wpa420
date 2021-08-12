from django.core.management.base import BaseCommand, CommandError
from wifi.models import AccessPoint, WifiImport
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Resets timestamps to align with import times'

    def handle(self, *args, **options):
        access_points = AccessPoint.objects.filter(wifi_import=None).order_by('added')
        for access_point in access_points:
            wifi_import = None
            try:
                wifi_import = WifiImport.objects.get(author=access_point.author, added=access_point.added)
            except:
                wifi_import = WifiImport(author=access_point.author, added=access_point.added)
                wifi_import.save()
            access_point.wifi_import = wifi_import
            access_point.save()
            print(f"Updated {access_point}")
        print("Done")