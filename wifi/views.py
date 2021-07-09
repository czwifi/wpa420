from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count

from .models import AccessPoint, WifiUser
from .forms import UploadFileForm, WigleForm

import json
from requests.auth import HTTPBasicAuth
import requests
from datetime import datetime
import hashlib

def index(request):
    return redirect('map')

@login_required
def map(request):
    ap_list = AccessPoint.objects.all()
    filtered_ap_list = AccessPoint.objects.exclude(latitude=None).prefetch_related('author__user')
    user_list = WifiUser.objects.all().select_related('user').annotate(Count('accesspoint')).order_by('-accesspoint__count')
    provider_list = []
    providers = ['UPC', 'Vodafone', 'O2', 'MujO2', 'PODA', 'TP-LINK', 'ASUS']
    for provider in providers:
        provider_list.append({'provider':provider, 'ap_count': AccessPoint.objects.filter(ssid__startswith=provider).count()})
    provider_list.sort(key=lambda x: x['ap_count'], reverse=True)
    template = loader.get_template('map.html')
    context = {
        'ap_list': ap_list,
        'filtered_ap_list': filtered_ap_list,
        'leaderboards': user_list,
        'provider_list': provider_list,
    }
    return HttpResponse(template.render(context, request))

@login_required
def upload_form(request):
    form = UploadFileForm(request.POST, request.FILES)
    if request.method == 'POST':
        if form.is_valid():
            #TODO: create wifiuser if does not exist
            wifi_author = WifiUser.objects.get(user=request.user)
            #TODO: handle semicolons in ssids?
            lines = request.FILES['file'].read().decode('utf-8').splitlines()
            print(lines)
            total = skipped = 0
            for line in lines:
                total += 1
                networkInfo = line.split(";")
                if AccessPoint.objects.filter(bssid=networkInfo[2].upper()).exists():
                    skipped += 1
                    continue
                access_point = AccessPoint(
                    latitude = None if networkInfo[0] == "null" else networkInfo[0],
                    longitude = None if networkInfo[1] == "null" else networkInfo[1],
                    bssid = networkInfo[2].upper(),
                    ssid = networkInfo[3],
                    password = networkInfo[4],
                    author = wifi_author,
                    wps_enabled = False,
                )
                access_point.save()
            context = {'total': total, 'skipped': skipped, 'new': total - skipped}
            return render(request, 'upload_complete.html', context)
        else:
            field_errors = [ (field.label, field.errors) for field in form] 
            print(field_errors)
    else:
        context = {'form': form}
        return render(request, 'upload.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def upload_form_json(request):
    form = UploadFileForm(request.POST, request.FILES)
    context = {'form': form}
    if request.method == 'POST':
        if form.is_valid():
            lines = request.FILES['file'].read().decode('utf-8')
            json_file = json.loads(lines)
            for network in json_file:
                if AccessPoint.objects.filter(bssid=network['MAC'].upper()).exists() or not User.objects.filter(username=network["author"]).exists():
                    continue
                access_point = AccessPoint(
                    bssid = network['MAC'].upper(),
                    ssid = network["SSID"],
                    wps = network["WPS"],
                    author = User.objects.get(username=network["author"]),
                    password = network["password"],
                    latitude = None if network["position"][0] == "null" else network["position"][0],
                    longitude = None if network["position"][1] == "null" else network["position"][1],
                    wps_enabled = False,
                )
                access_point.added = network["timestamp"]
                print(network["timestamp"])
                print(access_point.added)
                access_point.save()
            return HttpResponse("yes")
        else:
            field_errors = [ (field.label, field.errors) for field in form] 
            print(field_errors)
    else:
        return render(request, 'upload.html', context)

def wifi_list_json(request):
    networks = []
    ap_list = AccessPoint.objects.all().prefetch_related('author__user')
    for ap in ap_list:
        network = {
            "MAC": ap.bssid,
            "SSID": ap.ssid,
            "WPS": "null",
            "_id": str(ap.pk),
            "author": ap.author.user.username,
            "password": ap.password,
            "position": [
                "null" if ap.latitude is None else str(ap.latitude),
                "null" if ap.longitude is None else str(ap.longitude),
            ],
            "status": "0",
            "timestamp": ap.added,
        }
        networks.append(network)
    return JsonResponse(networks, safe=False)

def api_dbhash(request):
    # since this is only used for validation whether the db needs update
    # we will return the hash of the latest timestamp for now
    # as computing the hash of the entire db would be too costly
    return HttpResponse(hashlib.md5(AccessPoint.objects.order_by('-added')[0].added.strftime('%Y-%m-%dT%H:%M:%S%z').encode('utf-8')).hexdigest())

@login_required
def refresh_location(request):
    form = WigleForm(request.POST, request.FILES)
    context = {'form': form}
    if request.method == 'POST':
        if form.is_valid():
            attempts = updates = 0
            ap_list = AccessPoint.objects.filter(author=WifiUser.objects.get(user=request.user), latitude=None, longitude=None).order_by('location_refreshed')
            for ap in ap_list:
                wigle_info = requests.get(f'https://api.wigle.net/api/v2/network/detail', params={'netid': ap.bssid.lower()}, auth=HTTPBasicAuth(form.cleaned_data['wigle_name'], form.cleaned_data['wigle_key']))
                if wigle_info.status_code != 200:
                    return HttpResponse("bad wigle api data")
                wigle_info = json.loads(wigle_info.text)
                print(wigle_info)
                if wigle_info['success'] is False and wigle_info['message'] == 'too many queries today.':
                    break
                ap.location_refreshed = datetime.now()
                attempts += 1
                if wigle_info['success'] is True:
                    ap.latitude = wigle_info['results'][0]['trilat']
                    ap.longitude = wigle_info['results'][0]['trilong']
                    updates += 1
                ap.save()
                print(wigle_info)
            context = {
                'attempts': attempts,
                'updates': updates,
            }
            return render(request, 'refresh_complete.html', context)
        else:
            return HttpResponse("something went wrong")
    else:
        return render(request, 'refresh.html', context)