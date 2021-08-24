from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.shortcuts import render
from django.shortcuts import redirect

from functools import wraps
from datetime import datetime

from .models import WifiUserApiKey


def api_key_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            api_key = WifiUserApiKey.objects.get(key=request.META['HTTP_AUTHORIZATION'])
            api_key.used = datetime.now()
            api_key.save()
            return view_func(request, *args, **kwargs)
        except:
            return HttpResponse('Unauthorized', status=401)

    return _wrapped_view