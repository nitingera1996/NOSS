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

google_geocoding_api_key="AIzaSyAVPebYRc6oQkB9gT0f-z63IStnR02bQ34"
amadeus_api_key="oJS13442zS4sbBnZVeGa6Y6Y38BzmPyC"

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

def air_route(request):
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
                    # print dic_from
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
                    # print dic_to
    				# pp.pprint(near_airport_loc_json_2[0])
            except requests.exceptions.RequestException as e:
                print e

    except requests.exceptions.RequestException as e:
        print e
    try:
        payload={                                         
            'origin':dic_from['airport'],
            'destination':dic_to["airport"],
            'departure_date':date,
            'apikey':amadeus_api_key,
            'currency':"INR",
            'number_of_results':"1",
            "travel_class": travel_class}
        flights_return_ob = requests.get('https://api.sandbox.amadeus.com/v1.2/flights/low-fare-search',params=payload)
        # print flights_return_ob.status_code
        if flights_return_ob.status_code == requests.codes.ok:
            flights_return_json=flights_return_ob.json()
            # print flights_return_json
            flights_array=flights_return_json["results"]
    		# print flights_return_ob.from_cache
    		# pp.pprint(flights_array)
            response_dict['status']="True"
            response_dict['step 1']="From "+frm+" to "+dic_from['airport_name']+" travelling distance "+str(dic_from["distance"])+" km"
            response_dict['step_2']="From "+dic_from['airport_name']+" to "+dic_to['airport_name']
            response_dict['flights']=flights_array
            response_dict['step_3']="From "+dic_to['airport_name']+" to "+to+" travelling distance "+str(dic_to["distance"])+" km"
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