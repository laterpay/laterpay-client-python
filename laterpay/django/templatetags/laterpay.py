import re
from django.template import Library

register = Library()


def render_laterpay_header(context):
    laterpay = context['request'].laterpay

    # strip the protocol
    web_root = re.sub('^https?://', '', laterpay.web_root)

    return {'web_root': web_root}

register.inclusion_tag('laterpay/inclusion/render_header.html', takes_context=True)(render_laterpay_header)


def render_laterpay_footer(context, identify_callback=None):
    if identify_callback == '':
        identify_callback = None
    laterpay = context['request'].laterpay
    return {'identify_url': laterpay.get_identify_url(identify_callback)}

register.inclusion_tag('laterpay/inclusion/render_footer.html', takes_context=True)(render_laterpay_footer)


def laterpay_subscribe(context, product_key=None, subscription_key=None):
    laterpay = context['request'].laterpay
    return laterpay.get_subscription_url(product_key, subscription_key)

register.simple_tag(takes_context=True)(laterpay_subscribe)


def laterpay_buy(context, item_definition, product_key=None):
    laterpay = context['request'].laterpay
    return laterpay.get_buy_url(item_definition, product_key)

register.simple_tag(takes_context=True)(laterpay_buy)
