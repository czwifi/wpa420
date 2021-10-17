from celery import shared_task

from .handlers import generate_wifi_list_json
from .wigle import process_wigle, get_wigle_limit
from .models import AccessPoint


@shared_task
def start_import_processing(wifi_import):
	ap_list = AccessPoint.objects.filter(wifi_import__pk=wifi_import)
	try:
		process_wigle(ap_list)
	except:
		pass
	generate_wifi_list_json()

@shared_task
def do_wigle_processing():
	processed_count = get_wigle_limit() / 2
	ap_list = AccessPoint.objects.filter(wigle_ssid=None, refresh_attempts=0)
	try:
		ap_list_old = ap_list.order_by('wifi_import__added')[:processed_count]
		process_wigle(ap_list_old, True)
		ap_list_new = ap_list.order_by('-wifi_import__added')[:processed_count]
		process_wigle(ap_list_new, True)
	except:
		pass
	generate_wifi_list_json()

@shared_task
def assign_wps(wps_keys):
	for bssid in wps_keys:
		try:
			ap = AccessPoint.objects.get(bssid=bssid)
			ap.wps_enabled = True
			ap.wps = wps_keys[bssid]
			ap.save()
		except:
			pass
	generate_wifi_list_json()