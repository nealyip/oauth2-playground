## OAuth2 playground ##
A simple implementation of oauth2 using python, as a playground, it doesn't do too much checking.  

### Requirements ###
Python 3.4

### Dependencies ###
None

### Start ###
```
python index.py
```
If chrome doesn't open, please browse http://127.0.0.1:8080 by yourself  
Three servers will be opened once running the above command including   
authorization server, client and resource server.  

If there is any problem opening because of using port, you may change the port from config.py  

### From Docker ###
```docker
docker run --rm -p 8010:8010 -p 8080:8080 nealyip/oauth2-playground
```