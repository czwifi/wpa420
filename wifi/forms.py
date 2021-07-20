from django import forms
from .models import WifiUser

class UploadFileForm(forms.Form):
	file = forms.FileField(label='Select a file')
	import_as = forms.ModelChoiceField(queryset=WifiUser.objects.all().select_related('user').order_by('user__username'))


class WigleForm(forms.Form):
	wigle_name = forms.CharField(label='Wigle API Name', max_length=100)
	wigle_key = forms.CharField(label='Wigle API Key', max_length=100)

class RegisterForm(forms.Form):
	username = forms.CharField(label='Username', max_length=150)
	email = forms.EmailField(label='Email (optional)', required=False)
	password = forms.CharField(label='Password', widget=forms.PasswordInput)
	invite_code = forms.CharField(label='Invite Code', max_length=32)
	marker_color = forms.CharField(label='Marker Color', widget=forms.TextInput(attrs={'type': 'color'}))

class SettingsForm(forms.Form):
	username = forms.CharField(label='Username', max_length=150)
	email = forms.EmailField(label='Email (optional)', required=False)
	marker_color = forms.CharField(label='Marker Color', widget=forms.TextInput(attrs={'type': 'color'}))