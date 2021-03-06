import hashlib
import json
import random
import re
import urllib.parse as parse
import urllib.request as request
from urllib.error import HTTPError

import library.local_server as local_server
from . import AUTH_SERVER_PORT, CLIENT_PORT, RESOURCE_SERVER_PORT, HOST, CLIENT_ID, CLIENT_SECRET
from .credentials import Credentials, SESSIONS


def generateCode():
    m = hashlib.sha256()
    m.update(bytes(str(random.random()), encoding='ascii'))
    return m.hexdigest()


def get_user_info(access_token):
    r = request.Request('http://%s:%d/info' % (HOST, RESOURCE_SERVER_PORT), headers={
        'Authorization': 'Bearer %s' % access_token
    })
    req = request.urlopen(r)
    return req.read().decode('utf-8')


def get_user_images(access_token):
    r = request.Request('http://%s:%d/images' % (HOST, RESOURCE_SERVER_PORT), headers={
        'Authorization': 'Bearer %s' % access_token
    })
    req = request.urlopen(r)
    return req.read().decode('utf-8')


def login(username, password):
    req = request.Request('http://%s:%d/login?response_type=%s&scopes=%s' % (
        HOST, AUTH_SERVER_PORT, 'official_client', 'read_image,read_profile'
    ), method='POST')

    result = request.urlopen(req, data=parse.urlencode({
        'username': username,
        'pw': password
    }).encode('utf-8')).read().decode('utf-8')
    result = json.loads(result)
    return {key: result.get(key) for key in ('access_token', 'expires_in', 'start_time', 'refresh_token', 'scopes')}


def client_login():
    req = request.Request('http://%s:%d/login?response_type=%s&scopes=%s' % (
        HOST, AUTH_SERVER_PORT, 'client_credentials', 'read_image,read_profile'
    ), method='POST')
    result = request.urlopen(req, data=parse.urlencode({
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }).encode('utf-8')).read().decode('utf-8')
    result = json.loads(result)
    return {key: result.get(key) for key in ('access_token', 'expires_in', 'start_time', 'scopes')}


class ClientHandler(local_server.Handler):

    def do_POST(self):
        parsed = parse.urlparse(self.path)
        if parsed.path == '/ropc_login':
            content_length = int(self.headers['Content-Length'])
            q = dict(parse.parse_qsl(self.rfile.read(content_length)))
            result = login(*[q.get(x).decode('utf-8') for x in [b'username', b'pw']])
            session_id = generateCode()
            SESSIONS.setdefault(session_id, {'oauth2': Credentials(result)})
            self.redirect('http://%s:%d/user' % (HOST, CLIENT_PORT), headers={
                "Set-Cookie": 'SESSIONID=%s; httponly' % (session_id)
            }.items())

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
                                'scopes': 'read_image,read_profile',
                                'response_type': 'code'
                            }))
                    implicit_grant = '<a href="http://%s:%d/login?%s">Implicit Grant (For client side js application)</a>' % (
                        HOST,
                        AUTH_SERVER_PORT,
                        parse.urlencode({
                            'redirect_url': 'http://%s:%d/redirect_implicit_grant' % (HOST, CLIENT_PORT),
                            'client_id': CLIENT_ID,
                            'scopes': 'read_image,read_profile',
                            'response_type': 'token'
                        })
                    )
                    res_pass = '<a href="http://%s:%d/ropc_login">Resource Owner Password Credentials (For offical apps)</a>' % (
                        HOST,
                        CLIENT_PORT
                    )
                    client_id_client_secret = '<a href="http://%s:%d/cc_login">Client ID Client Secret (For confidential client, protected resources owned by client itself)</a>' % (
                        HOST,
                        CLIENT_PORT
                    )
                    body = '<!DOCTYPE html><html><body><h1>Welcome to client</h1><h3>Select a grant flow</h3><p>%s</p><p>%s</p><p>%s</p><p>%s</p></body></html>' % (
                        authorization_code, implicit_grant, res_pass, client_id_client_secret)
                    self.ok(body)
            elif parsed.path == '/redirect':
                code = query.get('code')
                assert code is not None, 'Auth code not found'
                session_id = generateCode()
                SESSIONS.setdefault(session_id, {'oauth2': Credentials.fromAuthCode(code)})
                self.redirect('http://%s:%d/user' % (HOST, CLIENT_PORT), headers={
                    "Set-Cookie": 'SESSIONID=%s; httponly' % (session_id)
                }.items())
            elif parsed.path == '/redirect_implicit_grant':
                body = '<!DOCTYPE html><html><body><h1>Welcome to client (User page)</h1><p>Server receive no access token as the token is passed by fragment from auth server. Refresh token is therefore not allowed.</p><script>%s</script></body></html>' % (
                    'document.body.appendChild(document.createTextNode("Access response server by this access token: "+location.hash.split(/=/)[1])); location.hash="";'
                )
                self.ok(body)
            elif parsed.path == '/ropc_login':
                body = '<!DOCTYPE html><html><body><h1>Welcome to client (Login page)</h1><form method=post>Login: <input name=username value=a /><input name=pw type=password value=a /><input type=submit /></form></body></html>'
                self.ok(body)
            elif parsed.path == '/cc_login':
                secret = client_login()
                self.redirect('http://%s:%d/user_cc' % (HOST, CLIENT_PORT))
            elif parsed.path == '/user':
                assert search_session and SESSIONS.get(search_session.group(1)), 'Session not found'
                oauth2 = SESSIONS.get(search_session.group(1)).get('oauth2')
                token = oauth2.access_token
                user = get_user_info(token)
                images = json.loads(get_user_images(token)) or []
                body = '<h1>Hello %s</h1><p><h3>You have these images</h3>%s</p>' % (
                    user, '\r\n'.join(['<div>%s</div>' % image for image in images]))
                self.ok(body)
            elif parsed.path == '/user_cc':
                body = '<h1>Welcome to client (Client ID Client Secret page)</h1><p>Display content stored by client</p>'
                self.ok(body)
        except HTTPError as e:
            print(e.fp.read())
            self.error(e)
        except BaseException as e:
            self.error(e)


def run():
    local_server.serve(CLIENT_PORT, ClientHandler)
