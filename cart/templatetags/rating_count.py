from django import template
from cart.models import Rating

register = template.Library()

@register.filter
def stars(number):
    if number == 0:
            stars = '<i class="fa fa-star-o"></i>&nbsp;' * 5
    elif number == 1:
        stars = '<i class="fa fa-star"></i>&nbsp;' * 1 + '<i class="fa fa-star-o"></i>&nbsp;' * 4
    elif number == 2:
        stars = '<i class="fa fa-star"></i>&nbsp;' * 2 + '<i class="fa fa-star-o"></i>&nbsp;' * 3
    elif number == 3:
        stars = '<i class="fa fa-star"></i>&nbsp;' * 3 + '<i class="fa fa-star-o"></i>&nbsp;' * 2
    elif number == 4:
        stars = '<i class="fa fa-star"></i>&nbsp;' * 4 + '<i class="fa fa-star-o"></i>&nbsp;' * 1
    else:
        stars = '<i class="fa fa-star-o"></i>&nbsp;' * 5
    return stars


@register.filter
def rating(product):
    ratings = Rating.objects.filter(product__id=product.id).exclude(rate=None)
    if ratings.exists():
        total_rating = 0
        count = ratings.count()
        for rate in ratings:
            total_rating += rate.rate
        rating_avg = total_rating / count
        rate = rating_avg
        if rate == 0:
            stars = '<i class="fa fa-star-o"></i>&nbsp;' * 5
        elif rate == 1:
            stars = '<i class="fa fa-star"></i>&nbsp;' * 1 + '<i class="fa fa-star-o"></i>&nbsp;' * 4
        elif rate == 2:
            stars = '<i class="fa fa-star"></i>&nbsp;' * 2 + '<i class="fa fa-star-o"></i>&nbsp;' * 3
        elif rate == 3:
            stars = '<i class="fa fa-star"></i>&nbsp;' * 3 + '<i class="fa fa-star-o"></i>&nbsp;' * 2
        elif rate == 4:
            stars = '<i class="fa fa-star"></i>&nbsp;' * 4 + '<i class="fa fa-star-o"></i>&nbsp;' * 1
        else:
            stars = '<i class="fa fa-star-o"></i>&nbsp;' * 5

    else:
        stars = '<i class="fa fa-star-o"></i>&nbsp;' * 5
    return stars
