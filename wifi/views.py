from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt


from .models import AccessPoint, WifiUser, WifiUserInvite, WifiUserApiKey
from .forms import UploadFileForm, WigleForm, RegisterForm, SettingsForm, CreateWifiUserApiKeyForm, ApiKeyForm
from .decorators import api_key_required
from .handlers import process_import, generate_v1_ap_array, render_generic_error, render_json_error, generate_api_key

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
    filtered_ap_list = AccessPoint.objects.exclude(latitude=None).prefetch_related('wifi_import__author__user')
    unprocessed_ap_list = AccessPoint.objects.filter(refresh_attempts=0)
    user_list = WifiUser.objects.all().select_related('user').annotate(Count('accesspoint')).order_by('-accesspoint__count')
    provider_list = []
    providers = ['UPC', 'Vodafone', 'O2', 'MujO2', 'PODA', 'TP-LINK', 'ASUS']
    for provider in providers:
        provider_list.append({'provider':provider, 'ap_count': AccessPoint.objects.filter(ssid__startswith=provider).count()})
    provider_list.sort(key=lambda x: x['ap_count'], reverse=True)
    context = {
        'ap_list': ap_list,
        'filtered_ap_list': filtered_ap_list,
        'unprocessed_ap_list': unprocessed_ap_list,
        'leaderboards': user_list,
        'provider_list': provider_list,
    }
    return render(request, 'map.html', context)

@login_required
def upload_form(request):
    wifi_author = WifiUser.objects.get(user=request.user)
    form = UploadFileForm(request.POST or None, request.FILES or None, initial={'import_as': wifi_author})
    if request.method == 'POST':
        if form.is_valid():
            if request.user.is_superuser and form.cleaned_data['import_as'] is not None:
                wifi_author = form.cleaned_data['import_as']
            import_text = request.FILES['file'].read().decode('utf-8')
            import_results = process_import(import_text, wifi_author)
            context = {'total': import_results.to_add, 'skipped': import_results.skipped, 'new': import_results.new}
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
            context = {'total': len(access_points), 'skipped': 'didnt calculate', 'new': 'Please also run the fixtimestamps and createimports commands in CLI'}
            return render(request, 'upload_complete.html', context)
        else:
            field_errors = [ (field.label, field.errors) for field in form] 
            print(field_errors)
    else:
        return render(request, 'upload.html', context)

@login_required
def export(request):
    return render(request, 'export.html')

@api_key_required
def wifi_list_json(request):
    ap_list = AccessPoint.objects.all().prefetch_related('wifi_import__author__user')
    networks = generate_v1_ap_array(ap_list)
    return JsonResponse(networks, safe=False)

@csrf_exempt
def api_get_api_key(request):
    if request.method == 'POST':
        user = authenticate(username=request.POST.get('username', ''), password=request.POST.get('password', ''))
        if user is None:
            return render_json_error(request, "Invalid login credentials")
        wifi_user = WifiUser.objects.get(user=user)
        if wifi_user is None:
            return render_json_error(request, "WifiUser does not exist")
        api_key = generate_api_key(wifi_user, request.POST.get('description', 'Unnamed app'))
        response = {"success": True, "api_key": api_key.key}
        return JsonResponse(response, safe=False)
    else:
        return render_json_error(request, "Invalid request type")


@login_required
def wifi_list_downloadable(request, format=None, additional=False):
    if additional == "mine":
        ap_list = AccessPoint.objects.filter(wifi_import__author=WifiUser.objects.get(user=request.user)).prefetch_related('wifi_import__author__user')
    else:
        ap_list = AccessPoint.objects.all().prefetch_related('wifi_import__author__user')

    if format == "jsonv1":
        networks = generate_v1_ap_array(ap_list)
        response = JsonResponse(networks, safe=False)
        response['Content-Disposition'] = 'attachment; filename=export.json'
        return response
    else:
        return render_generic_error(request, "Invalid export format")

@api_key_required
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
                    return render_generic_error(request, "bad wigle api data")
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
            return render(request, 'my_imports/refresh_complete.html', context)
        else:
            return render_generic_error(request, "something went wrong")
    else:
        return render(request, 'my_imports/refresh.html', context)

@login_required
def generate_invite(request):
    invite = WifiUserInvite(
        invite_code = get_random_string(length=32),
        author = WifiUser.objects.get(user=request.user)
    )
    invite.save()
    context = {'invite_code': invite.invite_code}
    return render(request, 'account/generate_invite.html', context)

def register(request):
    register_form = RegisterForm(request.POST)
    if request.method == 'POST':
        if register_form.is_valid():
            try:
                invite = WifiUserInvite.objects.get(invite_code=register_form.cleaned_data['invite_code'], invitee=None)
            except:
                #invalid invite code
                return render(request, "account/register_error.html")

            if User.objects.filter(username=register_form.cleaned_data['username']).exists():
                #username taken
                return render(request, "account/register_error.html")

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
            return render(request, "account/register_error.html")
    else:
        context = {
            'form': register_form
        }
        return render(request, "account/register.html", context)

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
            render_generic_error(request, "Invalid form input detected.")

    context = {
        'form': settings_form,
        'update_message': request.method == 'POST',
        'error_message': error_message
    }
    return render(request, "account/settings.html", context)

@login_required
def manage_api_keys(request):
    wifi_user = WifiUser.objects.get(user=request.user)
    key_list = WifiUserApiKey.objects.filter(wifi_user=wifi_user).order_by('-used')
    context = {
        'key_list': key_list
    }
    return render(request, "account/settings/api_keys.html", context)

@login_required
def create_api_key(request):
    wifi_user = WifiUser.objects.get(user=request.user)
    form = CreateWifiUserApiKeyForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            api_key = generate_api_key(wifi_user, form.cleaned_data['description'])
            context = {
                'api_key': api_key.key
            }
            return render(request, "account/settings/api_keys/new_complete.html", context)
        else:
            return render_generic_error(request, "Invalid form input detected.") #TODO: error handling

    context = {
        'form': form
    }
    return render(request, "account/settings/api_keys/new.html", context)

@login_required
def delete_api_key(request, key_id=None):
    wifi_user = WifiUser.objects.get(user=request.user)
    try:
        api_key = WifiUserApiKey.objects.get(pk=key_id)
        if not api_key.wifi_user == wifi_user:
            return render_generic_error(request, "the key exists but it belongs to someone else")
        api_key.delete()
        return redirect('api_keys')
    except:
        return render_generic_error(request, "the key probably doesn't exist")