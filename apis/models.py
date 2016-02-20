from django.db import models
from django.contrib.auth.models import User

class UserDetails(models.Model):
	user = models.OneToOneField(User)
	key = models.CharField(max_length=50)

	def __unicode__(self):
		return self.user.email