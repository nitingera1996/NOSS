from django.shortcuts import render
import requests
import json
from bs4 import BeautifulSoup
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from apis.models import *
import string
import random
import datetime
import ast
from ratelimit.decorators import ratelimit
import math
import os
import hashlib
import hmac
import base64


if 'ON_HEROKU' in os.environ:
    pass
else:
    from django.core.cache import cache
    import requests_cache
    requests_cache.install_cache()

google_geocoding_api_key="AIzaSyAVPebYRc6oQkB9gT0f-z63IStnR02bQ34"
amadeus_api_key="oJS13442zS4sbBnZVeGa6Y6Y38BzmPyC"
railway_api_key="jruwt3809"
google_matrix_api_key="AIzaSyBqLD2_EXtqKWi8WPWEKiELVNrINuTa91s"
CACHE_TIMEOUT=60
rate = '100/h'

def generate_key():
    s = string.letters + string.digits
    return ''.join(random.sample(s, 50))

def provide_hash(message,key):
    message = bytes(message).encode('utf-8')
    secret = bytes(key).encode('utf-8')

    signature = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).digest())
    return signature

@ratelimit(key='ip', rate=rate, block=True)
def openvpn_password(request):
    # a=request.GET.get('q', '')
    # print a
    response_dict={}
    # k#ey="http://www.vpnbook.com/freevpn"
    #value = cache.get(key)
    # if value is None:
    try:
        r  = requests.get("http://www.vpnbook.com/freevpn")
        data = r.text
        soup = BeautifulSoup(data,'html.parser')
        tags=soup.find_all('li')
        for t in tags:
            l=str(t.get_text())
            if l.startswith("Password"):
                now_password=l.split(" ",1)[-1]
                response_dict['password']=now_password
                response_dict['status']="True"
    except requests.exceptions.RequestException as e:
        # print e
        response_dict['status']="False"
        response_dict['message']="Check ur internet connection"
        # value = now_password 
        # cache.set(key, value, CACHE_TIMEOUT)
    # else:
    #     response_dict['password']=value
    #     response_dict['status']="True"
    return HttpResponse(json.dumps(response_dict), content_type='application/javascript')

@login_required(login_url='/account/login')
def profile(request):
    context = {}
    try:
        ud = UserDetails.objects.get(user=request.user)
    except Exception as e:
        ud = UserDetails.objects.create(user=request.user, private_key=generate_key(),public_key=generate_key())
    context['ud'] = ud
    return render(request, "profile.html", context)

