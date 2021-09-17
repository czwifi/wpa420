from celery import shared_task
#from demoapp.models import Widget
from .wigle import process_wigle
from .models import AccessPoint

@shared_task
def start_import_processing(wifi_import):
	ap_list = AccessPoint.objects.filter(wifi_import__pk=wifi_import)
	process_wigle(ap_list)

@shared_task
def do_wigle_processing():
	ap_list = AccessPoint.objects.filter(wigle_ssid=None, refresh_attempts=0).order_by('-wifi_import__added')
	process_wigle(ap_list)