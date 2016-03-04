#!/usr/bin/python
# -*- coding: utf-8 -*-
from HTMLParser import HTMLParser


class FormParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.url = None
        self.params = {}
        self.in_form = False
        self.form_parsed = False
        self.method = "GET"

    def handle_starttag(self, tag, attributes):
        tag = tag.lower()
        if tag == "form":
            if self.form_parsed:
                raise RuntimeError("Second form on page")
            if self.in_form:
                raise RuntimeError("Already in form")
            self.in_form = True
        if not self.in_form:
            return
        attributes = dict((name.lower(), value) for name, value in attributes)
        if tag == "form":
            self.url = attributes["action"]
            if "method" in attributes:
                self.method = attributes["method"].upper()
        elif tag == "input" and "type" in attributes and "name" in attributes:
            if attributes["type"] in ["hidden", "text", "password"]:
                self.params[attributes["name"]] = attributes["value"] if "value" in attributes else ""

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "form":
            if not self.in_form:
                raise RuntimeError("Unexpected end of <form>")
            self.in_form = False
            self.form_parsed = True