@ratelimit(key='ip', rate=rate, block=True)
def rail_route(request):
    public_key=request.GET.get('public_key', '') #example request=http://localhost:8000/railroute/?departure_date=2016-04-03&origin=IIT%20Varanasi&duration=3&public_key=djWMgJqbAumanTIi034sO26lG19KfYDkxUwZLEc7otzpXHB8Fy&parsed_string=NKosistZBEUvJYFpHVO9836FtRna2SxYQ0AkjawS8/A=
    # print "public_key",public_key
    if public_key=='':
        return HttpResponse(json.dumps({'status':"False",'error':"Authentication failed, public_key not provided"}),content_type='application/javascript')
    else:
        found=False
        frm=request.GET.get('origin', '')
        if frm=='':
            return HttpResponse(json.dumps({'status':"False",'error':"origin not specfied"}),content_type='application/javascript')
        parsed_string=request.GET.get('parsed_string','')
        if parsed_string=='':
            return HttpResponse(json.dumps({'status':"False",'error':"parsed_string not provided"}),content_type='application/javascript')
        for user in UserDetails.objects.all():
            if user.public_key==public_key:
                u_private_key=user.private_key
                expected_parsed_string=provide_hash(frm,u_private_key)
                if expected_parsed_string!=parsed_string:
                    return HttpResponse(json.dumps({'status':"False",'error':"wrong parsed_string given"}),content_type='application/javascript')
                found=True
                break
        if found==False:
            return HttpResponse(json.dumps({'status':"False",'error':"Authentication failed, public_key not found"}),content_type='application/javascript')
    response_dict={}
    to=request.GET.get('destination', '')
    if to=='':
        return HttpResponse(json.dumps({'status':"False",'error':"plz specify the destination"}),content_type='application/javascript')
    date=request.GET.get('departure_date', '')
    if frm==to:
        return HttpResponse(json.dumps({'status':"False",'error':"no railroute possible"}),content_type='application/javascript')
    if valid_date(date)==False:
        if date!="":
            return HttpResponse(json.dumps({'status':"False",'error':"plz enter date in yyyy-mm-dd format"}),content_type='application/javascript')
        else:
            return HttpResponse(json.dumps({'status':"False",'error':"plz specify the destination_date"}),content_type='application/javascript')
    date=date[8:10]+'-'+date[5:7]+'-'+date[:4]
    print frm,to,date
    try:                        #From here, we find out the name of the origin city from the address to be given input to railway API
        payload={'address':frm,'key':google_geocoding_api_key}
        frm_loc_ob = requests.get('https://maps.googleapis.com/maps/api/geocode/json',params=payload)
        if frm_loc_ob.status_code == requests.codes.ok:
            frm_loc_json=frm_loc_ob.json()
            add=frm_loc_json['results'][0]["address_components"]
            flag=1
            for element in add:
                if element['types'][0]=="locality":
                    source_city=element["long_name"]
                    flag=0
            if flag:
                source_city=frm
    except requests.exceptions.RequestException as e:
        print e
    try:
        frm_loc_ob = requests.get("http://api.railwayapi.com/name_to_code/station/"+source_city+"/apikey/"+railway_api_key+'/')
        if frm_loc_ob.status_code == requests.codes.ok:
            frm_loc_json=frm_loc_ob.json()
            # print frm_loc_json
            if frm_loc_json['response_code']==200:
                stations=frm_loc_json['stations']
                max=0
                for station in stations:
                    ans=sum(a==b for a, b in zip(station['fullname'],source_city))
                    if ans>=max:
                        max=ans
                        source_code=station['code']    
    except requests.exceptions.RequestException as e:
        print e

    print "first part done"
    try:
 #From here, we find out the name of the destination city from the address to be given input to railway API
        payload={'address':to,'key':google_geocoding_api_key}
        to_loc_ob = requests.get('https://maps.googleapis.com/maps/api/geocode/json',params=payload)
        if to_loc_ob.status_code == requests.codes.ok:
            to_loc_json=to_loc_ob.json()
            add=to_loc_json['results'][0]["address_components"]
            flag=1
            for element in add:
                if element['types'][0]=="locality":
                    dest_city=element["long_name"]
                    flag=0
            if flag:
                dest_city=to
    except requests.exceptions.RequestException as e:
        print e

    try:
        frm_loc_ob = requests.get("http://api.railwayapi.com/name_to_code/station/"+dest_city+"/apikey/"+railway_api_key+'/')
        if frm_loc_ob.status_code == requests.codes.ok:
            frm_loc_json=frm_loc_ob.json()
            # print frm_loc_json
            if frm_loc_json['response_code']==200:
                stations=frm_loc_json['stations']
                max=0
                for station in stations:
                    ans=sum(a==b for a, b in zip(station['fullname'],dest_city))
                    if ans>=max:
                        max=ans
                        dest_code=station['code']    
    except requests.exceptions.RequestException as e:
        print e

    travel_class=request.GET.get('travel_class', '')
    if travel_class=='':
        travel_class="3A"
    if travel_class!='3A' and travel_class!='2A' and travel_class!='1A' and travel_class!='SS':
        return HttpResponse(json.dumps({'status':"False",'error':"Please choose a proper railway class."}),content_type='application/javascript')    
    response_dict['from']=source_city
    response_dict['to']=dest_city
    print source_code,dest_code
    try:                                #Here we find available trains between stations
        payload={'from_station':source_code,'to_station':dest_code,'class':travel_class,'date':date,'adults':1,'children':0,'male_seniors':0,'female_seniors':0}
        path_html = requests.get('http://www.cleartrip.com/trains/results',params=payload)
        path_html =path_html.text
        soup = BeautifulSoup(path_html,'html.parser')
        try:
            train_data = soup.find_all("script", type="text/javascript",src=False)[2].get_text()[19:]
        except IndexError as e:
            response_dict["result"]="No direct train was found"
            return HttpResponse(json.dumps(response_dict),content_type='application/javascript') 
        end_pos=train_data.find(',"trips":')
        train_data = train_data[:(end_pos)]+'}'
        train_data=str(train_data)
        train_data=train_data.replace("true","True")
        train_data=train_data.replace("false","False")
        print train_data
        end_pos =train_data.find(',"3":{"distance')
        if end_pos>0:
            train_data=train_data[:end_pos]+'}}'
        print
        print end_pos
        print train_data
        train_data=ast.literal_eval(train_data)
        response_dict['train_data']=train_data       
        frm_stn_name=train_data["trains"]["1"]["from"]+" Station"
        to_stn_name=train_data["trains"]["1"]["to"]+" Station"
        my_dict={}
        try:
            payload={'origins':frm,'destinations':frm_stn_name,'key':google_matrix_api_key}
            my_loc_to_stn=requests.get('https://maps.googleapis.com/maps/api/distancematrix/json',params=payload)
            if my_loc_to_stn.status_code == requests.codes.ok:
                my_loc_to_stn=my_loc_to_stn.json()
                my_dict['dist1']=my_loc_to_stn['rows'][0]['elements'][0]['distance']['text']
                my_dict['time1']=my_loc_to_stn['rows'][0]['elements'][0]['duration']['text']
        except requests.exceptions.RequestException as e:
            print e       
        try:
            payload={'origins':to_stn_name,'destinations':to,'key':google_matrix_api_key}
            my_loc_to_stn=requests.get('https://maps.googleapis.com/maps/api/distancematrix/json',params=payload)
            if my_loc_to_stn.status_code == requests.codes.ok:
                my_loc_to_stn=my_loc_to_stn.json()
                my_dict['dist2']=my_loc_to_stn['rows'][0]['elements'][0]['distance']['text']
                my_dict['time2']=my_loc_to_stn['rows'][0]['elements'][0]['duration']['text']
        except requests.exceptions.RequestException as e:
            print e
        response_dict['step1']="Travel from "+ frm +" to " + frm_stn_name +" which is "+ my_dict['dist1']+" away and takes "+my_dict['time1']
        response_dict['step2']="Board the suitable train form the list"
        response_dict['step3']="Travel from "+ to_stn_name +" to " + to + " which is "+ my_dict['dist2']+" away and takes "+my_dict['time2']
        response_dict['status']=True
    except requests.exceptions.RequestException as e:
        print e
    return HttpResponse(json.dumps(response_dict),content_type='application/javascript')
            


