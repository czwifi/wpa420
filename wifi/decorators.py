from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.shortcuts import render
from django.shortcuts import redirect
from django.utils import timezone

from functools import wraps
from datetime import datetime

from .models import WifiUserApiKey


def api_key_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            api_key = WifiUserApiKey.objects.get(key=request.META['HTTP_AUTHORIZATION'])
            api_key.used = timezone.now()
            api_key.save()
        except:
            return HttpResponse('Unauthorized', status=401)
        return view_func(request, *args, **kwargs)

    return _wrapped_view