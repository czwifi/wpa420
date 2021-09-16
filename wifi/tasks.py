from celery import shared_task
#from demoapp.models import Widget
from .wigle import process_wigle
from .models import AccessPoint

@shared_task
def start_import_processing(wifi_import):
	ap_list = AccessPoint.objects.filter(wifi_import__pk=wifi_import)
	process_wigle(ap_list)