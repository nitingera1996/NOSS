from django.shortcuts import render
import requests
import json
from bs4 import BeautifulSoup
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from apis.models import *
import string
import random

def generate_key():
    s = string.letters + string.digits
    return ''.join(random.sample(s, 50))

def openvpn_password(request):
    try:
        response_dict={}
        r  = requests.get("http://www.vpnbook.com/freevpn")
        data = r.text
        soup = BeautifulSoup(data,'html.parser')
        tags=soup.find_all('li')
        for t in tags:
            l=str(t.get_text())
            if l.startswith("Password"):
                now_password=l.split(" ",1)[-1]
                response_dict['password']=now_password
    except requests.exceptions.RequestException as e:
        print e
    return HttpResponse(json.dumps(response_dict), content_type='application/javascript') 

@login_required(login_url='/account/login')
def profile(request):
    context = {}
    ud = UserDetails.objects.filter(user=request.user)
    if not ud:
        ud = UserDetails.objects.create(user=request.user, key=generate_key())
    context['ud'] = ud[0]
    print ud
    return render(request, "profile.html", context)