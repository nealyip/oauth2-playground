import json
import urllib.parse as parse
import urllib.request as request
from urllib.error import HTTPError

import library.local_server as local_server
from library import datetime_helper
from . import AUTH_SERVER_PORT, HOST

USERS = {
    'a': {
        'name': 'Tom',
        'images': [
            'https://google.com/abc.jpg',
            'https://google.com/def.jpg'
        ]
    }
}


def get_permission(token):
    user = request.urlopen('http://%s:%d/user?token=%s' % (HOST, AUTH_SERVER_PORT, token))
    body = user.read()

    return json.loads(body.decode('utf-8'))


class Handler(local_server.Handler):
    def do_GET(self):
        try:
            parsed = parse.urlparse(self.path)
            query = dict(parse.parse_qsl(parsed.query))

            assert query.get('token') is not None, 'Missing token'
            permission = get_permission(query.get('token'))
            assert not datetime_helper.is_expired(permission.get('not_after'), 0), 'Expired'

            user = USERS.get(permission.get('username'))
            assert user is not None, 'User not found'
            scopes = parse.unquote(permission.get('scopes')).split(',')

            if parsed.path == '/info':
                assert 'read_profile' in scopes, 'No permission'
                self.ok(user.get('name'))
            elif parsed.path == '/images':
                assert 'read_image' in scopes, 'No permission'
                self.ok(json.dumps(user.get('images')))
        except HTTPError as e:
            self.error(e, code=e.code)
        except BaseException as be:
            self.error(be)


def run():
    local_server.serve(8000, Handler)