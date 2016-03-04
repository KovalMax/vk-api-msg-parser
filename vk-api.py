#!/usr/bin/python
# -*- coding: utf-8 -*-
import cookielib
import datetime
import json
import time
import urllib
import urllib2
from urlparse import urlparse
from config import Credentials
from formparser import FormParser


class Auth:
    def __init__(self, client_id, redirect, display, permissions, response_type, version):
        self.current_parse_id = ''

        self.file_name = ''

        self.api_url = 'https://api.vk.com/method/'

        self.data = {
            'client_id': client_id,
            'redirect_uri': redirect,
            'display': display,
            'scope': permissions,
            'response_type': response_type,
            'v': version
        }

        self.opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(cookielib.CookieJar()),
            urllib2.HTTPRedirectHandler()
        )

        self.offset = 0
        self.count = 200
        self.login = Credentials.login
        self.password = Credentials.password

    def auth_url(self):
        url = 'https://oauth.vk.com/authorize?'

        for param in self.data:
            url += '%s=%s&' % (param, self.data[param])

        auth_object = self.opener.open(url)
        form = auth_object.read()

        parser = FormParser()
        parser.feed(form)
        parser.close()
        parser.params['email'] = self.login
        parser.params['pass'] = self.password

        auth_object = self.opener.open(parser.url, urllib.urlencode(parser.params))
        return auth_object.read()

    def give_access(self, form):
        parser = FormParser()
        parser.feed(form)
        parser.close()

        access = self.opener.open(parser.url, urllib.urlencode(parser.params))
        return access.geturl()

    @staticmethod
    def split_key_value(kv_pair):
        result = kv_pair.split("=")
        return result[0], result[1]

    def return_token(self, url):
        result = dict(self.split_key_value(kvPair) for kvPair in urlparse(url).fragment.split('&'))
        return result['access_token']

    def get_history(self, user_id, reverse, vk_token):
        self.current_parse_id = user_id
        history_url = self.api_url + 'messages.getHistory?user_id=%s&count=%s&offset=%s&rev=%s&v=5.44&access_token=%s'\
                                     % (user_id, self.count, self.offset, reverse, vk_token)
        history = urllib2.urlopen(history_url).read()
        return history

    def get_user_name(self, vk_token):
        user_url = self.api_url + 'users.get?user_ids=%s&v=5.44&access_token=%s' % \
                   (self.current_parse_id, vk_token)

        user = urllib2.urlopen(user_url).read()
        user = json.loads(user)
        for chat_name in user['response']:
            user = chat_name['first_name'] + ' ' + chat_name['last_name'] + ': '
            self.file_name = 'chat' + chat_name['first_name'] + chat_name['last_name'] + '.txt'
        return user

    def get_video(self, video_to_find, vk_token):
        video_url = self.api_url + 'video.get?videos=%s&v=5.44&access_token=%s' % (video_to_find, vk_token)
        video = urllib2.urlopen(video_url).read()
        video = json.loads(video)
        if video['response']['count']:
            for video_link in video['response']['items']:
                video = video_link.get('player')
        else:
            video = 'Video not found'
        return video


vk_object = Auth('vk_client_id', 'http://oauth.vk.com/blank.html', 'touch', '9999999', 'token', '5.44')

authorize = vk_object.auth_url()

access_object = vk_object.give_access(authorize)

token = vk_object.return_token(access_object)

parsing = True

result_history = []

while parsing:
    user_history = json.loads(vk_object.get_history('user_id_to_parse', '1', token))

    print 'count of founded messages: ' + str(len(user_history['response']['items']))

    print 'offset: ' + str(vk_object.offset)

    if len(user_history['response']['items']) >= 199:
        vk_object.offset += 200

        result_history += user_history['response']['items']

        time.sleep(0.4)
    else:
        result_history += user_history['response']['items']

        parsing = False

print 'total count of founded messages: ' + str(len(result_history))

vk_chat_name = vk_object.get_user_name(token)

file_log = open(vk_object.file_name, 'a+')

for item in result_history:
    from_user = vk_chat_name if item.get('from_id') == item.get('user_id') else 'Me: '

    date = datetime.datetime.fromtimestamp(int(item.get('date'))).strftime('%d-%m-%Y %H:%M:%S')

    file_log.write(
        date + '\t' + from_user.encode('utf-8', 'ignore') + '\t' + item.get('body').encode('utf-8', 'ignore')
    )

    if item.get('attachments'):
        for attach in item.get('attachments'):
            if attach['type'] == 'sticker':
                file_log.write('\t' + attach['type'] + ': ' + attach['sticker']['photo_64'])
            elif attach['type'] == 'photo':
                photo_sizes = ['photo_75', 'photo_130', 'photo_604', 'photo_807', 'photo_1280', 'photo_2560']

                photo_link = 'link not found'

                for size in photo_sizes:
                    if size in attach['photo']:
                        photo_link = attach['photo'][size]

                file_log.write('\t' + attach['type'] + ': ' + photo_link)
            elif attach['type'] == 'link':
                file_log.write('\t' + attach['type'] + ': ' + attach['link']['url'])
            elif attach['type'] == 'video':
                find_this_video = str(attach['video']['owner_id']) + '_' + str(attach['video']['id'])

                vk_video_link = vk_object.get_video(find_this_video, token)

                file_log.write('\t' + attach['type'] + ': ' + vk_video_link)
            else:
                file_log.write('\t' + attach['type'])

    file_log.write('\n')

file_log.write('------------------------------------------------------' * 2 + '\n')
file_log.close()
