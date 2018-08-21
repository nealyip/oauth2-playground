import datetime


def strfrtime(t: str):
    return datetime.datetime.strptime(t[:-3] + t[-2:], r'%Y-%m-%dT%H:%M:%S.%f%z')


def expiry(t: str, seconds: int):
    start_time = strfrtime(t)
    return start_time + datetime.timedelta(seconds=seconds)


def is_expired(t: str, seconds: int):
    exp = expiry(t, seconds)
    return datetime.datetime.now(tz=datetime.timezone.utc) > exp


def utcnow():
    return datetime.datetime.now(tz=datetime.timezone.utc).isoformat(timespec='milliseconds')
