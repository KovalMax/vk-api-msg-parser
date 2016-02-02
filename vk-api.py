#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib2, json, sys, cookielib, urllib, datetime
from urlparse import urlparse
from HTMLParser import HTMLParser

class FormParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.url = None
        self.params = {}
        self.in_form = False
        self.form_parsed = False
        self.method = "GET"

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "form":
            if self.form_parsed:
                raise RuntimeError("Second form on page")
            if self.in_form:
                raise RuntimeError("Already in form")
            self.in_form = True
        if not self.in_form:
            return
        attrs = dict((name.lower(), value) for name, value in attrs)
        if tag == "form":
            self.url = attrs["action"]
            if "method" in attrs:
                self.method = attrs["method"].upper()
        elif tag == "input" and "type" in attrs and "name" in attrs:
            if attrs["type"] in ["hidden", "text", "password"]:
                self.params[attrs["name"]] = attrs["value"] if "value" in attrs else ""

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "form":
            if not self.in_form:
                raise RuntimeError("Unexpected end of <form>")
            self.in_form = False
            self.form_parsed = True

class Auth:
    def __init__(self, clientId, redirect, display, permissions, responseType, version):
        self.data = {
            'client_id' : clientId,
            'redirect_uri' : redirect,
            'display' : display,
            'scope' : permissions,
            'response_type' : responseType,
            'v' : version
        }

        self.opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(cookielib.CookieJar()),
            urllib2.HTTPRedirectHandler()
        )
        self.login = 'your login'
        self.password = 'your password'
        self.userToParse = 'your friend-id' 

    def authUrl(self, email, password):
        url = 'https://oauth.vk.com/authorize?'

        for param in self.data:
            url += '%s=%s&' % (param, self.data[param])
        
        auth = self.opener.open(url)
        form = auth.read()

        parser = FormParser()
        parser.feed(form)
        parser.close
        parser.params['email'] = email
        parser.params['pass'] = password

        auth = self.opener.open(parser.url, urllib.urlencode(parser.params))
        return auth.read()

    def giveAccess(self, form):
        parser = FormParser()
        parser.feed(form)
        parser.close

        access = self.opener.open(parser.url, urllib.urlencode(parser.params))
        return access.geturl()

    def splitKeyValue(self, kvPair):
        result = kvPair.split("=")
        return result[0], result[1]

    def returnToken(self, url):
        result = dict(self.splitKeyValue(kvPair) for kvPair in urlparse(url).fragment.split('&'))
        return result['access_token']

    def getDialogs(self, count, token):
        dialogUrl = 'https://api.vk.com/method/messages.getDialogs?count=%s&preview_length=0&v=5.44&access_token=%s' % (count, token)
        dialogs = urllib2.urlopen(dialogUrl).read()
        return dialogs

    def getHistory(self, userId, count, reverse, token):
        historyUrl = 'https://api.vk.com/method/messages.getHistory?user_id=%s&count=%s&rev=%s&v=5.44&access_token=%s' % (userId, count, reverse, token)
        history = urllib2.urlopen(historyUrl).read()
        return history


object = Auth('5255792', 'http://oauth.vk.com/blank.html', 'touch', '9999999', 'token', '5.44')

auth = object.authUrl(object.login, object.password)

giveAccess = object.giveAccess(auth)

token = object.returnToken(giveAccess)

file_log = open('someFile.txt', 'a+')
file_log.truncate(0)

userHistory = json.loads(object.getHistory(object.userToParse, '200', '1', token))

for item in userHistory['response']['items']:
    date = datetime.datetime.fromtimestamp(int(item.get('date'))).strftime('%d-%m-%Y %H:%M:%S')
    file_log.write(date + '\t' + item.get('body').encode('utf-8', 'ignore') + '\n')

file_log.close()
