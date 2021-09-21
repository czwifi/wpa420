from celery import shared_task
#from demoapp.models import Widget
from .wigle import process_wigle, get_wigle_limit
from .models import AccessPoint

@shared_task
def start_import_processing(wifi_import):
	ap_list = AccessPoint.objects.filter(wifi_import__pk=wifi_import)
	process_wigle(ap_list)

@shared_task
def do_wigle_processing():
	processed_count = get_wigle_limit() / 2
	ap_list = AccessPoint.objects.filter(wigle_ssid=None, refresh_attempts=0)
	ap_list_old = ap_list.order_by('wifi_import__added')[:processed_count]
	process_wigle(ap_list_old)
	ap_list_new = ap_list.order_by('-wifi_import__added')[:processed_count]
	process_wigle(ap_list_new)