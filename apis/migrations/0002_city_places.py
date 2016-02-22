# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apis', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=b'100')),
                ('lat', models.CharField(default=b'0.00', max_length=8)),
                ('lng', models.CharField(default=b'0.00', max_length=8)),
            ],
        ),
        migrations.CreateModel(
            name='Places',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(default=b'yo')),
                ('img_src', models.TextField(default=b'http://www.google.com')),
                ('city', models.ForeignKey(to='apis.City')),
            ],
        ),
    ]
