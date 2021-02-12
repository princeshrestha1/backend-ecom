from django import forms
from .models import *
from account.models import User
from ckeditor.widgets import CKEditorWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from ckeditor.fields import RichTextField
from dal import autocomplete

RATE_CHOICES = (
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
    (5, 5),
)

QUICK_CHOICES = (
    ('Not an option', '----------------------'),
    ('1', 'Delete Selected'),
)

QUICK_CHOICES_PRODUCTS =  (
    ('Not an option', '----------------------'),
    ('1', 'Delete Selected'),
    ('2', 'Make Visible'),
    ('3', 'Make as New Product'),
    ('4', 'Make as Product on Sale'),
    ('5', 'Make as Coming Soon')
    ) 


class HorizRadioRenderer(forms.RadioSelect):
    """ this overrides widget method to put radio buttons horizontally
        instead of vertically.
    """
    def render(self):
        """Outputs radios"""
        return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            "title", "code", "valid_from", "valid_to", "validity_count",
            "discount_type", "discount_percent", "discount_amount",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update(
                {'class': 'form-control'})
        self.fields['discount_type'].widget.attrs.update({
            'id': 'select-list', 'class': 'form-control'})
        self.fields['valid_from'].widget.attrs.update(
            {'class': 'datetimepicker form-control'})
        self.fields['valid_to'].widget.attrs.update(
            {'class': 'datetimepicker form-control'})


    def clean_discount_percent(self):
        discount_percent = self.cleaned_data['discount_percent']
        if float(discount_percent) < 0.0:
            raise forms.ValidationError('Discount Percent must be greater than 0')
        return discount_percent


    def clean_valid_to(self):
        valid_to = self.cleaned_data['valid_to']
        valid_from = self.cleaned_data['valid_from']
        if valid_to.date() < valid_from.date():
            raise forms.ValidationError(
                "The valid to date cannot be before the valid from date!")
        return valid_to



