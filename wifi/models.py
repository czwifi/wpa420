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
    def __str__(self):
        return self.user.username

class WifiUserApiKey(models.Model):
	key = models.CharField(max_length=32, db_index=True, unique=True)
	wifi_user = models.ForeignKey(
		WifiUser,
		on_delete=models.CASCADE,
		db_index=True,
	)
	description = models.CharField(max_length=255)
	created = models.DateTimeField('date created', default=datetime.now)
	used = models.DateTimeField('date used', default=datetime.now)
	def __str__(self):
		return f"{self.wifi_user} : {self.description}"

class WifiUserInvite(models.Model):
	invite_code = models.CharField(max_length=32, db_index=True, unique=True)
	author = models.ForeignKey(
		WifiUser,
		on_delete=models.CASCADE,
		db_index=True,
		related_name='invites',
	)
	invitee = models.ForeignKey(
		WifiUser,
		null=True, blank=True,
		on_delete=models.CASCADE,
		db_index=True,
		related_name='invited_by',
	)
	generated = models.DateTimeField('date generated', default=datetime.now)
	def __str__(self):
		return f"{self.author} : {self.invitee}"

class WifiImport(models.Model):

	class Source(models.TextChoices):
		WARDRIVING = 'wardriving', _('Wardriving')
		MANUAL = 'manual', _('Manual Entry')
		CLOUD = 'cloud', _('Cloud')

	author = models.ForeignKey(
		WifiUser,
		on_delete=models.CASCADE,
		db_index=True,
	)

	source = models.CharField(
		max_length=10, 
		null=True, blank=True,
		choices=Source.choices, 
		#default=Frequency.FREQ_2_4G,
	)

	added = models.DateTimeField('date added', default=datetime.now)
	delete_unlocateable = models.BooleanField(default=False)

	def __str__(self):
		return f"{self.author} - {self.added}"
    
class AccessPoint(models.Model):

	class Encryption(models.TextChoices):
		WEP = 'wep', _('WEP')
		WPA = 'wpa', _('WPA')
		WPA2 = 'wpa2', _('WPA2')
		WPA3 = 'wpa3', _('WPA3')
		NONE = 'none', _('None')

	class Frequency(models.TextChoices):
		FREQ_2_4G = '2_4G', _('2.4 GHz')
		FREQ_5G = '5G', _('5 GHz')

	ssid = models.CharField(max_length=32, db_index=True)
	bssid = models.CharField(unique=True, max_length=17, db_index=True)
	wps = models.CharField(max_length=8, blank=True)
	wps_enabled = models.BooleanField()
	latitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True, db_index=True)
	longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True, db_index=True)
	password = models.CharField(max_length=63)
	location_refreshed = models.DateTimeField('date location refreshed', blank=True, null=True)
	refresh_attempts = models.IntegerField(default=0, db_index=True)
	frequency = models.CharField(
		max_length=4, 
		null=True, blank=True,
		choices=Frequency.choices, 
		#default=Frequency.FREQ_2_4G,
	)
	wifi_import = models.ForeignKey(
		WifiImport,
		on_delete=models.CASCADE,
		db_index=True,
		null=True, blank=True,
	)

	#Deprecated fields
	## Should be taken from import
	author = models.ForeignKey(
		WifiUser,
		on_delete=models.CASCADE,
		db_index=True,
	)
	added = models.DateTimeField('date added', default=datetime.now)

	#Wigle Data
	wigle_ssid = models.CharField(max_length=32, db_index=True, blank=True, null=True)
	channel = models.IntegerField(blank=True, null= True)
	wigle_qos = models.IntegerField(blank=True, null= True)
	city = models.CharField(blank=True, null=True, max_length=255)
	country = models.CharField(blank=True, null=True, max_length=255)
	wigle_firsttime = models.DateTimeField('added to wigle', blank=True, null=True)
	wigle_lasttime = models.DateTimeField('last seen on wigle', blank=True, null=True)
	wigle_lastupdt = models.DateTimeField('last updated on wigle', blank=True, null=True)
	housenumber = models.CharField(blank=True, null=True, max_length=255)
	name = models.CharField(blank=True, null=True, max_length=255)
	postalcode = models.CharField(blank=True, null=True, max_length=255)
	region = models.CharField(blank=True, null=True, max_length=255)
	road = models.CharField(blank=True, null=True, max_length=255)
	wigle_type = models.CharField(blank=True, null=True, max_length=255)
	encryption = models.CharField(
		max_length=4, 
		null=True, blank=True,
		choices=Encryption.choices, 
		#default=Encryption.WPA2,
	)
	def __str__(self):
		return f"{self.bssid} - {self.ssid}"