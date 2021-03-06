from rest_framework import serializers
from cart.models import Product

class AddProductsSerializers(serializers.Serializer):
    product_name = serializers.CharField()
    product_weight = serializers.CharField()
    product_slug = serializers.CharField()
    # photos = serializers.ImageField()
    description = serializers.CharField()
    summary = serializers.CharField()
    warning = serializers.CharField()
    quantity = serializers.CharField()
    category_title = serializers.CharField()
    category_slug = serializers.CharField()
    category_image = serializers.ImageField()
    sub_categories = serializers.CharField()
    owner = serializers.CharField()
    tags = serializers.CharField()
    unit = serializers.CharField()
    price = serializers.CharField()
    discount_percent = serializers.CharField()
    product_address = serializers.CharField()

    seo_title = serializers.CharField(required=False)
    seo_description = serializers.CharField(required=False)
    seo_keywords = serializers.CharField(required=False)
    vat = serializers.CharField(required=False)
    vat_included = serializers.CharField(required=False)
    vat_amount = serializers.CharField(required=False)
    expire_on = serializers.CharField(required=False)
    is_new = serializers.CharField(required=False)
    is_on_sale = serializers.CharField(required=False)
    is_coming_soon = serializers.CharField(required=False)
    variant = serializers.CharField(required=False)
    priority = serializers.CharField(required=False)
    category_description = serializers.CharField(required=False)

class ProductIDSerializer(serializers.Serializer):
    product_id = serializers.CharField()