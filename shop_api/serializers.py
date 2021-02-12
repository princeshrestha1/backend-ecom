from rest_framework import serializers
from cart.models import *
from account.models  import User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.html import strip_tags
import datetime


class UserLoginSerializer(serializers.ModelSerializer):
	email = serializers.EmailField(allow_blank=True, required=False)
	password = serializers.CharField(style={'input_type': 'password'})
	token = serializers.CharField(read_only=True)

	class Meta:
		model = User
		fields = ['email', 'password', 'token']
		extra_kwargs = {'password': {
			'write_only': True
		}}

	def validate(self, data):
		email = data.get('email', None)

		if not email:
			raise ValidationError('An email is required')

		user = User.objects.filter(
			Q(email=email)).distinct()

		if user.exists() and user.count() == 1:
			user = user.first()
		else:
			raise ValidationError("This email is invalid")
		return data


class UserRegistrationSerializer(serializers.Serializer):
	email = serializers.EmailField()
	username = serializers.CharField()
	password = serializers.CharField(style={'input_type': 'password'})
	confirm_password = serializers.CharField(style={'input_type': 'password'})
	mobile_number = serializers.CharField(style={'input_type': 'integer'})

	def validate_email(self, email):
		existing = User.objects.filter(email=email).first()
		if existing:
			raise serializers.ValidationError("Someone with that email "
				"address has already registered. Was it you?")
		return email

	def validate_username(self, username):
		existing = User.objects.filter(username=username).first()
		if existing:
			raise serializers.ValidationError("Someone with that username "
				"has already registered. Was it you?")
		return username

	def validate_mobile_number(self, mobile_number):
		existing = User.objects.filter(contact_no1=mobile_number).first()
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


class UserUpdateSerializer(serializers.Serializer):
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
	billing_addr = serializers.BooleanField(required=False)
	shipping_addr = serializers.BooleanField(required=False)


	# class Meta:
	#     fields = [
	#         'first_name', 'last_name', 'gender', 'birthdate', 'address_line1', 'address_line2',
	#         'contact_no1', 'contact_no2', 'landmark', 'city', 'district', 'billing_addr',
	#         'shipping_addr']

class UpdateAddressSerializer(serializers.Serializer):
    address_line1 = serializers.CharField(max_length=255, required=True)
    contact_no1 = serializers.CharField(max_length=255, required=True)

    def validate(self, data):
        contact = data.get('contact_no1')
        if len(contact) > 10:
            raise ValidationError({'contact_no1':'Contact number cannot be more than 10 '})
        return data


class PhotoSerializer(serializers.ModelSerializer):

	class Meta:
		model = Photo
		fields = ['photo']


class CategorySerializer(serializers.ModelSerializer):

	class Meta:
		model = Category
		fields = ['title']


class TagSerializer(serializers.ModelSerializer):

	class Meta:
		model = Tag
		fields = ['title']


class QuantitySerializer(serializers.ModelSerializer):

	class Meta:
		model = ProductInTransaction
		fields = ['quantity']


class CouponSerializer(serializers.ModelSerializer):
	valid_from = serializers.SerializerMethodField()

	def get_valid_from(self,obj):
		if obj:
			return str((datetime.datetime.strftime(obj.valid_from,'%b %d, %Y')))
	
	valid_to = serializers.SerializerMethodField()

	def get_valid_to(self,obj):
		if obj:
			return str((datetime.datetime.strftime(obj.valid_to,'%b %d, %Y')))


	class Meta:
		model = Coupon
		fields = ['title', 'code', 'valid_from', 'valid_to']


class NotifyMeSerializer(serializers.ModelSerializer):

	class Meta:
		model = NotifyMe
		fields = ['email', 'remarks']


class ProductSerializer(serializers.ModelSerializer):
	photos = PhotoSerializer(read_only=True, many=True)
	categories = CategorySerializer(read_only=True, many=True)
	tags = TagSerializer(read_only=True, many=True)
	share = serializers.SerializerMethodField('product_share')
	old_price = serializers.SerializerMethodField()
	discount_percent = serializers.SerializerMethodField()
	display_old_price = serializers.ReadOnlyField(read_only=True)
	display_new_price = serializers.ReadOnlyField(read_only=True)

	def product_share(self,product):
		url = 'http:breadfruit.prixa.net/product/'+ str(product.id) + '/detail/'
		return url

	class Meta:
		model = Product
		fields = [
			'name', 'photos', 'description', 'categories', 'tags', 'old_price', 'price', 'grand_total','display_old_price','display_new_price',
			'vat', 'discount_percent','share']
			
	def get_old_price(self,obj):
		return str(int(obj.old_price))

	def get_discount_percent(self,obj):
		return str(int(obj.discount_percent))

class RatingSerializer(serializers.ModelSerializer):

	class Meta:
		model = Rating
		fields = ['rate', 'review']




