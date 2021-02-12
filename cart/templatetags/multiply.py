from django import template

register = template.Library()

@register.filter
def multiply_qty_price(qty, price):
    return qty * price


@register.filter
def multiply_for_vat(qty, vat):
    return qty * vat


@register.filter
def multiply_for_discount(qty, discount):
    return qty * discount


@register.filter
def round_up(amount):
	amount = float(amount)

	return int(round(amount))