def rail_route_to_airport(frm,to,date,travel_class):            ##this function gives rail route to or from airport if airport is far away                  
    response_dict={} 
    date=date[8:10]+'-'+date[5:7]+'-'+date[:4]
    print frm,to,date
    try:
        payload={'address':frm,'key':google_geocoding_api_key}
        frm_loc_ob = requests.get('https://maps.googleapis.com/maps/api/geocode/json',params=payload)
        if frm_loc_ob.status_code == requests.codes.ok:
            frm_loc_json=frm_loc_ob.json()
            add=frm_loc_json['results'][0]["address_components"]
            flag=1
            for element in add:
                if element['types'][0]=="locality":
                    source_city=element["long_name"]
                    flag=0
            if flag:
                source_city=frm
    except requests.exceptions.RequestException as e:
        print e
    try:
        frm_loc_ob = requests.get("http://api.railwayapi.com/name_to_code/station/"+source_city+"/apikey/"+railway_api_key+'/')
        if frm_loc_ob.status_code == requests.codes.ok:
            frm_loc_json=frm_loc_ob.json()
            # print frm_loc_json
            if frm_loc_json['response_code']==200:
                stations=frm_loc_json['stations']
                max=0
                for station in stations:
                    ans=sum(a==b for a, b in zip(station['fullname'],source_city))
                    if ans>=max:
                        max=ans
                        source_code=station['code']    
    except requests.exceptions.RequestException as e:
        print e
    print "first part done"
    try:
        payload={'address':to,'key':google_geocoding_api_key}
        to_loc_ob = requests.get('https://maps.googleapis.com/maps/api/geocode/json',params=payload)
        if to_loc_ob.status_code == requests.codes.ok:
            to_loc_json=to_loc_ob.json()
            add=to_loc_json['results'][0]["address_components"]
            flag=1
            for element in add:
                if element['types'][0]=="locality":
                    dest_city=element["long_name"]
                    flag=0
            if flag:
                dest_city=to
    except requests.exceptions.RequestException as e:
        print e

    try:
        frm_loc_ob = requests.get("http://api.railwayapi.com/name_to_code/station/"+dest_city+"/apikey/"+railway_api_key+'/')
        if frm_loc_ob.status_code == requests.codes.ok:
            frm_loc_json=frm_loc_ob.json()
            # print frm_loc_json
            if frm_loc_json['response_code']==200:
                stations=frm_loc_json['stations']
                max=0
                for station in stations:
                    ans=sum(a==b for a, b in zip(station['fullname'],dest_city))
                    if ans>=max:
                        max=ans
                        dest_code=station['code']    
    except requests.exceptions.RequestException as e:
        print e

    print "second part done"
    if travel_class=="":
        travel_class="3A"
    response_dict['from']=source_city
    response_dict['to']=dest_city
    try:
        payload={'from_station':source_code,'to_station':dest_code,'class':travel_class,'date':date,'adults':1,'children':0,'male_seniors':0,'female_seniors':0}
        path_html = requests.get('http://www.cleartrip.com/trains/results',params=payload)
        path_html =path_html.text
        soup = BeautifulSoup(path_html,'html.parser')
        try:
            train_data = soup.find_all("script", type="text/javascript",src=False)[2].get_text()[19:]
        except IndexError as e:
            response_dict["result"]="No direct train was found"
            response_dict['not_found']=1
            return response_dict
        end_pos=train_data.find(',"trips":')
        train_data = train_data[:(end_pos)]+'}'
        train_data=str(train_data)
        train_data=train_data.replace("true","True")
        train_data=train_data.replace("false","False")
        end_pos =train_data.find(',"3":{"distance')
        if end_pos>0:
            train_data=train_data[:end_pos]+'}}'
        train_data=ast.literal_eval(train_data)
        response_dict['train_data']=train_data       
        frm_stn_name=train_data["trains"]["1"]["from"]+" Station"
        to_stn_name=train_data["trains"]["1"]["to"]+" Station"
        my_dict={}
        try:
            payload={'origins':frm,'destinations':frm_stn_name,'key':google_matrix_api_key}
            my_loc_to_stn=requests.get('https://maps.googleapis.com/maps/api/distancematrix/json',params=payload)
            if my_loc_to_stn.status_code == requests.codes.ok:
                my_loc_to_stn=my_loc_to_stn.json()
                my_dict['dist1']=my_loc_to_stn['rows'][0]['elements'][0]['distance']['text']
                my_dict['time1']=my_loc_to_stn['rows'][0]['elements'][0]['duration']['text']
        except requests.exceptions.RequestException as e:
            print e       
        try:
            payload={'origins':to_stn_name,'destinations':to,'key':google_matrix_api_key}
            my_loc_to_stn=requests.get('https://maps.googleapis.com/maps/api/distancematrix/json',params=payload)
            if my_loc_to_stn.status_code == requests.codes.ok:
                my_loc_to_stn=my_loc_to_stn.json()
                my_dict['dist2']=my_loc_to_stn['rows'][0]['elements'][0]['distance']['text']
                my_dict['time2']=my_loc_to_stn['rows'][0]['elements'][0]['duration']['text']
        except requests.exceptions.RequestException as e:
            print e
        response_dict['step1']="Travel from "+ frm +" to " + frm_stn_name +" which is "+ my_dict['dist1']+" away and takes "+my_dict['time1']
        response_dict['step2']="Board the suitable train form the list"
        response_dict['step3']="Travel from "+ to_stn_name +" to " + to + " which is "+ my_dict['dist2']+" away and takes "+my_dict['time2']
        response_dict['my_dict']=my_dict
        response_dict['not_found']=0
    except requests.exceptions.RequestException as e:
        print e
    return response_dict


