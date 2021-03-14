from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.

CURRENT_DOMAIN = '142.93.221.85'

class Timestampable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_at = models.DateTimeField(auto_now_add=False, auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self):
        self.deleted_at = timezone.now()
        super().save()


GENDER_CHOICES = (
    ("Male", "Male"),
    ("Female", "Female"),
    ("Others", "Others"))


CUSTOMER_CHOICES = (
    ('Registered', "Registered"),
    ('Guest', "Guest"))



class User(AbstractUser):
    # username = models.CharField(max_length=255,unique=False,default=' ')
    gender = models.CharField("Gender", max_length=15, choices=GENDER_CHOICES, default="Male")
    birthdate = models.DateField("Birthday", null=True, blank=True)
    customer_type = models.CharField(max_length=15, choices=CUSTOMER_CHOICES, default="Registered")
    # address_line1 = models.CharField("Address Line", max_length=255, null=True, blank=True)
    mobile_number = models.BigIntegerField("Mobile Number",null=True,unique=True)
    # address_line2 = models.CharField("Optional Address", max_length=255, null=True, blank=True)
    # contact_no1 = models.BigIntegerField("Contact Line", null=True, blank=True)
    # contact_no2 = models.BigIntegerField("Optional Contact", null=True, blank=True)
    # city = models.CharField("City", max_length=255, null=True, blank=True)
    # province = models.CharField("Province", max_length=255, null=True, blank=True)
    # postal_code = models.CharField("Postal Code",max_length=255,null=True,blank=True,default=' ')
    # lat = models.CharField("Latitude",max_length=255,null=True,blank=True,default=' ')
    # lng = models.CharField("Longitude",max_length=255,null=True,blank=True,default=' ')
    # street_name = models.CharField("Street Name",max_length=255,null=True,blank=True,default=' ')
    # country = models.CharField("Country",max_length=255,null=True,blank=True,default=' ')
    is_read = models.BooleanField(default=False)
    otp_code = models.PositiveIntegerField(default=0)
    # USERNAME_FIELDS=['mobile_number','username']
    # REQUIRED_FIELDS = ['email']
    def __str__(self):
        return self.username

    @property
    def name(self):
        return "{0} {1}".format(self.first_name, self.last_name)



class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, null=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return str(self.email)


class ShippingAddress(models.Model):
    user = models.ForeignKey(User, related_name="user_shipping_addr", on_delete=models.CASCADE)
    city = models.CharField("City",max_length=255,null=True,blank=True,default=' ')
    name = models.CharField("Name",max_length=255,null=True,blank=True,default=' ')
    contact_number = models.CharField("Phone Number",max_length=255,null=True,blank=True,default=' ')
    country = models.CharField("Name",max_length=255,null=True,blank=True,default=' ')
    postal_code = models.CharField("Postal Code",max_length=255,null=True,blank=True,default=' ')
    street_name = models.CharField("Street Name",max_length=255,null=True,blank=True,default=' ')
    lat = models.CharField('Latitude',null=True,blank=True,max_length=255)
    lng = models.CharField('Longitude',null=True,blank=True,max_length=255)

    def __str__(self):
        return str(self.user)

    def full_address(self):
        return self.street_name +  ", "+ self.city +", "+ self.country + ", "+ self.postal_code

