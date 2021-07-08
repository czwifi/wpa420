from django.db import models
from django.conf import settings
from django.utils.translation import gettext as _

from datetime import datetime

# Create your models here.
class WifiUser(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_index=True,
    )
    marker_color = models.CharField(default='ffffff', max_length=6)
    
class AccessPoint(models.Model):

	class Encryption(models.TextChoices):
		WEP = 'WEP', _('WEP')
		WPA = 'WPA', _('WPA')
		WPA2 = 'WPA2', _('WPA2')
		WPA3 = 'WPA3', _('WPA3')

	class Frequency(models.TextChoices):
		FREQ_2_4G = '2_4G', _('2.4 GHz')
		FREQ_5G = '5G', _('5 GHz')

	ssid = models.CharField(max_length=32, db_index=True)
	bssid = models.CharField(unique=True, max_length=17, db_index=True)
	wps = models.CharField(max_length=8, blank=True)
	wps_enabled = models.BooleanField()
	author = models.ForeignKey(
		WifiUser,
		on_delete=models.CASCADE,
		null=True, blank=True,
		db_index=True,
	)
	latitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True, db_index=True)
	longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True, db_index=True)
	password = models.CharField(max_length=63)
	added = models.DateTimeField('date added', default=datetime.now)
	location_refreshed = models.DateTimeField('date location refreshed', blank=True, null=True, default=datetime.now)
	encryption = models.CharField(
		max_length=4, 
		choices=Encryption.choices, 
		default=Encryption.WPA2,
	)
	frequency = models.CharField(
		max_length=4, 
		choices=Frequency.choices, 
		default=Frequency.FREQ_2_4G,
	)