@ratelimit(key='ip', rate=rate, block=True)
def air_route(request):
    public_key=request.GET.get('public_key', '') #example request=http://localhost:8000/airroute/?destination=Krishna%20Nagar,%20Mathura&departure_date=2016-04-03&travel_class=ECONOMY&origin=IIT%20Varanasi&public_key=djWMgJqbAumanTIi034sO26lG19KfYDkxUwZLEc7otzpXHB8Fy&parsed_string=NKosistZBEUvJYFpHVO9836FtRna2SxYQ0AkjawS8/A=
    # print "public_key",public_key
    if public_key=='':
        return HttpResponse(json.dumps({'status':"False",'error':"Authentication failed, public_key not provided"}),content_type='application/javascript')
    else:
        found=False
        frm=request.GET.get('origin', '')
        if frm=='':
            return HttpResponse(json.dumps({'status':"False",'error':"origin not specfied"}),content_type='application/javascript')
        parsed_string=request.GET.get('parsed_string','')
        if parsed_string=='':
            return HttpResponse(json.dumps({'status':"False",'error':"parsed_string not provided"}),content_type='application/javascript')
        for user in UserDetails.objects.all():
            if user.public_key==public_key:
                u_private_key=user.private_key
                expected_parsed_string=provide_hash(frm,u_private_key)
                if expected_parsed_string!=parsed_string:
                    return HttpResponse(json.dumps({'status':"False",'error':"wrong parsed_string given"}),content_type='application/javascript')
                found=True
                break
        if found==False:
            return HttpResponse(json.dumps({'status':"False",'error':"Authentication failed, public_key not found"}),content_type='application/javascript')
    flag1,flag2=[0,0]
    response_dict={} 
    to=request.GET.get('destination', '')
    if to=="":
        return HttpResponse(json.dumps({'status':"False",'error':"plz specify the destination"}),content_type='application/javascript')
    date=request.GET.get('departure_date', '')
    if frm==to:
        return HttpResponse(json.dumps({'status':"False",'error':"no airroute possible"}),content_type='application/javascript')
    if valid_date(date)==False:
        if date!="":
            return HttpResponse(json.dumps({'status':"False",'error':"plz enter date in yyyy-mm-dd format"}),content_type='application/javascript')
        else:
            return HttpResponse(json.dumps({'status':"False",'error':"plz specify the destination_date"}),content_type='application/javascript')

    travel_class=request.GET.get('travel_class', '')
    if travel_class=="":
        travel_class="ECONOMY"
    if travel_class!="ECONOMY" and travel_class!="BUSINESS" and travel_class!="FIRST" and travel_class!="PREMIUM_ECONOMY":
        return HttpResponse(json.dumps({'status':"False",'error':"Please select proper class"}),content_type='application/javascript')    
    print frm,to,date,travel_class
    try:
        payload={'address':frm,'key':google_geocoding_api_key}
        frm_loc_ob = requests.get('https://maps.googleapis.com/maps/api/geocode/json',params=payload)
        if frm_loc_ob.status_code == requests.codes.ok:
            # print "OK"
            frm_loc_json=frm_loc_ob.json()
            # pp.pprint(frm_loc_json['results'][0]["geometry"]["location"])
            location=frm_loc_json['results'][0]["geometry"]["location"]
            frm_lat=location["lat"]
            frm_lng=location["lng"]
            try:
                payload={"apikey":amadeus_api_key,'latitude':frm_lat,'longitude':frm_lng}
                near_airport_loc_ob_1=requests.get('https://api.sandbox.amadeus.com/v1.2/airports/nearest-relevant',params=payload)
                if near_airport_loc_ob_1.status_code == requests.codes.ok :
                    near_airport_loc_json_1=near_airport_loc_ob_1.json()
                    dic_from=near_airport_loc_json_1[0]
            except requests.exceptions.RequestException as e:
                print e
    except requests.exceptions.RequestException as e:
        print e
    try:
        payload={'address':to,'key':google_geocoding_api_key}
        to_loc_ob = requests.get('https://maps.googleapis.com/maps/api/geocode/json',params=payload)
        if to_loc_ob.status_code == requests.codes.ok:
            # print "OK"
            to_loc_json=to_loc_ob.json()
            # pp.pprint(frm_loc_json['results'][0]["geometry"]["location"])
            location=to_loc_json['results'][0]["geometry"]["location"]
            to_lat=location["lat"]
            to_lng=location["lng"]
            try:
                payload={"apikey":amadeus_api_key,'latitude':to_lat,'longitude':to_lng}
                near_airport_loc_ob_2=requests.get('https://api.sandbox.amadeus.com/v1.2/airports/nearest-relevant',params=payload)
                # print near_airport_loc_ob
                if near_airport_loc_ob_2.status_code == requests.codes.ok:
                    near_airport_loc_json_2=near_airport_loc_ob_2.json()
                    dic_to=near_airport_loc_json_2[0]
            except requests.exceptions.RequestException as e:
                print e

    except requests.exceptions.RequestException as e:
        print e

    if dic_from['airport']==dic_to['airport']:
        return HttpResponse(json.dumps({'status':"False",'error':"no airroute possible"}),content_type='application/javascript')
    if dic_from["distance"]>50:
        print "have to travel by train to airport"
        flag1=1
        response_dict1=rail_route_to_airport(frm,dic_from["airport_name"],date,"")
        # print response_dict1

    if dic_to["distance"]>50:
        print "have to travel by train from airport"
        flag2=1
        print dic_to["airport_name"],to,date
        response_dict2=rail_route_to_airport(dic_to["airport_name"],to,date,"")
        # print response_dict2
    

    try:
        payload={                                         
            'origin':dic_from['airport'],
            'destination':dic_to["airport"],
            'departure_date':date,
            'apikey':amadeus_api_key,
            'currency':"INR",
            'number_of_results':"1",
            "travel_class": travel_class}
        # print payload
        flights_return_ob = requests.get('https://api.sandbox.amadeus.com/v1.2/flights/low-fare-search',params=payload)
        # print flights_return_ob.status_code
        if flights_return_ob.status_code == requests.codes.ok:
            flights_return_json=flights_return_ob.json()
            flights_array=flights_return_json["results"]
            response_dict['status']="True"
            if flag1:
                if response_dict1['not_found']:
                    response_dict['step1']="From "+frm+" to "+dic_from['airport_name']+" travelling distance "+str(dic_from["distance"])+" km"    
                else:    
                    response_dict['step1.1']=response_dict1['step1']
                    response_dict['step1.2']=response_dict1['step2']
                    response_dict['step1.3']=response_dict1['step3']
                    response_dict['train_to_airport_data']=response_dict1['train_data']
            else:
                response_dict['step1']="From "+frm+" to "+dic_from['airport_name']+" travelling distance "+str(dic_from["distance"])+" km"
            response_dict['step2']="From "+dic_from['airport_name']+" to "+dic_to['airport_name']
            response_dict['flights']=flights_array
            if flag2:
                if response_dict2['not_found']:
                    response_dict['step3']="From "+dic_to['airport_name']+" to "+to+" travelling distance "+str(dic_to["distance"])+" km"
                else:
                    response_dict['step3.1']=response_dict2['step1']
                    response_dict['step3.2']=response_dict2['step2']
                    response_dict['step3.3']=response_dict2['step3']
                    response_dict['train_from_airport_data']=response_dict2['train_data']
            else:
                response_dict['step3']="From "+dic_to['airport_name']+" to "+to+" travelling distance "+str(dic_to["distance"])+" km"
        else:
            return HttpResponse(json.dumps({'status':"False",'error':"departure_date should be after today's day"}),content_type='application/javascript')
    except requests.exceptions.RequestException as e:
        print e
    return HttpResponse(json.dumps(response_dict),content_type='application/javascript')           


