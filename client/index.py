import hashlib
import json
import random
import re
import urllib.parse as parse
import urllib.request as request
from urllib.error import HTTPError

import library.local_server as local_server
from . import AUTH_SERVER_PORT, CLIENT_PORT, RESOURCE_SERVER_PORT, HOST, CLIENT_ID
from .credentials import Credentials, SESSIONS


def generateCode():
    m = hashlib.sha256()
    m.update(bytes(str(random.random()), encoding='ascii'))
    return m.hexdigest()


def get_user_info(access_token):
    req = request.urlopen('http://%s:%d/info?token=%s' % (HOST, RESOURCE_SERVER_PORT, access_token))
    return req.read().decode('utf-8')


def get_user_images(access_token):
    req = request.urlopen('http://%s:%d/images?token=%s' % (HOST, RESOURCE_SERVER_PORT, access_token))
    return req.read().decode('utf-8')


class Handler(local_server.Handler):
    def do_GET(self):
        try:
            parsed = parse.urlparse(self.path)
            query = dict(parse.parse_qsl(parsed.query))
            cookies = self.headers.get('Cookie') or ''
            search_session = re.search(r'SESSIONID=\b(\w+)\b', cookies)
            if parsed.path == '/':
                if search_session is not None and SESSIONS.get(search_session.group(1)) is not None:
                    self.redirect('http://%s:%d/user' % (HOST, CLIENT_PORT))
                else:
                    authorization_code = '<a href="http://%s:%d/login?%s">Authorization Code</a>' % (
                        HOST,
                        AUTH_SERVER_PORT,
                        parse.urlencode(
                            {
                                'redirect_url': 'http://%s:%d/redirect' % (HOST, CLIENT_PORT),
                                'client_id': CLIENT_ID,
                                'scopes': 'read_image,read_profile'
                            }))
                    body = '<!DOCTYPE html><html><body><h1>Welcome to client</h1><p>%s</p></body></html>' % (
                        authorization_code)
                    self.ok(body)
            elif parsed.path == '/redirect':
                code = query.get('code')
                assert code is not None, 'Auth code not found'
                session_id = generateCode()
                SESSIONS.setdefault(session_id, {'oauth2': Credentials.fromAuthCode(code)})
                self.redirect('http://%s:%d/user' % (HOST, CLIENT_PORT), headers={
                    "Set-Cookie": 'SESSIONID=%s; httponly' % (session_id)
                }.items())
            elif parsed.path == '/user':
                assert search_session and SESSIONS.get(search_session.group(1)), 'Session not found'
                oauth2 = SESSIONS.get(search_session.group(1)).get('oauth2')
                token = oauth2.access_token
                user = get_user_info(token)
                images = json.loads(get_user_images(token)) or []
                body = '<h1>Hello %s</h1><p><h3>You have these images</h3>%s</p>' % (
                    user, '\r\n'.join(['<div>%s</div>' % image for image in images]))
                self.ok(body)
        except HTTPError as e:
            print(e.fp.read())
            self.error(e)
        except BaseException as e:
            self.error(e)


def run():
    local_server.serve(CLIENT_PORT, Handler)
