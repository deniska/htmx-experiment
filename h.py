from html import escape
import functools

class HTMLElement:
    def __init__(self, tag, attrs, content, self_closing):
        self.tag = tag
        self.attrs = attrs
        self.content = content
        self.self_closing = self_closing

    def render(self, parts):
        a = parts.append
        a('<')
        a(self.tag)
        for k, v in self.attrs.items():
            if isinstance(v, list):
                v = ' '.join(v)
            a(' ')
            a(k)
            a('="')
            a(escape_attr(v))
            a('"')
        a('>')
        if not self.self_closing:
            for thing in self.content:
                thing.render(parts)
            a('</')
            a(self.tag)
            a('>')

class SafeString:
    def __init__(self, s):
        self.s = s

    def render(self, parts):
        parts.append(escape(self.s))

class DangerString:
    def __init__(self, s):
        self.s = s

    def render(self, parts):
        parts.append(self.s)

class Helper:
    def __init__(self, tag, self_closing=False):
        self.tag = tag
        self.self_closing = False

    def __call__(self, *args):
        attrs = {}
        content = []
        for arg in args:
            if isinstance(arg, (HTMLElement, SafeString, DangerString)):
                content.append(arg)
            elif isinstance(arg, str):
                content.append(SafeString(arg))
            elif isinstance(arg, dict):
                attrs = arg
            else:
                raise TypeError('Unexpected type')
        return HTMLElement(self.tag, attrs, content, self.self_closing)

def _render(renderable):
    parts = ['<!DOCTYPE html>\n']
    renderable.render(parts)
    return ''.join(parts)

def escape_attr(s):
    return s.replace('&', '&amp;').replace('"', '&#34;')

class HBo:
    name = 'hbo'
    api = 2

    def apply(self, cb, route):
        @functools.wraps(cb)
        def wrapper(*args, **kwargs):
            result = cb(*args, **kwargs)
            if isinstance(result, (HTMLElement, SafeString, DangerString)):
                return _render(result)
            return result
        return wrapper

html = Helper('html')
head = Helper('head')
body = Helper('body')
title = Helper('title')
a = Helper('a')
div = Helper('div')
span = Helper('span')
h1 = Helper('h1')
form = Helper('form')
label = Helper('label')
button = Helper('button')
input = Helper('input', self_closing=True)
style = Helper('style')
script = Helper('script')
