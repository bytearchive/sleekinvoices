from django.contrib.auth.models import User
from django import forms
from . models import Company_credentials,Invoice,Client

class SigninForm(forms.ModelForm):

    username = forms.CharField(label='Username',max_length=25,min_length=4,widget=forms.TextInput({"placeholder":"Username"}))
    password = forms.CharField(min_length=8,max_length=25,widget=forms.PasswordInput({"placeholder": "Enter Password here.."}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput({"placeholder": "xyz@agiliq.com"}))
    class Meta:
        model = User
        fields = ['email','username','password']


class CompanyCredentialsForm(forms.ModelForm):

    class Meta:
        model = Company_credentials
        fields = ['company_name','company_address','email','country','phone_number','website_url']

class RaiseInvoiceForm(forms.ModelForm):

    #raise_for = forms.CharField(widget=forms.TextInput({"placeholder":"ABC Infosolutions"}))
    currency =  forms.CharField(widget=forms.TextInput({"placeholder":"Dollars"}))

    class Meta:
        model = Invoice
        fields = ['client','currency','message']


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['organisation_name', 'email','client_address','country', 'phone_number']