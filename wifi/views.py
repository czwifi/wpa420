from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils.crypto import get_random_string

from .models import AccessPoint, WifiUser, WifiUserInvite
from .forms import UploadFileForm, WigleForm, RegisterForm, SettingsForm

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
    wifi_author = WifiUser.objects.get(user=request.user)
    form = UploadFileForm(request.POST or None, request.FILES or None, initial={'import_as': wifi_author})
    if request.method == 'POST':
        if form.is_valid():
            if request.user.is_superuser and form.cleaned_data['import_as'] is not None:
                wifi_author = form.cleaned_data['import_as']
            #TODO: create wifiuser if does not exist
            #TODO: handle semicolons in ssids?
            lines = request.FILES['file'].read().decode('utf-8').splitlines()
            print(lines)
            access_points = []
            for line in lines:
                networkInfo = line.split(";")
                #if AccessPoint.objects.filter(bssid=networkInfo[2].upper()).exists():
                #    skipped += 1
                #    continue
                access_point = AccessPoint(
                    latitude = None if networkInfo[0] == "null" else networkInfo[0],
                    longitude = None if networkInfo[1] == "null" else networkInfo[1],
                    bssid = networkInfo[2].upper(),
                    ssid = networkInfo[3],
                    password = networkInfo[4],
                    author = wifi_author,
                    wps_enabled = False,
                )
                access_points.append(access_point)
                #access_point.save()
            total = AccessPoint.objects.count()
            to_add = len(access_points)
            AccessPoint.objects.bulk_create(access_points, ignore_conflicts=True)
            new = AccessPoint.objects.count() - total
            context = {'total': to_add, 'skipped': to_add - new, 'new': new}
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
            access_points = []
            wifi_users = {}
            for network in json_file:
                if not network["author"] in wifi_users:
                    if not User.objects.filter(username=network["author"]).exists():
                        wifi_users[network["author"]] = None
                        continue
                    wifi_users[network["author"]] = WifiUser.objects.get(user__username=network["author"])
                if network["author"] is None:
                    continue
                access_point = AccessPoint(
                    bssid = network['MAC'].upper(),
                    ssid = network["SSID"],
                    wps = network["WPS"],
                    author = wifi_users[network["author"]],
                    password = network["password"],
                    latitude = None if network["position"][0] == "null" or network["position"][0] == "" else network["position"][0],
                    longitude = None if network["position"][1] == "null" or network["position"][0] == "" else network["position"][1],
                    wps_enabled = False,
                )
                access_point.added = network["timestamp"]
                access_points.append(access_point)
            AccessPoint.objects.bulk_create(access_points, ignore_conflicts=True)
            context = {'total': len(access_points), 'skipped': 'didnt calculate', 'new': 'didnt calculate'}
            return render(request, 'upload_complete.html', context)
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

@login_required
def generate_invite(request):
    invite = WifiUserInvite(
        invite_code = get_random_string(length=32),
        author = WifiUser.objects.get(user=request.user)
    )
    invite.save()
    context = {'invite_code': invite.invite_code}
    return render(request, 'generate_invite.html', context)

def register(request):
    register_form = RegisterForm(request.POST)
    if request.method == 'POST':
        if register_form.is_valid():
            try:
                invite = WifiUserInvite.objects.get(invite_code=register_form.cleaned_data['invite_code'], invitee=None)
            except:
                #invalid invite code
                return render(request, "register_error.html")

            if User.objects.filter(username=register_form.cleaned_data['username']).exists():
                #username taken
                return render(request, "register_error.html")

            user = User.objects.create_user(register_form.cleaned_data['username'], register_form.cleaned_data['email'], register_form.cleaned_data['password'])
            wifi_user = WifiUser(
                user = user,
                marker_color = register_form.cleaned_data['marker_color'].replace('#',''),
            )
            wifi_user.save()
            invite.invitee = wifi_user
            invite.save()

            return redirect('login')

        else:
            return render(request, "register_error.html")
    else:
        context = {
            'form': register_form
        }
        return render(request, "register.html", context)

@login_required
def settings(request):
    wifi_user = WifiUser.objects.get(user=request.user)
    initial_dict = {
        'username': request.user.username,
        'email': request.user.email,
        'marker_color': f"#{wifi_user.marker_color}",

    }
    settings_form = SettingsForm(request.POST or None, initial = initial_dict)
    error_message = None
    if request.method == 'POST':
        if settings_form.is_valid():
            user = request.user
            if not user.username.lower() == settings_form.cleaned_data['username'].lower() and User.objects.filter(username__iexact=settings_form.cleaned_data['username']).exists():
                error_message = f"Unable to change username: {settings_form.cleaned_data['username']} is already taken."
            else:
                user.username = settings_form.cleaned_data['username']
            user.email = settings_form.cleaned_data['email']
            user.save()
            wifi_user.marker_color = settings_form.cleaned_data['marker_color'].replace('#','')
            wifi_user.save()
        else:
            error_message = "Invalid form input detected."

    context = {
        'form': settings_form,
        'update_message': request.method == 'POST',
        'error_message': error_message
    }
    return render(request, "settings.html", context)