def air_route_to_tour(frm,to,date,travel_class):
    flag1,flag2=[0,0]
    response_dict={} #example request=http://localhost:8000/airroute/?destination=Krishna%20Nagar,%20Mathura&departure_date=2016-04-03&travel_class=ECONOMY&origin=IIT%20Varanasi
    if travel_class=="":
        travel_class="ECONOMY"
    print frm,to,date,travel_class
    try:
        payload={'address':frm,'key':google_geocoding_api_key}
        frm_loc_ob = requests.get('https://maps.googleapis.com/maps/api/geocode/json',params=payload)
        if frm_loc_ob.status_code == requests.codes.ok:
            # print "OK"
            frm_loc_json=frm_loc_ob.json()
            # pp.pprint(frm_loc_json['results'][0]["geometry"]["location"])
            location=frm_loc_json['results'][0]["geometry"]["location"]
            frm_lat=location["lat"]
            frm_lng=location["lng"]
            try:
                payload={"apikey":amadeus_api_key,'latitude':frm_lat,'longitude':frm_lng}
                near_airport_loc_ob_1=requests.get('https://api.sandbox.amadeus.com/v1.2/airports/nearest-relevant',params=payload)
                if near_airport_loc_ob_1.status_code == requests.codes.ok :
                    near_airport_loc_json_1=near_airport_loc_ob_1.json()
                    dic_from=near_airport_loc_json_1[0]
            except requests.exceptions.RequestException as e:
                print e
    except requests.exceptions.RequestException as e:
        print e
    try:
        payload={'address':to,'key':google_geocoding_api_key}
        to_loc_ob = requests.get('https://maps.googleapis.com/maps/api/geocode/json',params=payload)
        if to_loc_ob.status_code == requests.codes.ok:
            # print "OK"
            to_loc_json=to_loc_ob.json()
            # pp.pprint(frm_loc_json['results'][0]["geometry"]["location"])
            location=to_loc_json['results'][0]["geometry"]["location"]
            to_lat=location["lat"]
            to_lng=location["lng"]
            try:
                payload={"apikey":amadeus_api_key,'latitude':to_lat,'longitude':to_lng}
                near_airport_loc_ob_2=requests.get('https://api.sandbox.amadeus.com/v1.2/airports/nearest-relevant',params=payload)
                # print near_airport_loc_ob
                if near_airport_loc_ob_2.status_code == requests.codes.ok:
                    near_airport_loc_json_2=near_airport_loc_ob_2.json()
                    dic_to=near_airport_loc_json_2[0]
            except requests.exceptions.RequestException as e:
                print e

    except requests.exceptions.RequestException as e:
        print e

    if dic_from['airport']==dic_to['airport']:
        return HttpResponse(json.dumps({'status':"False",'error':"no airroute possible"}),content_type='application/javascript')
    if dic_from["distance"]>50:
        print "have to travel by train to airport"
        flag1=1
        response_dict1=rail_route_to_airport(frm,dic_from["airport_name"],date,"")
        print response_dict1

    if dic_to["distance"]>50:
        print "have to travel by train from airport"
        flag2=1
        print dic_to["airport_name"],to,date
        response_dict2=rail_route_to_airport(dic_to["airport_name"],to,date,"")
        print response_dict2
    

    try:
        payload={                                         
            'origin':dic_from['airport'],
            'destination':dic_to["airport"],
            'departure_date':date,
            'apikey':amadeus_api_key,
            'currency':"INR",
            'number_of_results':"1",
            "travel_class": travel_class}
        print payload
        flights_return_ob = requests.get('https://api.sandbox.amadeus.com/v1.2/flights/low-fare-search',params=payload)
        # print flights_return_ob.status_code
        if flights_return_ob.status_code == requests.codes.ok:
            flights_return_json=flights_return_ob.json()
            flights_array=flights_return_json["results"]
            response_dict['status']="True"
            if flag1:
                if response_dict1['not_found']:
                    response_dict['step1']="From "+frm+" to "+dic_from['airport_name']+" travelling distance "+str(dic_from["distance"])+" km"    
                else:    
                    response_dict['step1.1']=response_dict1['step1']
                    response_dict['step1.2']=response_dict1['step2']
                    response_dict['step1.3']=response_dict1['step3']
                    response_dict['train_to_airport_data']=response_dict1['train_data']
            else:
                response_dict['step1']="From "+frm+" to "+dic_from['airport_name']+" travelling distance "+str(dic_from["distance"])+" km"
            response_dict['step2']="From "+dic_from['airport_name']+" to "+dic_to['airport_name']
            response_dict['flights']=flights_array
            if flag2:
                if response_dict2['not_found']:
                    response_dict['step3']="From "+dic_to['airport_name']+" to "+to+" travelling distance "+str(dic_to["distance"])+" km"
                else:
                    response_dict['step3.1']=response_dict2['step1']
                    response_dict['step3.2']=response_dict2['step2']
                    response_dict['step3.3']=response_dict2['step3']
                    response_dict['train_from_airport_data']=response_dict2['train_data']
            else:
                response_dict['step3']="From "+dic_to['airport_name']+" to "+to+" travelling distance "+str(dic_to["distance"])+" km"
        else:
            return HttpResponse(json.dumps({'status':"False",'error':"departure_date should be after today's day"}),content_type='application/javascript')
    except requests.exceptions.RequestException as e:
        print e
    return response_dict



