from django.core.management.base import BaseCommand, CommandError
from wifi.models import AccessPoint
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Resets timestamps to align with import times'

    def handle(self, *args, **options):
        access_points = AccessPoint.objects.order_by('added')
        last_timestamp = access_points[0].added
        for access_point in access_points:
        	start = last_timestamp.replace(second=0)
        	end = start + timedelta(minutes=1)
        	if start <= access_point.added <= end:
        		print(f"Updating {access_point}")
        		access_point.added = last_timestamp
        		access_point.save()
        	else:
        		print(f"New import: {access_point}")
        		last_timestamp = access_point.added
        print("Done")