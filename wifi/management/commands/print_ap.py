from django.core.management.base import BaseCommand, CommandError
from wifi.models import AccessPoint, WifiImport
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
import requests
import json

class Command(BaseCommand):
    help = 'Resets timestamps to align with import times'

    def add_arguments(self, parser):
        parser.add_argument('bssids', nargs='+')

    def handle(self, *args, **options):
        for bssid in options['bssids']:
            print("==========================")
            ap = AccessPoint.objects.get(bssid=bssid)
            temp = vars(ap)
            for item in temp:
                print(item, ':', temp[item])