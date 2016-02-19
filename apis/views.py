from django.shortcuts import render
import requests
import json
from bs4 import BeautifulSoup
from django.http import HttpResponse
from django.contrib.auth.models import User
from apis.models import *

def openvpn_password(request):
    response_dict={}
    r  = requests.get("http://www.vpnbook.com/freevpn")
    data = r.text
    soup = BeautifulSoup(data, "html.parser")
    tags=soup.find_all('li')
    for t in tags:
        l=str(t.get_text())
        if l.startswith("Password"):
            now_password=l.split(" ",1)[-1]
            response_dict['password']=now_password
    return HttpResponse(json.dumps(response_dict), content_type='application/javascript') 

