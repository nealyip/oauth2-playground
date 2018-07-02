from library.datetime_helper import is_expired
import urllib.request as request
import urllib.parse as parse
import json
from . import AUTH_SERVER_PORT, HOST, CLIENT_ID, CLIENT_SECRET

SESSIONS = {

}


def get_access_token(authcode=None, refresh_token=None):
    assert authcode is not None or refresh_token is not None, 'Require either auth or refresh token'
    url = request.Request('http://%s:%s/token' % (HOST, AUTH_SERVER_PORT), method='POST', headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    })

    params = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    params.update(
        {
            'code': authcode,
            'grant_type': 'authorization_code'
        } if authcode is not None else {
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        })

    req = request.urlopen(url, data=parse.urlencode(params).encode('ascii'))
    return json.loads(req.read().decode('ascii'))


class Credentials:
    def __init__(self, creds):
        self.creds = creds

    def __getattr__(self, item):
        if item == 'access_token':
            if self.expired:
                self.refresh()
        return self.creds.get('access_token', None)

    @property
    def expired(self):
        return is_expired(self.creds['start_time'], self.creds['expires_in'])

    def refresh(self):
        new_token = get_access_token(refresh_token=self.creds['refresh_token'])
        self.creds = new_token

    @staticmethod
    def fromAuthCode(authcode):
        return Credentials(get_access_token(authcode))
