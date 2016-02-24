from django.db import models
from django.contrib.auth.models import User

class UserDetails(models.Model):
	user = models.OneToOneField(User)
	private_key = models.CharField(max_length=50)
	public_key = models.CharField(max_length=50)

	def __unicode__(self):
		return self.user.email

class Tags(models.Model):
	name=models.CharField(max_length=50)

	def __unicode__(self):
		return self.name
		
class City(models.Model):
	name = models.CharField(max_length=100)
	lat = models.CharField(max_length=15,default="0.00")
	lng = models.CharField(max_length=15,default="0.00")
	tags = models.ManyToManyField(Tags)
	rating = models.IntegerField(default='1')

	def __unicode__(self):
		return self.name


class Places(models.Model):
	name=models.TextField(default="yo")
	img_src=models.TextField(default="http://www.google.com")
	city=models.ForeignKey(City)
	about=models.TextField(default='something')

	def __unicode__(self):
		return self.name

