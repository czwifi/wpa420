from wifi.models import AccessPoint

from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
import requests
import json
import os

class BadWigleApiData(Exception):
    pass

class TooManyQueriesToday(Exception):
    pass

class TooManyLocalRequests(Exception):
    pass

def get_wigle_limit():
    return int(os.getenv('WIGLE_LIMIT',10))

def check_too_many_aps():
    wigle_limit = get_wigle_limit()
    ap_count = AccessPoint.objects.filter(location_refreshed__gte= datetime.now() - timedelta(hours = 24)).count()
    if ap_count > wigle_limit:
        raise TooManyLocalRequests

def refresh_ap(ap, wigle_name, wigle_key):
    check_too_many_aps()

    wigle_info = requests.get(f'https://api.wigle.net/api/v2/network/detail', params={'netid': ap.bssid.lower()}, auth=HTTPBasicAuth(wigle_name, wigle_key))
    if wigle_info.status_code != 200 and wigle_info.status_code != 404:
        raise BadWigleApiData
    wigle_info = json.loads(wigle_info.text)
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
        ap.encryption = None if ap_info['encryption'] == 'unknown' else ap_info['encryption']
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

def process_wigle(ap_list):
    wigle_name = os.getenv('WIGLE_NAME','')
    wigle_key = os.getenv('WIGLE_KEY','')
    if wigle_name == '' or wigle_key == '':
        return
    for ap in ap_list:
        refresh_ap(ap, wigle_name, wigle_key)