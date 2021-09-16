from django.core.management.base import BaseCommand, CommandError
from wifi.models import AccessPoint, WifiImport
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
import requests
import json
import os

class BadWigleApiData(Exception):
    pass

class TooManyQueriesToday(Exception):
    pass

class Command(BaseCommand):
    help = 'Loads Wigle info for all networks'

    def refresh_ap(self, ap, wigle_name, wigle_key):
        wigle_info = requests.get(f'https://api.wigle.net/api/v2/network/detail', params={'netid': ap.bssid.lower()}, auth=HTTPBasicAuth(wigle_name, wigle_key))
        print(wigle_info.text)
        if wigle_info.status_code != 200 and wigle_info.status_code != 404:
            raise BadWigleApiData
        wigle_info = json.loads(wigle_info.text)
        #print(wigle_info)
        if wigle_info['success'] is False and wigle_info['message'] == 'too many queries today.':
            raise TooManyQueriesToday
        ap.location_refreshed = datetime.now()
        ap.refresh_attempts += 1
        if wigle_info['success'] is True:
            ap_info = wigle_info['results'][0]

            ap.latitude = ap_info['trilat']
            ap.longitude = ap_info['trilong']
            ap.channel = ap_info['channel']
            ap.city = ap_info['city']
            ap.country = ap_info['country']
            ap.encryption = ap_info['encryption']
            ap.wigle_firsttime = ap_info['firsttime']
            ap.housenumber = ap_info['housenumber']
            ap.wigle_lasttime = ap_info['lasttime']
            ap.wigle_lastupdt = ap_info['lastupdt']
            ap.name = ap_info['name']
            ap.postalcode = ap_info['postalcode']
            ap.region = ap_info['region']
            ap.road = ap_info['road']
            ap.wigle_ssid = ap_info['ssid']
            ap.wigle_qos = ap_info['qos']
            ap.wigle_type = ap_info['type']
            if ap.frequency == None:
                ap.frequency = AccessPoint.Frequency.FREQ_2_4G if ap.channel <= 14 else AccessPoint.Frequency.FREQ_5G
        ap.save()
        print(f"{ap.bssid}")
        #print(wigle_info)

    def handle(self, *args, **options):
        wigle_name = os.getenv('WIGLE_NAME','')
        wigle_key = os.getenv('WIGLE_KEY','')
        ap_list = AccessPoint.objects.filter(wigle_ssid=None, refresh_attempts=0).order_by('location_refreshed')
        for ap in ap_list:
            self.refresh_ap(ap, wigle_name, wigle_key)