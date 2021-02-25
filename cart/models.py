import os
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

User = settings.AUTH_USER_MODEL

RATE_CHOICES = (
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
    (5, 5),
)

SHIPMENT_CHOICES = (
    ('Order Placed', 'Order Placed'),
    ('Order Confirmed', 'Order Confirmed'),
    ('Order Processed', 'Order Processed'),
    ('Ready to Ship', 'Ready to Ship'),
    ('Out for Delivery', 'Out for Delivery'),    
    ('Delivered', 'Delivered'),    
)

SLIDER_CHOICES=(
    ('product','product'),
    ('category','category'),
 )

PAYMENT_CHOICES=(
    ('Cash on Delivery','Cash on Delivery'),
    ('Online Pay','Online Pay'),
    )

AD_CHOICES=(
    (1, 'ABOVE_FOOTER_LEFT'),
    (2, 'ABOVE_FOOTER_RIGHT'),
    (3, 'FULL_WIDTH_BELOW_SLIDER'),
    (4, 'FULL_WIDTH_BELOW_TODAYS_DEAL'),
    (5, 'FULL_WIDTH_BELOW_PRODUCTS_ON_SALE'),
    (6, 'FULL_WIDTH_BELOW_LATEST_PRODUCTS'),
    (7, 'HOMEPAGE_ROADBLOCK'),
    )


AD_DICT = {}
for indAd in AD_CHOICES:
    AD_DICT[str(indAd[0])]=str(indAd[1])


class Timestampable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_at = models.DateTimeField(auto_now_add=False, auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self):
        self.deleted_at = timezone.now()
        super().save()


class Photo(Timestampable):
    photo = models.ImageField("Photo")
    is_title_photo = models.BooleanField(default=False)
    title = models.CharField(
        "Photo Title", max_length=255, null=True, blank=True)

    def __str__(self):
        return str(self.photo.url)

    def imagename(self): 
        basename, extension = os.path.splitext(os.path.basename(self.photo.name)) 
        return basename


class Keywords(Timestampable):
    title = models.CharField("Title", max_length=255)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

class SubCategory(Timestampable):
    name = models.CharField("SubCategory Name", max_length=255)

    def __str__(self):
        return self.name


        
class Category(Timestampable):
    title = models.CharField("Category Title", max_length=255)
    slug = models.SlugField("Category Slug", unique=True)
    image = models.ImageField('category image', null=True, blank=True, upload_to='category/')
    description = models.TextField(
        "Category Description", null=True, blank=True)
    seo_title = models.CharField("Category Name", max_length=255, null=True, blank=True)
    seo_description = models.TextField("SEO Description", null=True, blank=True)
    seo_keywords = models.ManyToManyField(Keywords, blank=True)

    class Meta:
        # unique_together = ('slug')    
        verbose_name_plural = "categories"
        ordering = ["title"]

    def __str__(self):
        return self.title
    
    def imagename(self): 
        basename, extension = os.path.splitext(os.path.basename(self.image.name)) 
        return basename

    @property
    def get_seo_title(self):
        if self.seo_title:
            return self.seo_title
        return self.title

    @property
    def get_seo_description(self):
        if self.seo_description:
            return self.seo_description
        return self.description

    @property
    def get_seo_keywords(self):
        if self.seo_keywords.exists():
            return (','.join(str(item) for item in self.seo_keywords.all()))
        return self.title

class SubCategoryMapping(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name = 'category_mapping')
    sub_category = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, related_name = 'sub_category_mapping')

class Tag(Timestampable):
    title = models.CharField("Tag Title", max_length=255, unique=True)
    description = models.TextField(
        "Tag Description", null=True, blank=True)

    def __str__(self):
        return self.title


