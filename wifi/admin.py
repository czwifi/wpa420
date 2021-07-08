from django.contrib import admin
from .models import AccessPoint, WifiUser

# Register your models here.
admin.site.register(AccessPoint)
admin.site.register(WifiUser)