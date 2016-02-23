# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apis', '0002_city_places'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tags',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=b'15')),
            ],
        ),
        migrations.AddField(
            model_name='city',
            name='rating',
            field=models.IntegerField(default=b'1'),
        ),
        migrations.AddField(
            model_name='places',
            name='about',
            field=models.TextField(default=b'something'),
        ),
        migrations.AddField(
            model_name='city',
            name='tags',
            field=models.ManyToManyField(to='apis.Tags'),
        ),
    ]
