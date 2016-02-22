from django.db import models
from django.contrib.auth.models import User

class UserDetails(models.Model):
	user = models.OneToOneField(User)
	key = models.CharField(max_length=50)

	def __unicode__(self):
		return self.user.email

class City(models.Model):
	name = models.CharField(max_length="100")
	lat = models.CharField(max_length=8,default="0.00")
	lng = models.CharField(max_length=8,default="0.00")

	def __unicode__(self):
		return self.name


class Places(models.Model):
	name=models.TextField(default="yo")
	img_src=models.TextField(default="http://www.google.com")
	city=models.ForeignKey(City)

	def __unicode__(self):
		return self.name
