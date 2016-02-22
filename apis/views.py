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
import datetime
import ast

google_geocoding_api_key="AIzaSyAVPebYRc6oQkB9gT0f-z63IStnR02bQ34"
amadeus_api_key="oJS13442zS4sbBnZVeGa6Y6Y38BzmPyC"
railway_api_key="jruwt3809"
google_matrix_api_key="AIzaSyBqLD2_EXtqKWi8WPWEKiELVNrINuTa91s"

def generate_key():
    s = string.letters + string.digits
    return ''.join(random.sample(s, 50))

def openvpn_password(request):
    # a=request.GET.get('q', '')
    # print a
    response_dict={}
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
        print e
        response_dict['status']="False"
        response_dict['message']="Check ur internet connection"
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

def rail_route(request):
    response_dict={} #example request=http://localhost:8000/airroute/?destination=Krishna%20Nagar,%20Mathura&departure_date=2016-04-03&travel_class=ECONOMY&origin=IIT%20Varanasi
    frm=request.GET.get('origin', '')
    if frm==None:
        return HttpResponse(json.dumps({'status':"False",'error':"plz specify the origin"}),content_type='application/javascript')
    to=request.GET.get('destination', '')
    if to==None:
        return HttpResponse(json.dumps({'status':"False",'error':"plz specify the destination"}),content_type='application/javascript')
    date=request.GET.get('departure_date', '')
    if frm==to:
        return HttpResponse(json.dumps({'status':"False",'error':"no railroute possible"}),content_type='application/javascript')
    if valid_date(date)==False:
        if date:
            return HttpResponse(json.dumps({'status':"False",'error':"plz enter date in yyyy-mm-dd format"}),content_type='application/javascript')
        else:
            return HttpResponse(json.dumps({'status':"False",'error':"plz specify the destination_date"}),content_type='application/javascript')
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
    print "second part done"
    travel_class=request.GET.get('travel_class', '')
    if travel_class==None:
        travel_class="3A"
    response_dict['from']=source_city
    response_dict['to']=dest_city
    try:
        payload={'from_city':source_city,'to_city':dest_city,'class':travel_class,'date':date,'adults':1,'children':0,'male_seniors':0,'female_seniors':0}
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
    except requests.exceptions.RequestException as e:
        print e
    return HttpResponse(json.dumps(response_dict),content_type='application/javascript')
            

def rail_route_to_airport(frm,to,date):
    response_dict={} #example request=http://localhost:8000/airroute/?destination=Krishna%20Nagar,%20Mathura&departure_date=2016-04-03&travel_class=ECONOMY&origin=IIT%20Varanasi
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
    print "second part done"
    travel_class="3A"
    response_dict['from']=source_city
    response_dict['to']=dest_city
    try:
        payload={'from_city':source_city,'to_city':dest_city,'class':travel_class,'date':date,'adults':1,'children':0,'male_seniors':0,'female_seniors':0}
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



def air_route(request):
    flag1,flag2=[0,0]
    response_dict={} #example request=http://localhost:8000/airroute/?destination=Krishna%20Nagar,%20Mathura&departure_date=2016-04-03&travel_class=ECONOMY&origin=IIT%20Varanasi
    frm=request.GET.get('origin', '')
    if frm==None:
        return HttpResponse(json.dumps({'status':"False",'error':"plz specify the origin"}),content_type='application/javascript')
    to=request.GET.get('destination', '')
    if to==None:
        return HttpResponse(json.dumps({'status':"False",'error':"plz specify the destination"}),content_type='application/javascript')
    date=request.GET.get('departure_date', '')
    if frm==to:
        return HttpResponse(json.dumps({'status':"False",'error':"no airroute possible"}),content_type='application/javascript')
    if valid_date(date)==False:
        if date:
            return HttpResponse(json.dumps({'status':"False",'error':"plz enter date in yyyy-mm-dd format"}),content_type='application/javascript')
        else:
            return HttpResponse(json.dumps({'status':"False",'error':"plz specify the destination_date"}),content_type='application/javascript')

    travel_class=request.GET.get('travel_class', '')
    if travel_class==None:
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

    if dic_from["distance"]>50:
        print "have to travel by train to airport"
        flag1=1
        response_dict1=rail_route_to_airport(frm,dic_from["airport_name"],date)
        print response_dict1

    if dic_to["distance"]>50:
        print "have to travel by train from airport"
        flag2=1
        print dic_to["airport_name"],to,date
        response_dict2=rail_route_to_airport(dic_to["airport_name"],to,date)
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
    return HttpResponse(json.dumps(response_dict),content_type='application/javascript')

def valid_date(datestring):
    try:
        datetime.datetime.strptime(datestring, '%Y-%m-%d')
        return True
    except ValueError:
        return False
