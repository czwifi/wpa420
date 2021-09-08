from django.shortcuts import render
from django.http import JsonResponse
from django.utils.crypto import get_random_string

from .models import AccessPoint, WifiImport, WifiUserApiKey

class ImportResults:
	def __init__(self, to_add, new):
		self.to_add = to_add
		self.new = new
		self.skipped = to_add - new

#TODO: handle semicolons in ssids?
def process_import(import_text, wifi_author):
    lines = import_text.splitlines()
    wifi_import = WifiImport(author=wifi_author)
    wifi_import.save()
    access_points = []
    for line in lines:
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
    new = AccessPoint.objects.count() - total
    return ImportResults(to_add, new)

def generate_v1_ap_array(ap_list):
    networks = []
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
        }
        networks.append(network)
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