def valid_date(datestring):
    try:
        datetime.datetime.strptime(datestring, '%Y-%m-%d')
        return True
    except ValueError:
        return False

@ratelimit(key='ip', rate=rate, block=True)
def predict_city(request):
    public_key=request.GET.get('public_key', '') #example request=http://localhost:8000/predict_city/?departure_date=2016-04-03&origin=IIT%20Varanasi&duration=3&public_key=djWMgJqbAumanTIi034sO26lG19KfYDkxUwZLEc7otzpXHB8Fy&parsed_string=NKosistZBEUvJYFpHVO9836FtRna2SxYQ0AkjawS8/A=
    # print "public_key",public_key
    if public_key=='':
        return HttpResponse(json.dumps({'status':"False",'error':"Authentication failed, public_key not provided"}),content_type='application/javascript')
    else:
        found=False
        frm=request.GET.get('origin', '')
        if frm=='':
            return HttpResponse(json.dumps({'status':"False",'error':"origin not specfied"}),content_type='application/javascript')
        parsed_string=request.GET.get('parsed_string','')
        if parsed_string=='':
            return HttpResponse(json.dumps({'status':"False",'error':"parsed_string not provided"}),content_type='application/javascript')
        for user in UserDetails.objects.all():
            if user.public_key==public_key:
                u_private_key=user.private_key
                expected_parsed_string=provide_hash(frm,u_private_key)
                if expected_parsed_string!=parsed_string:
                    return HttpResponse(json.dumps({'status':"False",'error':"wrong parsed_string given"}),content_type='application/javascript')
                found=True
                break
        if found==False:
            return HttpResponse(json.dumps({'status':"False",'error':"Authentication failed, public_key not found"}),content_type='application/javascript')
    response_dict={} 
    date=request.GET.get('departure_date', '')
    if valid_date(date)==False:
        if date!="":
            return HttpResponse(json.dumps({'status':"False",'error':"plz enter date in yyyy-mm-dd format"}),content_type='application/javascript')
        else:
            return HttpResponse(json.dumps({'status':"False",'error':"plz specify the destination_date"}),content_type='application/javascript')
    duration=request.GET.get('duration','')
    max_min_ranges_rail={'1':{'min_range':0.00,'max_range':100.00},
                      '2':{'min_range':100.00,'max_range':300.00},
                      '3':{'min_range':200.00,'max_range':500.00},
                      '4':{'min_range':400.00,'max_range':700.00},
                      '5':{'min_range':500.00,'max_range':1000.00},
                      '6':{'min_range':600.00,'max_range':1300.00},
                      '7':{'min_range':700.00,'max_range':1500.00}}
    max_distance=max_min_ranges_rail[duration]['max_range']
    min_distance=max_min_ranges_rail[duration]['min_range']
    try:
        payload={'address':frm,'key':google_geocoding_api_key}
        frm_loc_ob = requests.get('https://maps.googleapis.com/maps/api/geocode/json',params=payload)
        if frm_loc_ob.status_code == requests.codes.ok:
            # print "OK"
            frm_loc_json=frm_loc_ob.json()
            # print frm_loc_json
            # pp.pprint(frm_loc_json['results'][0]["geometry"]["location"])
            location=frm_loc_json['results'][0]["geometry"]["location"]
            frm_lat=location["lat"]
            frm_lng=location["lng"]
            # print type(frm_lng)
    except:
        frm_lat=25.28   # of Varanasi in case of no internet #BHU #LOL
        frm_lng=82.96
    city_results=[]
    count=0
    for city in City.objects.all().order_by('-rating'):
        dist=distance_on_unit_sphere(frm_lat,frm_lng,float(city.lat),float(city.lng))
        if dist <= max_distance and dist >= min_distance:
            # print city
            count+=1
            city_result={}
            city_result['city']=city.name
            city_places=city.places_set.all()
            # print city_places
            city_result_places=[]
            for place in city_places:
                p={}
                p['name']=place.name
                p['img']=place.img_src
                p['about']=place.about
                city_result_places.append(p)
            city_result['city_places']=city_result_places
            city_results.append(city_result)
        if count >= 5:
            break

            # print city
    response_dict['city_results']=city_results
    return HttpResponse(json.dumps(response_dict),content_type='application/javascript')


