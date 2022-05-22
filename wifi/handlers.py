from django.shortcuts import render
from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.core.cache import cache

from datetime import datetime

from .models import WifiUserApiKey, AccessPoint

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
            "WPS_enabled": ap.wps_enabled,
        }
        networks.append(network)
    print(datetime.now())
    return networks

def generate_wifi_list_json():
    ap_list = AccessPoint.objects.prefetch_related('wifi_import__author__user').order_by('bssid')
    networks = generate_v1_ap_array(ap_list)
    response = JsonResponse(networks, safe=False)
    cache.set('data_wifi_list_json', response, None)
    return response


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