import authorization_server
import resource_server
import client
import threading
import os
import webbrowser
from config import HOST, CLIENT_PORT


# import _thread

class AuthServer(threading.Thread):
    def run(self):
        authorization_server.run()


class ResServer(threading.Thread):
    def run(self):
        resource_server.run()


class ClientServer(threading.Thread):
    def run(self):
        client.run()


def create_servers():
    # try:
    #     _thread.start_new_thread(authorization_server.run, ())
    #     _thread.start_new_thread(resource_server.run, ())
    # except BaseException as be:
    #     print(be)
    # while 1:
    #     pass
    auth_thread = AuthServer()
    res_thread = ResServer()
    client_thread = ClientServer()

    auth_thread.start()
    res_thread.start()
    client_thread.start()

    return (client_thread, auth_thread, res_thread)


if __name__ == '__main__':
    servers = create_servers()

    # visit localhost:8080
    chromepath = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'
    url = "http://%s:%d" % (HOST, CLIENT_PORT)
    if os.path.isfile(chromepath):
        webbrowser.get("{!s} %s".format(chromepath)).open(url)
    else:
        print('Please goto %s with your favorite browser.' % url)
    [server.join() for server in servers]
