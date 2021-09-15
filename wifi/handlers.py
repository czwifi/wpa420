from django.shortcuts import render
from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.core.cache import cache

from datetime import datetime
import csv
import io

from .models import AccessPoint, WifiImport, WifiUserApiKey

class ImportResults:
    def __init__(self, to_add, new, additional):
        self.to_add = to_add
        self.new = new
        self.skipped = to_add - new
        self.additional = additional
        self.success = True

class ImportFailure:
    def __init__(self, failure_reason):
        self.success = False
        self.failure_reason = failure_reason

class ProcessedImport:
    def __init__(self, access_points, additional):
        self.access_points = access_points
        self.additional = additional

def process_import(import_file, wifi_author):
    lines = import_file.readlines()
    first_line = decode_line(lines[0])
    import_file.seek(0)

    if first_line is False:
        return ImportFailure("Provided import file is not a valid text file.")

    wifi_import = WifiImport(author=wifi_author)
    wifi_import.save()

    if '"Date";"BSSID";"ESSID";"WPS PIN";"WPA PSK"' in first_line:
        processed_import = process_oneshot_import(import_file, wifi_import)
    elif first_line.count(';') == 4:
        processed_import = process_txt_import(lines, wifi_import)
    else:
        wifi_import.delete()
        return ImportFailure("Unsupported import file.")

    access_points = processed_import.access_points
    total = AccessPoint.objects.count()
    to_add = len(access_points)
    AccessPoint.objects.bulk_create(access_points, ignore_conflicts=True, batch_size=1000)
    cache.set('data_wifi_list_json', None, None)
    new = AccessPoint.objects.count() - total
    return ImportResults(to_add, new, processed_import.additional)

def process_oneshot_import(import_file, wifi_import):
    access_points = []
    with io.TextIOWrapper(import_file, encoding='utf-8') as text_file:
        reader = csv.DictReader(text_file, delimiter=';')

        for networkInfo in reader:
            access_point = AccessPoint(
                latitude = None,
                longitude = None,
                bssid = networkInfo['BSSID'].upper(),
                ssid = networkInfo['ESSID'],
                password = networkInfo['WPA PSK'],
                author = wifi_import.author,
                wps_enabled = True,
                wps = networkInfo['WPS PIN'],
                wifi_import = wifi_import
            )
            access_points.append(access_point)

    return ProcessedImport(access_points, "")

#TODO: handle semicolons in ssids?
def process_txt_import(lines, wifi_import):
    access_points = []
    additional = ""
    i = 0
    for line in lines:
        i += 1
        line = decode_line(line)
        if line is False:
            additional += f"Unable to decode line {i}, skipping; "
            continue

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
            author = wifi_import.author,
            wps_enabled = False,
            wifi_import = wifi_import
        )
        access_points.append(access_point)
    return ProcessedImport(access_points, additional)

def decode_line(line):
    #workaround because the wifi standard doesn't specify an encoding
    try:
        return line.decode('utf-8')
    except:
        try:
            return line.decode('cp1250')
        except:
            return False

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