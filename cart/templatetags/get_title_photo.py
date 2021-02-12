from django import template

register = template.Library()

@register.filter
def cover_photo(product):
    images = product.photos.filter(deleted_at=None).exclude(
        is_title_photo=False)
    print(images)
    if images.exists():
        return images[0].photo
        # strdata = str(images[0])
        # data = strdata.split('/media/')
        # return data[1]
    else:
        return