class Product(Timestampable):
    name = models.CharField("Product Name", max_length=255)
    product_weight = models.CharField(max_length=100, null= True, blank=True)
    slug = models.SlugField("Product Slug", unique=True, max_length=255)
    photos = models.ManyToManyField(Photo, blank=True)
    description = models.TextField("Product Description", null=True, blank=True)
    summary = models.TextField("Product Summary", blank=True)
    warning = models.TextField("Product Warning", null=True, blank=True)
    visibility = models.BooleanField("Product Visibility", default=True)
    reference_code = models.CharField(
        "Product Reference Code", max_length=128, null=True, blank=True)
    barcode = models.CharField(
        "Product Barcode", max_length=128, null=True, blank=True)
    quantity = models.CharField("Product Quantity",max_length=255, default=' ')
    categories = models.ManyToManyField(Category)
    owner = models.CharField(max_length=255, null=True, blank=True)
    tags = models.ManyToManyField(Tag)
    unit = models.CharField('product unit',max_length=255,default=' ')
    seo_title = models.CharField("SEO Title", max_length=255, null=True, blank=True)
    seo_description = models.TextField("SEO Description", null=True, blank=True)
    seo_keywords = models.ManyToManyField(Keywords, blank=True)
    old_price = models.FloatField("Old Price", default=0.0)
    price = models.FloatField("Product Price", default=0.0)
    vat = models.FloatField("VAT", default=10.0)
    vat_included = models.BooleanField("VAT Inclusive", default=False)
    vat_amount = models.FloatField("VAT Amount", default=0.0)
    discount_percent = models.FloatField("Discount Percentage", default=0.0)
    discount_amount = models.FloatField("Discounted Amount", default=0.0)
    grand_total = models.FloatField("Grand Total", default=0.0)
    expire_on = models.DateField(null=True, blank=True)
    is_new = models.BooleanField("New Product", default=True)
    is_on_sale = models.BooleanField("Product on Sale", default=False)
    is_coming_soon = models.BooleanField("Coming Soon", default=False)
    order_count = models.PositiveIntegerField(default=0)
    variant = models.ManyToManyField('self', blank=True)
    likes = models.IntegerField(default='0')
    priority = models.PositiveIntegerField(default=0)
    product_address = models.CharField(max_length=255,default='Kathmandu')
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def default_photo(self):
        return '/static/frontend/image/breadfruit-psd.png'
    
    @property
    def display_old_price(self):
        if self.discount_percent:
            return str(round(self.price))
        return str(round(self.old_price))

    @property
    def display_new_price(self):
        if self.discount_percent:
            return str(round(self.price - (self.discount_percent/100) * self.price))
        return str(round(self.price))

    @property
    def get_seo_title(self):
        if self.seo_title:
            return self.seo_title
        return self.name

    @property
    def get_seo_description(self):
        if self.seo_description:
            return self.seo_description 
        return self.summary

    @property
    def get_seo_keywords(self):
        if self.seo_keywords.exists():
            return self.seo_keywords.filter(deleted_at=None)
        return self.tags.filter(deleted_at=None)
    
    

class ProductInTransaction(Timestampable):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    # order_id = models.CharField(max_length=255)
    products = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.PositiveIntegerField("Product Quantity", default=1)
    is_ordered = models.BooleanField(default=False) #true
    is_taken = models.BooleanField(default=False) #true
    is_completed = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    
    def __str__(self):
        return self.products.name


class Cart(Timestampable):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    products = models.ForeignKey(ProductInTransaction, null=True, blank=True, related_name="carts", on_delete=models.CASCADE)
    order_id = models.CharField(max_length=255,null=True,blank=True)
    is_ordered = models.BooleanField('is_ordered',default=False)
    is_taken = models.BooleanField(default=False)
    is_cancelled = models.BooleanField('is_cancelled',default=False)
    is_completed = models.BooleanField('is_completed',default=False)

    def __str__(self):
        return str(self.user)

