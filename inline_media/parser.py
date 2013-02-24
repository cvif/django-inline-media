# code borrowed from django-basic-apps by Nathan Borror
# https://github.com/nathanborror/django-basic-apps

import re

from django.template import TemplateSyntaxError
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.utils.encoding import smart_unicode
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

try:
    from BeautifulSoup import BeautifulSoup, NavigableString
except ImportError:
    from beautifulsoup import BeautifulSoup, NavigableString

from inline_media.conf import settings


def inlines(value, return_list=False):
    selfClosingTags = ['inline','img','br','input','meta','link','hr',]
    soup = BeautifulSoup(value, selfClosingTags=selfClosingTags)
    inline_list = []
    if return_list:
        for inline in soup.findAll('inline'):
            rendered_inline = render_inline(inline)
            if rendered_inline:
                inline_list.append(rendered_inline['context'])
        return inline_list
    else:
        for inline in soup.findAll('inline'):
            rendered_inline = render_inline(inline)
            if rendered_inline:
                rendered_item = BeautifulSoup(
                    render_to_string(rendered_inline['template'], 
                                     rendered_inline['context']),
                    selfClosingTags=selfClosingTags)
            else:
                rendered_item = ''
            inline.replaceWith(rendered_item)
        return mark_safe(soup)


#--------------------------------------------------
# Helpers for function 'render_inline'

def get_app_model_tuple(inline):
    """Retrieve app_label and model_name strings from a given inline tag.

    :param BeautifulSoup.Tag inline: Inline element found in a beautiful soup.
    """
    try:
        inline_type = inline['type']
        chunks = inline_type.split('.')
        app_label = '.'.join(chunks[:-1])
        model_name = chunks[-1]
    except:
        if settings.INLINE_MEDIA_DEBUG:
            raise TemplateSyntaxError, _(u"Couldn't find the attribute "
                                         "'type' in the <inline> tag.")
        return ''
    else:
        return app_label, model_name


def get_model(app_label, model_name):
    """Retrive the model class from a given app_label & model strings."""
    try:
        content_type = ContentType.objects.get(app_label=app_label, 
                                               model=model_name)
        model = content_type.model_class()
    except ContentType.DoesNotExist:
        if settings.INLINE_MEDIA_DEBUG:
            raise TemplateSyntaxError, _(u"Inline ContentType not found.")
        return None
    return model


def get_css_class(inline):
    """Retrieve the CSS class from a given inline tag."""
    try:
        css_class = smart_unicode(inline['class'])
    except:
        if settings.INLINE_MEDIA_DEBUG:
            raise TemplateSyntaxError, _(u"Couldn't find the attribute "
                                         "'class' in the <inline> tag.")
        return ''
    return css_class


size_regexp = re.compile(r'^inline_(?P<size_class>\w+)_\w+$')

def get_size(inline_type, css_class):
    """Get the size for the given inline tag.
    
    :param str inline_type: an 'app_label.model_name' for an inline type.
    :param str css_class: any of the valid inline_media css classes.
    
    Valid values for css_class are:
    'inline_(mini|small|medium|large|full)_(left|right)' and
    'inline_full_center'.

    Inline type registration in INLINE_MEDIA_CUSTOM_SIZES is not mandatory.
    It might be that the 'inline_type' is not registered in the setting,
    but if the 'css_class' is correct, a template will be use to render the 
    inline. 
    """
    match = size_regexp.match(css_class)
    if match:
        size_class = match.group('size_class')
    else:
        size_class = None
    custom_sizes = settings.INLINE_MEDIA_CUSTOM_SIZES.get(inline_type, None)
    if custom_sizes and custom_sizes.has_key(size_class):
        size = custom_sizes[size_class]
        if not size:
            size_class = None
        if type(size) == int:
            size = '%d' % size
        elif type(size) == tuple:
            size = '%dx%d' % size
    else:
        size = None
    return (size, size_class)


def render_inline(inline):
    """
    Replace inline markup with template markup that matches the
    appropriate app and model.

    """
    app_label, model_name = get_app_model_tuple(inline)
    model = get_model(app_label, model_name)
    css_class = get_css_class(inline)
    size, size_class = get_size(inline['type'], css_class)

    if not size_class: 
        if settings.INLINE_MEDIA_DEBUG:
            raise Exception("Size for class '%s' is explicitly disabled "
                            "in settings.INLINE_MEDIA_CUSTOM_SIZES "
                            "for app.model '%s.%s'." % (app_label, model_name))
        else:
            return ""
        
    try:
        obj = model.objects.get(pk=inline['id'])
        context = { 'content_type':"%s.%s" % (app_label, model_name), 
                    'object':obj, 
                    'class': css_class,
                    'size': size }
    except model.DoesNotExist:
        if settings.INLINE_MEDIA_DEBUG:
            raise model.DoesNotExist("Object matching '%s' does not exist")
        else:
            return ""
    except:
        if settings.INLINE_MEDIA_DEBUG:
            raise TemplateSyntaxError("The <inline> id attribute is "
                                      "missing or invalid.")
        else:
            return ""

    rendered_inline = {
        'template': [
            "inline_media/%s.%s.%s.html" % (app_label, model_name, size_class),
            "inline_media/%s.%s.default.html" % (app_label, model_name) ],
        'context': context}
    return rendered_inline