class SliderProductSerializer(serializers.ModelSerializer):
	photos = PhotoSerializer(read_only=True, many=True)
	categories = CategorySerializer(read_only=True, many=True)
	tags = TagSerializer(read_only=True, many=True)
	share = serializers.SerializerMethodField('product_share')
	you_save = serializers.SerializerMethodField()
	status = serializers.SerializerMethodField()
	description = serializers.SerializerMethodField()
	reviews = serializers.SerializerMethodField()
	reviews_count = serializers.SerializerMethodField()
	rating = serializers.SerializerMethodField()
	available = serializers.SerializerMethodField()
	is_wish = serializers.SerializerMethodField()
	summary = serializers.SerializerMethodField()
	discount_percent = serializers.SerializerMethodField()

	def get_is_wish(self,obj):
		try:
			wish_prod = Wishlist.objects.get(products__products_id=obj.id, deleted_at=None)
			return True
			
		except Wishlist.DoesNotExist:
			return False

	def get_available(self,obj):
		if obj.quantity > 0:
			return True
		else:
			return False

	def get_rating(self,obj):
		if obj:
			ratings = Rating.objects.filter(product__id=obj.id)
			toAddDict = {}
			if ratings.exists():
				total_rating = 0
				count = ratings.count()
				for rate in ratings:
					total_rating += rate.rate
				rating_avg = total_rating / count
				rate = rating_avg
			else:
				rate = 0
			return rate
		else:
			return ""
			
	def get_reviews(self,obj):
		if obj:
			ratings = Rating.objects.filter(product__id=obj.id)
			toAddDict = {}
			toAddTemp = []
			if ratings.exists():
				total_rating = 0
				count = ratings.count()
				for rate in ratings:
					total_rating += rate.rate
					toAddDict = {'username': rate.user.username, 'review': rate.review}
					toAddTemp.append(toAddDict)
			else:
				rate = 0

			return toAddTemp
		else:
			return ""

	def get_reviews_count(self,obj):
		if obj:
			ratings = Rating.objects.filter(product__id=obj.id)
			toAddTemp = {}
			toAddTemp["reviews"] = []
			if ratings.exists():
				total_rating = 0
				count = ratings.count()
				for rate in ratings:
					total_rating += rate.rate
					toAddTemp["reviews"].append({'username': rate.user.username, 'review': rate.review})
				rating_avg = total_rating / count
				rate = rating_avg
			else:
				rate = 0
			return str(len(toAddTemp["reviews"]))+' reviews'
		else:
			return ""


	def get_description(self,obj):
		if obj:
			return obj.description
		else:
			return ""

	def get_summary(self,obj):
		if obj:
			return obj.summary
		else:
			return ""

	def get_status(self,obj):
		if obj.quantity > 0:
			return 'In Stock'
		else:
			return 'Out of Stock'

	def get_you_save(self,obj):
		save = str(int(obj.old_price-obj.price))
		return save

	def product_share(self,product):
		if product.id:
			url = 'http:breadfruit.prixa.net/product/'+ str(product.id) + '/detail/'
			return url
		else:
			return 'No Url Found!!!'

	class Meta:
		model = Product
		fields = [
			'id','name', 'photos', 'description', 'categories', 'tags', 'old_price','visibility',
			'status','quantity','reference_code','price','is_on_sale','grand_total',
			'vat', 'vat_included','vat_amount','discount_percent','grand_total','you_save',
			'share','reviews','reviews_count','rating','available','is_wish','summary']


	def get_discount_percent(self,obj):
		return str(int(obj.discount_percent))



class SliderSerializer(serializers.ModelSerializer):
	category_id = serializers.SerializerMethodField()
	product = SliderProductSerializer()
	slider_type = serializers.SerializerMethodField()
	cart_quantity = serializers.SerializerMethodField()


	def get_slider_type(self,sliderlist):
		if sliderlist.slider_type != None:
			return sliderlist.slider_type
		else:
			return 'Slider Type Not Found!!!'

	
	def get_category_id(self,sliderlist):
		if sliderlist.category != None:
			return sliderlist.category.id
		else:
			return -1
	
	def get_cart_quantity(self, obj):
		print(self)
		if obj.product:
			if obj.product.productintransaction_set.filter(deleted_at__isnull=True).count() > 0:
				return str(obj.product.productintransaction_set.filter(deleted_at__isnull=True).first().quantity)
		return str(1)

	class Meta:
		model = Slider
		fields = ['id','photos','url','category_id','slider_type','product','cart_quantity']


class BuyNowSerializer(serializers.ModelSerializer):

	class Meta:
		serializers.CharField(style={'input_type': 'password'})
		model = User
		fields = ['first_name', 'last_name']


class ChangePasswordSerializer(serializers.Serializer):
	old_password = serializers.CharField(style={'input_type': 'password'})
	new_password = serializers.CharField(style={'input_type': 'password'})
	confirm_password = serializers.CharField(style={'input_type': 'password'})


class ConfirmCheckoutSerializer(serializers.ModelSerializer):
	class Meta:
		serializers.CharField(style={'input_type': 'password'})
		model = User
		fields = ['address_line1', 'contact_no1','address_line2','contact_no2']

class StockUpdateFromWalnutSerializer(serializers.Serializer):
	class Meta:
		model = Product
		fields = ['name','reference_code','quantity']