class Wishlist(Timestampable):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ForeignKey(ProductInTransaction, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.user.username


DISCUNT_CHOICES = (
    (1, "Percentage"),
    (2, "Flat")
)


class Coupon(Timestampable):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField("Coupon Title", max_length=255)
    code = models.CharField("Coupon Code", max_length=255)
    valid_from = models.DateTimeField("Valid From")
    valid_to = models.DateTimeField("Valid To")
    validity_count = models.PositiveIntegerField(
        "Validity Count", null=True, blank=True, default=1)
    discount_type = models.PositiveIntegerField(
        "Discount Type", choices=DISCUNT_CHOICES, default=1)
    discount_percent = models.FloatField("Discount Percentage", default=0)
    discount_amount = models.FloatField("Discount Amount", default=0)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Point(Timestampable):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_point = models.PositiveIntegerField("Total Points", default=0)

    def __str__(self):
        return self.user.username


class Status(Timestampable):
    name = models.CharField(choices=SHIPMENT_CHOICES,default="Order Placed", max_length=255, unique=True)

    def __str__(self):
        return self.name

class ProductRefund(Timestampable):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    products = models.ForeignKey(ProductInTransaction, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField("Product Quantity", default=0)

    class Meta:
        ordering =["-id"]

    def __str__(self):
        return str(self.pk)


class Order(Timestampable):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    products = models.ManyToManyField(ProductInTransaction, blank=True)
    refund = models.ManyToManyField(ProductRefund, blank=True) 
    email = models.EmailField(null=True, blank=True)
    contact_number = models.BigIntegerField(null=True, blank=True)
    shipped_date = models.DateField(null=True, blank=True, default=timezone.now)
    comment = models.TextField(blank=True)
    total = models.FloatField(default=0.0)
    condition_status = models.ForeignKey(Status, null=True, blank=True, on_delete=models.SET_NULL)
    code = models.CharField(max_length=50, unique=True)
    remarks = models.TextField(blank=True)
    is_confirmed = models.BooleanField(default=False)
    payment_type = models.CharField(max_length=20,choices=PAYMENT_CHOICES,default="Cash on Delivery")
    label = models.FileField(null=True, blank=True)



    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.code)

    def grand_total(self):
        total = 0
        discount = 0
        vat = 0
        for product in self.products.all(): 
            prod = str(product.products.name)  
            total_amt = product.products.price * product.quantity
            total = total + total_amt
            discount_amt = float(total_amt*product.products.discount_percent)/100
            discount = discount + discount_amt
            vat_amt = (float(total_amt-discount_amt)*product.products.vat)/100
            vat = vat+ vat_amt
        grand_total = total - discount + vat
        self.total = grand_total
        self.save()
        return self.total

class Tracker(Timestampable):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    status = models.ManyToManyField(Status, blank=True)
    remarks = models.TextField(blank=True)
    estimated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class FeaturedProduct(models.Model):
    products = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_at = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.products.name


class Slider(Timestampable):
    title = models.CharField(
        "Slider Title", max_length=200, null=True, blank=True)
    photos = models.ImageField("Slider Image")
    status = models.BooleanField(default=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    slider_type = models.CharField(max_length=20,choices=SLIDER_CHOICES, null=True, blank=True)
    category = models.ForeignKey(Category,null=True,blank=True, on_delete=models.SET_NULL)
    product =  models.ForeignKey(Product,null=True,blank=True, on_delete=models.SET_NULL)
    color_code = models.CharField(max_length=6,null=True, blank=True,default='2e9aff')

    def __str__(self):
        return self.title


class SiteConfig(Timestampable):
    key = models.CharField("Site Config Key", max_length=255)
    value = models.TextField("Site Config Value")

    def __str__(self):
        return self.key


class Rating(Timestampable):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rate = models.IntegerField(choices=RATE_CHOICES, null=True, blank=True)
    review = models.TextField(null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

# Oraganization and model number removed Emergency contact number=Contact number 2(ptional field (blank/null=true))
class Inquiry(Timestampable):
    name = models.CharField(max_length=100)
    # organization = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField()
    contact_number_1 = models.BigIntegerField()
    contact_number_2 = models.BigIntegerField(null=True, blank=True)
    product = models.CharField(max_length=255)
    # model_number = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(blank=True)
    is_responded = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Sales(Timestampable):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    delivered_date = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.pk)


class NotifyMe(Timestampable):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    email = models.EmailField()
    remarks = models.TextField(blank=True)
    is_emailed = models.BooleanField(default=False)
    is_read = models.BooleanField(default= False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.product.name


class RecentlyViewed(Timestampable):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.user.username


class Advertisement(Timestampable):
    title = models.CharField('Title', max_length=50, default=" ")
    embed_code=models.CharField(max_length=255,default=" ")
    priority = models.PositiveIntegerField(default=0)
    ad_type = models.IntegerField(choices=AD_CHOICES,default=1)

    def what_is(self):
        return AD_DICT[str(self.ad_type)]

    def __str__(self):
        return str(self.ad_type)



class Sender(Timestampable):
    sender_line_1 = models.CharField(max_length=100)
    postal_address = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    country = models.CharField(max_length=20)
    sender_code = models.CharField(max_length=100)
    sender_drop_center_code = models.CharField(max_length=100)
    sender_phone = models.CharField(max_length=100, null=True,blank=True )


    def __str__(self):
        return self.sender_line_1

# class ProductWeight(Timestampable):
#     # product_name = models.CharField(max_length=100)
#     product_wt = models.CharField(max_length=100)

#     def __str__(self):
#         return self.product_wt

# class Ship(Timestampable):
#     name = models.CharField(max_length=100)
#     address = models.CharField(max_length=100)
#     postal_address = models.CharField(max_length=100, null=True, blank=True)
#     country = models.CharField(max_length=100, null=True, blank=True)
#     product = models.ManyToManyField(ProductWeight)
#     label = models.FileField(null=True, blank=True)

#     def __str__(self):
#        return self.nameInformation

class Tracking(Timestampable):
    name = models.CharField(max_length=100, default="")

class OrderTracking(Timestampable):
    trackingcode = models.CharField(max_length=100)
    order = models.ForeignKey(Order, on_delete=models.CASCADE,default=1)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)

class File(models.Model):
    content = models.FileField()

class Story(models.Model):
    content_choices = ('Image','Image'),('Video','Video')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True,null=True)
    content_type = models.CharField(choices=content_choices,max_length=255, default='')
    source = models.ManyToManyField(File, blank=True)
    
    def __str__(self):
        return self.content_type