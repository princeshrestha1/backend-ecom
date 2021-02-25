from rest_framework import serializers
from cart.models import *
from account.models  import User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.html import strip_tags
import datetime



class UserRegistrationSerializer(serializers.Serializer):
	email = serializers.EmailField()
	username = serializers.CharField(required=False)
	password = serializers.CharField(style={'input_type': 'password'},required=True)
	confirm_password = serializers.CharField(style={'input_type': 'password'})
	mobile_number = serializers.CharField(style={'input_type': 'integer'})
	# token = serializers.CharField(read_only=True)

	def validate_email(self, email):
		existing = User.objects.filter(email=email).first()
		if existing:
			raise serializers.ValidationError("Someone with that email "
				"address has already registered. Was it you?")
		return email


	def validate_mobile_number(self, mobile_number):
		existing = User.objects.filter(mobile_number=mobile_number).first()
		if existing:
			raise serializers.ValidationError("Someone with that mobile number "
				" has already registered. Was it you?")
		if len(mobile_number) > 10:
			raise serializers.ValidationError('Enter a valid mobile number')
		return mobile_number

	def validate(self, data):
		if not data.get('password') or not data.get('confirm_password'):
			raise serializers.ValidationError("Please enter a password and "
				"confirm it.")

		if data.get('password') != data.get('confirm_password'):
			raise serializers.ValidationError("Those passwords don't match.")
		return data

class UserLoginSerializer(serializers.ModelSerializer):
	email = serializers.CharField(allow_blank=True, required=True)
	password = serializers.CharField(style={'input_type': 'password'})
	token = serializers.CharField(read_only=True)

	class Meta:
		model = User
		fields = ['password','email', 'token']
		extra_kwargs = {'password': {
			'write_only': True
		}}

class UserVerificationSerializers(serializers.Serializer):
	otp = serializers.CharField(required=True)


class UserProfileUpdateSerializers(serializers.Serializer):
	username = serializers.CharField(max_length=255)
	# last_name = serializers.CharField(max_length=255)
	mobile_number = serializers.CharField(max_length=255, required=True)
	email = serializers.EmailField()


class UserUpdateSerializers(serializers.Serializer):
	first_name = serializers.CharField(max_length=255)
	last_name = serializers.CharField(max_length=255)
	gender = serializers.CharField(max_length=15,default="Male")
	birthdate = serializers.DateField(required=False)
	address_line1 = serializers.CharField(max_length=255,required=True)
	address_line2 = serializers.CharField(max_length=255, required=False)
	contact_no1 = serializers.CharField(max_length=255, required=True)
	contact_no2 = serializers.CharField(max_length=255, required=False)
	landmark = serializers.CharField(max_length=255, required=False)
	city = serializers.CharField(max_length=255, required=False)

class UpdateAddressSerializer(serializers.Serializer):
	contact_number = serializers.CharField(max_length=255, required=True)
	country = serializers.CharField(max_length=255, required=True)
	name = serializers.CharField(max_length=255,required=True)
	postal_code = serializers.CharField(max_length=255, required=False)
	city = serializers.CharField(max_length=255, required=True)
	street_name = serializers.CharField(max_length=255, required=True)
	lat = serializers.CharField(max_length=255,required=False)
	lng = serializers.CharField(max_length=255,required=False)

class UpdateBillingAddressSerializer(serializers.Serializer):
	id = serializers.CharField(max_length=255, required=True)
	contact_number = serializers.CharField(max_length=255, required=True)
	country = serializers.CharField(max_length=255, required=True)
	name = serializers.CharField(max_length=255,required=True)
	postal_code = serializers.CharField(max_length=255, required=False)
	city = serializers.CharField(max_length=255, required=True)
	street_name = serializers.CharField(max_length=255, required=True)
	lat = serializers.CharField(max_length=255,required=False)
	lng = serializers.CharField(max_length=255,required=False)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class ProductIDSerializer(serializers.Serializer):
    category_title = serializers.CharField(required=True)

class SingleProductSerializer(serializers.Serializer):
    product_id = serializers.CharField(required=True)

class AddToCartSerializers(serializers.Serializer):
	user_id = serializers.CharField(read_only=True)
	product_id = serializers.CharField(required=True)
	product_quantity = serializers.CharField(required=True)


# class CheckoutSerializer(serializers.ModelSerializer):
class CheckoutSerializer(serializers.Serializer):
	order_id = serializers.CharField(required=False)
	products_id = serializers.CharField()
	# class Meta:
	# 	model = Cart
	# 	fields = ['order_id','products_id','is_ordered','is_taken','is_cancelled']

class CartADDSerializer(serializers.ModelSerializer):
	user_id = serializers.IntegerField(required=False)
	products_id = serializers.CharField()
	
	class Meta:
		model = ProductInTransaction
		fields = ['user_id', 'products_id']

class ConfirmCheckoutSerializer(serializers.Serializer):
	order_id = serializers.CharField(required=True)
	gateway = serializers.CharField(required=True)
	address_id = serializers.CharField(required=True)


class CancelSerializer(serializers.Serializer):
	order_id = serializers.CharField()