from django.core.management.base import BaseCommand, CommandError
from apis.models import *
from bs4 import BeautifulSoup
import requests
import requests
google_geocoding_api_key="AIzaSyAVPebYRc6oQkB9gT0f-z63IStnR02bQ34"


class Command(BaseCommand):
	args="arguments are not needed"
	help = "just populates the database"

	def handle(self, *args,**options):
		r  = requests.get("http://100besttouristdestinationsinindi.blogspot.sg/")
		data = r.text
		soup = BeautifulSoup(data)
		tags=soup.find_all('b')
		for t in tags:
			l=str(t.get_text())
			if l.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
				try:
					# print l.split(".",1)[1][1:]
					frm=l.split(".",1)[1][1:]
					frm=frm.split('(',1)[0]
					frm=frm.split('/',1)[0]
					frm=frm.split(' ',1)[0]
					# print frm
					payload={'address':frm,'key':google_geocoding_api_key}
					frm_loc_ob = requests.get('https://maps.googleapis.com/maps/api/geocode/json',params=payload)
					# print frm_loc_ob
					if frm_loc_ob.status_code == requests.codes.ok:
						#print "OK"
						frm_loc_json=frm_loc_ob.json()
						# print(frm_loc_json['results'][0]["geometry"]["location"])
						location=frm_loc_json['results'][0]["geometry"]["location"]
						frm_lat=location["lat"]
						frm_lng=location["lng"]
						frm_query=frm[0].lower()+frm[1:]
						c=City()
						c.name=frm
						c.lat=frm_lat
						c.lng=frm_lng
						c.save()
						self.stdout.write(frm)
						# print frm,frm_lat,frm_lng
						try:
							r  = requests.get("http://travel.india.com/"+frm_query+"/places-to-visit/")
							data = r.text
							soup = BeautifulSoup(data)
							tags=soup.find_all('figure')
							for t in tags:
								try:
									# print t.get('class')[0]
									if t.get('class')[0]=="col-sm-12":
										#l=t.get_text().encode('utf-8')
										more_tags=t.find_all('a')
										for mt in more_tags:
											if mt.get('class')[0]=="imgt":
												img=mt.img
												src=img['data-lazy-src']
												name=img['alt']
												p=Places()
												p.city=c
												p.img_src=src
												p.name=name
												p.save()
												# print src,name
								except:
									pass
						except:
							pass
				except requests.exceptions.RequestException as e:
					pass
					# print e
