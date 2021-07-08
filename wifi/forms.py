from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Select a file')

class WigleForm(forms.Form):
	wigle_name = forms.CharField(label='Wigle API Name', max_length=100)
	wigle_key = forms.CharField(label='Wigle API Key', max_length=100)