class CouponDeleteForm(forms.ModelForm):

    class Meta:
        model = Coupon
        fields = ['deleted_at']
        widgets = {
            'deleted_at': forms.HiddenInput(),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            "title", "image", "description","seo_title", "seo_description","seo_keywords"
        ]

    def __init__(self, data=None, *args, **kwargs):
        data = self.keyword_tags(data)
        super().__init__(data=data, *args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update(
                {'class': 'form-control'})
        self.fields['description'].widget = CKEditorUploadingWidget()
        self.fields['seo_keywords'].widget.attrs.update({
            'class': 'selector',})

    def keyword_tags(self,data):
        from django.http import QueryDict
        if data!= None:
            data_dict = dict(data)

            data_dict['seo_keywords'] = list()
            for value in data.getlist('seo_keywords'):
                try:
                    value = int(value)
                    data_dict['seo_keywords'].append(value)
                except:
                    keyword,_ = Keywords.objects.get_or_create(title = value)
                    data_dict['seo_keywords'].append(keyword.pk)
            
            data = QueryDict('', mutable=True)
            for key,values in data_dict.items():
                for value in values:
                    data.update({key:value})
        return data



class CategoryDeleteForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = ['deleted_at']
        widgets = {
            'deleted_at': forms.HiddenInput(),
        }


class ProductForm(forms.ModelForm):
    tag = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.filter(deleted_at__isnull=True),required=False,
        widget=autocomplete.ModelSelect2Multiple(url='cart:tags_autocomplete'))
    
    class Meta:
        model = Product
        fields = [
            "name", "reference_code", "barcode", "visibility", "description", "summary", "quantity", "warning",
            "categories", "price", "old_price", "vat", "vat_included", "discount_percent", "discount_amount","unit",
             "expire_on", "tags","seo_title","seo_keywords","seo_description", "variant", "owner", "product_address"
        ]

    def __init__(self, data=None, *args, **kwargs):
        data = self.keyword_tags(data)
        data = self.tags(data)
        super().__init__(data=data,*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update(
                {'class': 'form-control'})
        self.fields['categories'].widget.attrs.update({
            'class': 'select2 form-control'})
        self.fields['name'].widget.attrs.update({
            'placeholder': 'Enter the title'})
        self.fields['tags'].widget.attrs.update({'class': 'select-tags form-control'})
        self.fields['variant'].widget.attrs.update({'class': 'select2 form-control'})
        self.fields['vat_included'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['seo_keywords'].widget.attrs.update({
            'class': 'selector',})
        self.fields['seo_keywords'].queryset = Keywords.objects.filter(deleted_at__isnull=True)
        self.fields['categories'].queryset = Category.objects.filter(deleted_at__isnull=True)
        self.fields['tags'].queryset = Tag.objects.filter(deleted_at__isnull=True)
        self.fields['variant'].queryset = Product.objects.filter(deleted_at__isnull=True)
        self.fields['expire_on'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        self.fields['discount_amount'].required = False
        self.fields['old_price'].required = False
        self.fields['expire_on'].required = False
        self.fields['price'].required = True
        self.fields['summary'].widget = CKEditorUploadingWidget()
        self.fields['description'].widget = CKEditorUploadingWidget()



    def clean_price(self):
        price = self.cleaned_data['price']
        if float(price) < 0.0:
            raise forms.ValidationError('Amount must be greater than 0')
        return price

    def clean_discount_percent(self):
        discount_percent = self.cleaned_data['discount_percent']
        if float(discount_percent) < 0.0:
            raise forms.ValidationError('Discount Percent must be greater than 0')
        return discount_percent

    def clean_vat(self):
        vat = self.cleaned_data['vat']
        if float(vat) < 0.0:
            raise forms.ValidationError('VAT must be greater than 0')
        return vat

    def tags(self,data):
        from django.http import QueryDict
        if data!= None:
            data_dict = dict(data)

            data_dict['tags'] = list()
            for value in data.getlist('tags'):
                try:
                    value = int(value)
                    data_dict['tags'].append(value)
                except:
                    tag,_ = Tag.objects.get_or_create(title = value)
                    data_dict['tags'].append(tag.pk)
            
            data = QueryDict('', mutable=True)
            for key,values in data_dict.items():
                for value in values:
                    data.update({key:value})
        return data

    def keyword_tags(self,data):
        from django.http import QueryDict
        if data!= None:
            data_dict = dict(data)

            data_dict['seo_keywords'] = list()
            for value in data.getlist('seo_keywords'):
                try:
                    value = int(value)
                    data_dict['seo_keywords'].append(value)
                except:
                    keyword,_ = Keywords.objects.get_or_create(title = value)
                    data_dict['seo_keywords'].append(keyword.pk)
            
            data = QueryDict('', mutable=True)
            for key,values in data_dict.items():
                for value in values:
                    data.update({key:value})
        return data


class ProductPhotoForm(forms.ModelForm):
    
    class Meta:
        model = Photo
        fields = ['photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photo'].widget.attrs.update({
            'multiple': 'true'})
        self.fields['photo'].required = False


class ProductDeleteForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = ['deleted_at']
        widgets = {
            'deleted_at': forms.HiddenInput(),
        }


class OrderProductDeleteForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = []
 

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = [
            "title", "description",]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update(
                {'class': 'form-control'})
        # self.fields['description'].widget.attrs.update({'id': 'summernote'})


class KeywordForm(forms.ModelForm):
    class Meta:
        model = Keywords
        fields = [
            "title"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update(
                {'class': 'form-control'})


class KeywordDeleteForm(forms.ModelForm):

    class Meta:
        model = Keywords
        fields = ['deleted_at']
        widgets = {
            'deleted_at': forms.HiddenInput(),
        }


class TagDeleteForm(forms.ModelForm):

    class Meta:
        model = Tag
        fields = ['deleted_at']
        widgets = {
            'deleted_at': forms.HiddenInput(),
        }


class SliderForm(forms.ModelForm):
    
    class Meta:
        model = Slider
        fields = ["title", "photos","status",'slider_type',"category","product","url"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slider_type'].widget = forms.RadioSelect(choices=SLIDER_CHOICES)
        
        for field in iter(self.fields):
            if field == 'slider_type':
                continue
            if ('status' in field):
                continue
            
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
            self.fields['url'].required = False
            

            


class SliderDeleteForm(forms.ModelForm):

    class Meta:
        model = Slider
        fields = ['deleted_at']
        widgets = {
            'deleted_at': forms.HiddenInput(),
        }


class PhotoForm(forms.ModelForm):

    class Meta:
        model = Photo
        fields = ['title', 'photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update(
                {'class': 'form-control'})


class SiteConfigForm(forms.ModelForm):
    class Meta:
        model = SiteConfig
        fields = ["key", "value",]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update(
                {'class': 'form-control'})

class TodayDealForm(forms.ModelForm):
    class Meta:
        model = FeaturedProduct
        fields = [ ]



class FeaturedProductForm(forms.ModelForm):
    products = forms.ModelChoiceField(
        queryset=Product.objects.filter(deleted_at__isnull=True),
        required=False,
        widget=forms.Select(
            attrs={'class':  'form-control'}))

    class Meta:
        model = FeaturedProduct
        fields = [
            "products",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update(
                {
                    'class': 'form-control', 'id': 'select-product'})


class WishDeleteForm(forms.ModelForm):

    class Meta:
        model = Wishlist
        fields = ['deleted_at']
        widgets = {
            'deleted_at': forms.HiddenInput(),
        }


class ConfirmOrderForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = []
        widgets = {
            'user': forms.HiddenInput(),
            'products': forms.HiddenInput(),
        }


class OrderConfirmByCMS(forms.ModelForm):

    class Meta:
        model = Order
        fields = ["is_confirmed"]

class CancelOrderForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ["condition_status"]


class OrderStatusUpdateForm(forms.ModelForm):
    condition_status = forms.ModelChoiceField(queryset=Status.objects.filter(deleted_at__isnull=True))

    class Meta:
        model = Order
        fields = ["condition_status", "shipped_date" ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):

            self.fields['shipped_date'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required':'true'})
            self.fields['condition_status'].widget.attrs.update(
                {'class': 'form-control', 'required': 'true'})
            # self.fields['code'].widget.attrs.update(
            #     {'class': 'form-control', 'required': 'true'})


class OrderForm(forms.ModelForm):
    # products = forms.ModelChoiceField(queryset=Status.objects.filter(deleted_at__isnull=True))
    class Meta:
        model = Order
        fields = []

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for field in iter(self.fields):
                self.fields[field].widget.attrs.update(
                    {'class': 'form-control'})

class OrderFormCMS(forms.ModelForm):
    products = forms.ModelChoiceField(
		queryset=Product.objects.filter(deleted_at=None),
		required=True,
		widget=forms.Select(
			attrs={
				'data-placeholder':'Product',
				'style':  'width: 100%;'}))
    quantity = forms.IntegerField()

    class Meta:
        model = Order
        fields = [
            "products", "email", "contact_number", "condition_status","shipped_date"]
        widgets = {
            'condition_status': forms.Select(attrs={
                'class': 'form-control',
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update(
                {'class': 'form-control'})
            self.fields['shipped_date'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})



class RatingForm(forms.ModelForm):
    rate = forms.ChoiceField(choices=RATE_CHOICES,
            widget=forms.RadioSelect())

    class Meta:
        model = Rating
        fields = ['rate', 'review']
        widgets = {
            'review': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Your Review',
            })
        }

    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       self.fields['rate'].widget.attrs['class'] = 'rating'


class QuantityForm(forms.ModelForm):

    class Meta:
        model = ProductInTransaction
        fields = ['quantity']
        widgets = {
            'quantity': forms.TextInput(attrs={
                'class': 'form-control',
            })
        }


class TagAutoForm(forms.ModelForm):

    class Meta:
        model = Tag
        fields = ['title']


class GuestForm(forms.Form):
    first_name = forms.CharField(
        max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(
        max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}))
    mobile_number = forms.CharField(
        label='Contact Number', max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    street_name = forms.CharField(
        label='Street Name', max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(
        max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    country = forms.CharField(
        label='Country', max_length=100,
        widget=forms.TextInput())
    postal_code = forms.CharField(
        max_length=100, widget=forms.NumberInput(attrs={'class': 'form-control'}), required=False)
        
    def clean(self):
        cleaned_data = self.cleaned_data
        return cleaned_data

    def is_integer(self, number):
        try:
            int(number)
            return True
        except: 
            return False
            pass

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data['mobile_number']
        if self.is_integer(mobile_number) == False:
            raise forms.ValidationError('Enter a valid contact number')
        return mobile_number


class CouponApplyForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ["code"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update(
                {'class': 'form-control'})
        self.fields['code'].label = ''


class StatusForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update(
                {'class': 'form-control'})


class StatusDeleteForm(forms.ModelForm):

    class Meta:
        model = Status
        fields = ['deleted_at']
        widgets = {
            'deleted_at': forms.HiddenInput(),
        }


class StatusAutoForm(forms.ModelForm):

    class Meta:
        model = Status
        fields = ['name']


class TrackerForm(forms.ModelForm):
    estimated_date = forms.DateField(required=True)
    status = forms.ModelMultipleChoiceField(
        queryset=Status.objects.all(),
        required=True,
        widget=forms.SelectMultiple(
            attrs={'class':  'select2 form-control', 'data-placeholder': 'Status',
                   'style':  'width: 100%;'}))
    class Meta:
        model = Tracker
        fields = ["status", "remarks", "estimated_date"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update(
                {'class': 'form-control'})
        self.fields['remarks'].widget.attrs.update({'id': 'summernote'})
        self.fields['status'].widget.attrs.update({
            'id': 'select-status'})


class TrackingForm(forms.Form):
    code = forms.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update(
                {'class': 'form-control'})
            self.fields['code'].label = "Tracking ID"


class QuickActionForm(forms.Form):
    options = forms.ChoiceField(choices=QUICK_CHOICES, label='',widget=forms.Select(attrs={'class': 'form-control'}))



class QuickProductActionForm(forms.Form):
    options = forms.ChoiceField(choices=QUICK_CHOICES_PRODUCTS, label='',widget=forms.Select(attrs={'class': 'form-control'}))



class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [ "first_name", "last_name", "email", "mobile_number"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update(
                {'class': 'form-control'})
            # self.fields['city'].required = True
            # self.fields['province'].required = True
            # self.fields['country'].required = True
            # self.fields['street_name'].required = True
                 


class UserDeleteForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['is_active']
        widgets = {
            'is_active': forms.HiddenInput(),
        }

class PaymentForm(forms.ModelForm):

    payment_type = forms.ChoiceField(choices=PAYMENT_CHOICES, widget=forms.RadioSelect)
    class Meta:
        model = Order
        fields = ['payment_type']
      
# Oraganization and model number removed Emergency contact number=Contact number 2(ptional field (blank/null=true))
class InquiryForm(forms.ModelForm):

    class Meta:
        model = Inquiry
        fields = [
            'name', 'email', 'contact_number_1', 'contact_number_2',
            'product', 'description']
        widgets = {
            'name': forms.TextInput(
                attrs={
                'class': 'form-control',
                'placeholder': 'Full Name',
                'required': 'True',
            }),
            # 'organization': forms.TextInput(
                # attrs={
                # 'class': 'form-control',
                # 'placeholder': 'Organization Name',
            # }),
            'email': forms.EmailInput(
                attrs={
                'class': 'form-control',
                'placeholder': 'Email Address',
                'required': 'True',
            }),
            'contact_number_1': forms.TextInput(
                attrs={
                'class': 'form-control',
                'placeholder': 'Contact Number 1',
                'required': 'True',
            }),
            'contact_number_2': forms.TextInput(
                attrs={
                'class': 'form-control',
                'placeholder': 'Contact Number 2',
            }),
            'product': forms.TextInput(
                attrs={
                'class': 'form-control',
                'placeholder': 'Product',
                'required': 'True',
            }),
            # 'model_number': forms.TextInput(
                # attrs={
                # 'class': 'form-control',
                # 'placeholder': 'Model Number',
            # }),
            'description': forms.Textarea(
                attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Write something about your product',
                'style': 'resize: none;',
            }),
        }


class InquiryRespondForm(forms.ModelForm):

    class Meta:
        model = Inquiry
        fields = ['is_responded']
        widgets = {
            'is_responded': forms.HiddenInput(),
        }


class ExportForm(forms.Form):
    from_date = forms.DateField(required=False)
    to_date = forms.DateField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields['from_date'].widget.attrs.update(
            {'class': 'datetimepicker form-control'})
            self.fields['to_date'].widget.attrs.update(
            {'class': 'datetimepicker form-control'})


class ApproveReviewForm(forms.ModelForm):

    class Meta:
        model = Rating
        fields = ['is_approved']


class NotifyMeForm(forms.ModelForm):
    email = forms.EmailField(required=False)
    is_guest = forms.BooleanField(required=False, initial=True, widget=forms.HiddenInput())
    class Meta:
        model = NotifyMe
        fields = ['remarks', 'email','is_guest']
 
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        is_guest = cleaned_data.get('is_guest')
        if not email and is_guest == True:
            raise forms.ValidationError("Email Required")



class NotifyMeUpdateStatusForm(forms.ModelForm):
    class Meta:
        model = NotifyMe
        fields = ['is_emailed']


class NotifyMeDeleteForm(forms.ModelForm):

    class Meta:
        model = NotifyMe
        fields = ['deleted_at']
        widgets = {
            'deleted_at': forms.HiddenInput(),
        }


class QuantityAddForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = ['quantity']
        widgets = {
            'deleted_at': forms.NumberInput(),
        }
    
class AdvertisementForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        exclude = ['deleted_at']

    # Adding Classes to each for CSS styling
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

class AdvertisementDeleteForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = ['deleted_at']
        widgets = {
            'deleted_at': forms.HiddenInput(),
        }
