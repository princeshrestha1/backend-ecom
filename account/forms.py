import re 

from django import forms
from account.models import User, Subscriber, ShippingAddress
from django.contrib.auth.forms import PasswordResetForm


class UserForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'required': 'true',
        'placeholder': 'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'required': 'true',
        'placeholder': 'Confirm Password'}))

    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "email", "password1", "password2"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].widget.attrs.update(
            {'placeholder': 'First Name', 'required': 'true'})
        self.fields["last_name"].widget.attrs.update(
            {'placeholder': 'Last Name', 'required': 'true'})
        self.fields["email"].widget.attrs.update(
            {'placeholder': 'E-Mail', 'required': 'true'})

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if not password2:
            raise forms.ValidationError("You must confirm your password !")
        if password1 != password2:
            raise forms.ValidationError("Your passwords do not match !")

        return password2

        #User Name and Email Validation 

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.exclude(pk=self.instance.pk).get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError("Username already exists !")

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            email = User.objects.exclude(pk=self.instance.pk).get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError("Email already exists !")


class UserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "mobile_number", "email"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    #     self.fields["gender"].widget.attrs.update(
    #         {'class': 'custom-select', 'required': 'true'})
        # self.fields["last_name"].widget.attrs.update(
        #     {'placeholder': 'Last Name', 'required': 'true'})
        # self.fields["address_line1"].widget.attrs.update(
        #     {'placeholder': 'Address Line 1','required': 'true'})
        # self.fields["address_line2"].widget.attrs.update(
        #     {'placeholder': 'Address Line 2'})
        # self.fields["contact_no1"].widget.attrs.update(
        #     {'placeholder': 'Contact Line 1','required': 'true'})
        # self.fields["contact_no2"].widget.attrs.update(
        #     {'placeholder': 'Contact Line 2'})
        # self.fields["landmark"].widget.attrs.update(
        #     {'placeholder': 'Nearest Landmark'})
        # self.fields["city"].widget.attrs.update(
        #     {'placeholder': 'City'})
        # self.fields["email"].widget.attrs.update(
        #     {'placeholder': 'Email', 'required': 'true'})
        # self.fields["district"].widget.attrs.update(
        #     {'placeholder': 'District','required': 'true'})
        # self.fields["billing_addr"].widget.attrs.update(
        #     {'placeholder': 'Billing Address','required': 'true'})
        # self.fields["shipping_addr"].widget.attrs.update(
        #     {'placeholder': 'Shipping Address','required': 'true'})
        # self.fields['address_line2'].required = False
        # self.fields['contact_no2'].required = False
        # self.fields['landmark'].required = False
        # self.fields['birthdate'].required = False
        # self.fields['city'].required = True



class ShippingAddressForm(forms.ModelForm):

    class Meta:
        model = ShippingAddress
        fields = [
            "street_name", "city", "country", "postal_code", "contact_number"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        # self.fields["address_line2"].widget.attrs.update(
        #     {'placeholder': 'Address Line 2'})
        # self.fields["contact_no2"].widget.attrs.update(
        #     {'placeholder': 'Contact Line 2'})


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'required': 'true',
        'placeholder': 'Username or Email', 'class':'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'required': 'true',
        'placeholder': 'Password','class':'form-control' }))

    class Meta:
        fields = [
            "username",
            "password",
        ]


class StaffForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            self.fields['username'].widget.attrs.update({'class': 'form-control', 'required': 'True'})
            self.fields['email'].widget.attrs.update({'class': 'form-control', 'required': 'True'})


    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.exclude(pk=self.instance.pk).get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError("Username already exists")


    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            email = User.objects.exclude(pk=self.instance.pk).get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError("Email already exists!!")




class StaffDeleteForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['is_active']
        widgets = {
            'is_active': forms.HiddenInput(),
        }


class EmailForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'required': 'true',
            'id': 'email',
        }))


class SubscribeForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={'class': 'form-control',
                   'data-height': '37px'}))


class SubscriberDeleteForm(forms.ModelForm):

    class Meta:
        model = Subscriber
        fields = ['deleted_at']
        widgets = {
            'deleted_at': forms.HiddenInput(),
        }



class PasswordResetRequestForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={'class':  'form-control', 'placeholder': 'Email'}))


from django.contrib.auth.hashers import check_password


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class':'form-control','placeholder':'Current Password','id':'current_pass'}))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class':'form-control','placeholder':'Password','id':'pass'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Confirm Password', 'id': 'confirmpass'}))

    def __init__(self, *args, **kwargs):
        self.user_details = kwargs.pop('user', None)
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(ChangePasswordForm, self).clean()
        current_password = cleaned_data.get('current_password')
        checker = check_password(current_password, self.user_details.password)

        if checker:
            password = cleaned_data.get('password')
            confirm_password = cleaned_data.get('confirm_password')

            if (password != confirm_password):
                raise forms.ValidationError('Passwords do not match !!')
        else:
            raise forms.ValidationError('Current password not matched')