@ratelimit(key='ip', rate=rate, block=True)
def predict_city_with_journey(request):
    response_dict={} #example request=http://localhost:8000/predict_city_with_journey/?departure_date=2016-04-03&origin=IIT%20Varanasi&duration=3&public_key=djWMgJqbAumanTIi034sO26lG19KfYDkxUwZLEc7otzpXHB8Fy&parsed_string=NKosistZBEUvJYFpHVO9836FtRna2SxYQ0AkjawS8/A=
    mode=request.GET.get('mode','')
    if mode=="":
        mode='rail'
    travel_class=request.GET.get('travel_class','')
    if travel_class=="":
        if mode=='rail':
            travel_class='3A'
        else:
            travel_class='ECONOMY'
    frm=request.GET.get('origin', '')
    if frm=="":
        return HttpResponse(json.dumps({'status':"False",'error':"plz specify the origin"}),content_type='application/javascript')
    date=request.GET.get('departure_date', '')
    if valid_date(date)==False:
        if date!="":
            return HttpResponse(json.dumps({'status':"False",'error':"plz enter date in yyyy-mm-dd format"}),content_type='application/javascript')
        else:
            return HttpResponse(json.dumps({'status':"False",'error':"plz specify the destination_date"}),content_type='application/javascript')
    duration=request.GET.get('duration','')
    max_min_ranges_rail={'1':{'min_range':0.00,'max_range':100.00},
                      '2':{'min_range':100.00,'max_range':300.00},
                      '3':{'min_range':200.00,'max_range':500.00},
                      '4':{'min_range':400.00,'max_range':700.00},
                      '5':{'min_range':500.00,'max_range':1000.00},
                      '6':{'min_range':600.00,'max_range':1300.00},
                      '7':{'min_range':700.00,'max_range':1500.00}}
    max_distance=max_min_ranges_rail[duration]['max_range']
    min_distance=max_min_ranges_rail[duration]['min_range']
    try:
        payload={'address':frm,'key':google_geocoding_api_key}
        frm_loc_ob = requests.get('https://maps.googleapis.com/maps/api/geocode/json',params=payload)
        if frm_loc_ob.status_code == requests.codes.ok:
            # print "OK"
            frm_loc_json=frm_loc_ob.json()
            # print frm_loc_json
            # pp.pprint(frm_loc_json['results'][0]["geometry"]["location"])
            location=frm_loc_json['results'][0]["geometry"]["location"]
            frm_lat=location["lat"]
            frm_lng=location["lng"]
            # print type(frm_lng)
    except:
        frm_lat=25.28   # of Varanasi in case of no internet #BHU
        frm_lng=82.96
    city_results=[]
    count=0
    for city in City.objects.all().order_by('-rating'):
        dist=distance_on_unit_sphere(frm_lat,frm_lng,float(city.lat),float(city.lng))
        if dist <= max_distance and dist >= min_distance:
            # print city
            count+=1
            city_result={}
            city_result['city']=city.name
            city_places=city.places_set.all()
            # print city_places
            city_result_places=[]
            for place in city_places:
                p={}
                p['name']=place.name
                p['img']=place.img_src
                p['about']=place.about
                city_result_places.append(p)
            
            try:
                if mode=='rail':
                    city_result['journey_details']=rail_route_to_airport(frm,city_result['city'],date,travel_class)
                else:
                    city_result['journey_details']=air_route_to_tour(frm,city_result['city'],date,travel_class)

            except Exception as e:
                city_result['journey_details']='We could not find any conventional route to '+city_result['city']+'. Soon we are going to launch our own special means! ;)'
            city_result['city_places']=city_result_places
            city_results.append(city_result)
        if count >= 3:
            break

            # print city
    response_dict['city_results']=city_results
    return HttpResponse(json.dumps(response_dict),content_type='application/javascript')




