from django.shortcuts import render
from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.core.cache import cache

from datetime import datetime

from .models import AccessPoint, WifiImport, WifiUserApiKey

class ImportResults:
	def __init__(self, to_add, new):
		self.to_add = to_add
		self.new = new
		self.skipped = to_add - new

#TODO: handle semicolons in ssids?
def process_import(import_file, wifi_author):
    lines = import_file.readlines()
    wifi_import = WifiImport(author=wifi_author)
    wifi_import.save()
    access_points = []
    for line in lines:
        #workaround because the wifi standard doesn't specify an encoding
        try:
            line = line.decode('utf-8')
        except:
            line = line.decode('cp1250')

        #avoid trailing newlines caused by the file itself
        #TODO: check if the number of semicolons matches the expected amount and tell the user if it doesn't
        if len(line) > 0 and line[-1] == '\n':
            line = line[:-1]

        networkInfo = line.split(";")
        access_point = AccessPoint(
            latitude = None if networkInfo[0] == "null" else networkInfo[0],
            longitude = None if networkInfo[1] == "null" else networkInfo[1],
            bssid = networkInfo[2].upper(),
            ssid = networkInfo[3],
            password = networkInfo[4],
            author = wifi_author,
            wps_enabled = False,
            wifi_import = wifi_import
        )
        access_points.append(access_point)
    total = AccessPoint.objects.count()
    to_add = len(access_points)
    AccessPoint.objects.bulk_create(access_points, ignore_conflicts=True)
    cache.set('data_wifi_list_json', None, None)
    new = AccessPoint.objects.count() - total
    return ImportResults(to_add, new)

def generate_v1_ap_array(ap_list):
    networks = []
    print(datetime.now())
    for ap in ap_list:
        network = {
            "MAC": ap.bssid,
            "SSID": ap.ssid,
            "WPS": str(ap.wps),
            "_id": str(ap.pk),
            "author": ap.wifi_import.author.user.username,
            "password": ap.password,
            "position": [
                "null" if ap.latitude is None else str(ap.latitude),
                "null" if ap.longitude is None else str(ap.longitude),
            ],
            "status": "0",
            "timestamp": ap.wifi_import.added,
            "marker_color": ap.wifi_import.author.marker_color,
        }
        networks.append(network)
    print(datetime.now())
    return networks


def generate_api_key(wifi_user, description):
    api_key = WifiUserApiKey(
        key = get_random_string(length=32),
        wifi_user = wifi_user,
        description = description
    )
    api_key.save()
    return api_key


def render_generic_error(request, error_text):
	return render(request, "account/error.html", {'error': error_text})

def render_json_error(request, error_text):
    response = {"success": False, "error_text": error_text}
    return JsonResponse(response, safe=False)