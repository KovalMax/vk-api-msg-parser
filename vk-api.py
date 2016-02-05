#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib2, json, sys, cookielib, urllib, datetime
from urlparse import urlparse
from formparser import FormParser
from config import Credentials

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
        self.login = Credentials.login
        self.password = Credentials.password

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
        self.currentParseId = userId
        historyUrl = 'https://api.vk.com/method/messages.getHistory?user_id=%s&count=%s&rev=%s&v=5.44&access_token=%s' % (userId, count, reverse, token)
        history = urllib2.urlopen(historyUrl).read()
        return history

    def getUserName(self, token):
        userUrl = 'https://api.vk.com/method/users.get?user_ids=%s&v=5.44&access_token=%s' % (self.currentParseId, token)
        user = urllib2.urlopen(userUrl).read()
        user = json.loads(user)
        for chatName in user['response']:
            user = chatName['first_name'] + ' ' + chatName['last_name'] + ': '
            self.fileName = 'chat' + chatName['first_name'] + chatName['last_name'] + '.txt'
        return user

object = Auth('5255792', 'http://oauth.vk.com/blank.html', 'touch', '9999999', 'token', '5.44')

auth = object.authUrl(object.login, object.password)

giveAccess = object.giveAccess(auth)

token = object.returnToken(giveAccess)

userHistory = json.loads(object.getHistory('id of user to parse messages', '200', '1', token))

chatName = object.getUserName(token)

file_log = open(object.fileName, 'a+')

for item in userHistory['response']['items']:
    fromUser = chatName if item.get('from_id') == item.get('user_id') else 'Me: '
    
    date = datetime.datetime.fromtimestamp(int(item.get('date'))).strftime('%d-%m-%Y %H:%M:%S')

    file_log.write(
        date 
        + '\t'
        + fromUser.encode('utf-8', 'ignore')
        + '\t'
        + item.get('body').encode('utf-8', 'ignore')
    )

    if(item.get('attachments')):
        for attach in item.get('attachments'):
            if attach['type'] == 'sticker':
                file_log.write('\t' + attach['type'] + ': ' + attach['sticker']['photo_64'])
            elif attach['type'] == 'photo':
                photoLink = attach['photo']['photo_1280'] if 'photo_1280' in attach['photo'] else attach['photo']['photo_807']
                file_log.write('\t' + attach['type'] + ': ' + photoLink)
            elif attach['type'] == 'link':
                file_log.write('\t' + attach['type'] + ': ' + attach['link']['url'])
            else:
                file_log.write('\t' + attach['type'])
                
    if(item.get('emoji')):
        file_log.write('\t' + 'here must be a smile :)')
    file_log.write('\n')

file_log.write('------------------------------------------------------'*2 + '\n')
file_log.close()