def distance_on_unit_sphere(lat1, long1, lat2, long2):
 
    # Convert latitude and longitude to 
    # spherical coordinates in radians.
    degrees_to_radians = math.pi/180.0
         
    # phi = 90 - latitude
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians
         
    # theta = longitude
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians
         
    # Compute spherical distance from spherical coordinates.
         
    # For two locations in spherical coordinates 
    # (1, theta, phi) and (1, theta', phi')
    # cosine( arc length ) = 
    #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length
     
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos( cos )
 
    # Remember to multiply arc by the radius of the earth 
    # in your favorite set of units to get length.
    return arc*6373

def index(request):
    context = {}
    return render(request, 'index.html', context)

def docs(request):
    context = {}
    return render(request, 'Documentation.html', context)

def faqs(request):
    context = {}
    return render(request, 'faqs.html', context)

@login_required(login_url='/account/login')
@ratelimit(key='ip', rate='2/h', block=True)
def newtoken(request):
    if request.method == "POST":
        try:
            u = UserDetails.objects.get(user=request.user)
            u.private_key = generate_key()
            u.public_key = generate_key()
            u.save()
            return JsonResponse({"private_key":u.private_key,'public_key':u.public_key})
        except Exception as e:
            print e
            return JsonResponse({"error":"true"})
