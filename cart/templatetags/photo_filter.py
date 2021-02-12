from django import template
import urllib, base64
from io import StringIO


register = template.Library()

@register.filter
def not_deleted_photos(product):
    images = product.photos.filter(deleted_at=None)
    return images


@register.filter
def get64(url):
    """
    	Method returning base64 image data instead of URL
    """
    if url.startswith("http"):
        image = StringIO(urllib.urlopen(url).read())
        return 'data:image/jpg;base64,' + base64.b64encode(image.read())
    return 'http://breadfruit.prixa.net' + url
