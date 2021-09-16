from django.core.management.base import BaseCommand, CommandError
from wifi.models import AccessPoint
from wifi.wigle import process_wigle

class Command(BaseCommand):
    help = 'Loads Wigle info for all networks'
    #print(wigle_info)

    def handle(self, *args, **options):
        ap_list = AccessPoint.objects.filter(wigle_ssid=None, refresh_attempts=0).order_by('location_refreshed')
        process_wigle(ap_list)