import hashlib
import json
import random
import urllib.parse as parse

import library.local_server as local_server
from library import datetime_helper
from . import AUTH_SERVER_PORT, ACCESS_TOKEN_LIFETIME

authorization_codes = {

}

clients = {
    'client1': 'client1secret'
}

access_tokens = {

}


def generate_token(grant_type, code, **kwargs):
    access_token = generate_code()
    token = {}
    if grant_type == 'authorization_code':
        authcode = authorization_codes.get(code)
        username, scopes = [authcode.get(key) for key in ('username', 'scopes')]
        assert username is not None, 'Auth code incorrect'
        del authorization_codes[code]  # use once only
        token = {
            'refresh_token': generate_code(),
            'start_time': datetime_helper.utcnow(),
            'expires_in': ACCESS_TOKEN_LIFETIME,
            'scopes': scopes.decode('utf-8'),
            'username': username
        }
    elif grant_type == 'refresh_token':
        found = {ac for ac in access_tokens if access_tokens[ac].get('refresh_token') == code}
        assert len(found) > 0, 'Refresh token not found'
        token = access_tokens.get(list(found)[0]).copy()
        token.update({
            'start_time': datetime_helper.utcnow()
        })
    elif grant_type == 'implicit_grant':
        token.update({
            'expires_in': ACCESS_TOKEN_LIFETIME,
            'scopes': kwargs.get('scopes').decode('utf-8')
        })
    else:
        raise Exception('Wrong grant type')

    token['access_token'] = access_token
    access_tokens.setdefault(access_token, {})
    access_tokens[access_token] = token
    return token


def generate_code():
    m = hashlib.sha256()
    m.update(bytes(str(random.random()), encoding='ascii'))
    return m.hexdigest()


class AuthServerHandler(local_server.Handler):
    def do_POST(self):

        parsed = parse.urlparse(self.path)
        query = dict(parse.parse_qsl(parsed.query))

        if parsed.path == '/login':
            global authorization_codes
            content_length = int(self.headers['Content-Length'])
            q = dict(parse.parse_qsl(self.rfile.read(content_length)))
            assert q.get(b'username', b'') != b'', 'Missing username'
            assert q.get(b'pw', b'') != b'', 'Missing password'
            username = q.get(b'username').decode('utf-8')

            response_type = query.get('response_type')

            if response_type == 'code':
                # Authorization grant flow
                authcode = generate_code()
                authorization_codes.setdefault(authcode, '')
                authorization_codes[authcode] = {
                    'username': username,
                    'scopes': q.get(b'scopes')
                }

                self.redirect('%s?%s' % (query.get('redirect_url', ''), parse.urlencode({
                    'code': authcode
                })))
            elif response_type == 'token':
                # Implicit grant flow
                token = generate_token('implicit_grant', '', scopes=q.get(b'scopes'))

                self.redirect('%s#access_token=%s' % (query.get('redirect_url', ''), token['access_token']))
        elif parsed.path == '/token':
            content_length = int(self.headers['Content-Length'])
            q = dict(parse.parse_qsl(self.rfile.read(content_length)))
            assert clients.get(q.get(b'client_id', b'').decode()) == q.get(b'client_secret',
                                                                           b'').decode(), 'Wrong Secret'

            grant_type = q.get(b'grant_type').decode('ascii')
            token = generate_token(grant_type, (q.get(b'code') if grant_type == 'authorization_code' else q.get(
                b'refresh_token')).decode('utf-8'))
            body = json.dumps({
                key: token.get(key) for key in token if
                key in {'access_token', 'refresh_token', 'start_time', 'expires_in'}
            })

            self.ok(body)

    def do_GET(self):
        try:
            parsed = parse.urlparse(self.path)
            query = dict(parse.parse_qsl(parsed.query))
            if parsed.path == '/login':
                body = '<!DOCTYPE html><html><body><h1>Welcome to authorization server</h1><p>%s wants to using your credentials for %s </p><p><form method=post>Login: <input name=username value=a /><input name=pw type=password value=a /><input type=hidden name="scopes" value="%s" /><input type=submit /></form></p></body></html>' % (
                    query.get('client_id'),
                    query.get('scopes'),
                    parse.quote(query.get('scopes'))
                )

                self.ok(body)
            elif parsed.path == '/user':
                token = access_tokens.get(self.headers.get('Authorization')[7:])
                assert token.get('scopes'), 'Token not found'
                start_time = token.get('start_time')
                assert not datetime_helper.is_expired(start_time, token.get('expires_in')), 'Expired'
                body = json.dumps({
                    'scopes': token.get('scopes'),
                    'not_after': datetime_helper.expiry(start_time, token.get('expires_in')).isoformat(),
                    'username': token.get('username')
                })
                self.ok(body)
        except AssertionError as e:
            if e.args[0] == 'Expired':
                self.error(e, code=403)
            else:
                self.error(e)
        except BaseException as e:
            self.error(e)


def run():
    local_server.serve(AUTH_SERVER_PORT, AuthServerHandler)
