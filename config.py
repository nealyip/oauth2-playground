import os

HOST =  os.getenv('HOST_IP', '127.0.0.1')
CLIENT_PORT = int(os.getenv('CLIENT_PORT', 8080))
AUTH_SERVER_PORT = int(os.getenv('AUTH_SERVER_PORT', 8010))
RESOURCE_SERVER_PORT =  int(os.getenv('RESOURCE_SERVER_PORT', 8000))
ACCESS_TOKEN_LIFETIME = int(os.getenv('ACCESS_TOKEN_LIFETIME', 3600))