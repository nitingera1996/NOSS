# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apis', '0004_auto_20160224_1150'),
    ]

    operations = [
        migrations.AlterField(
            model_name='city',
            name='lat',
            field=models.CharField(default=b'0.00', max_length=15),
        ),
        migrations.AlterField(
            model_name='city',
            name='lng',
            field=models.CharField(default=b'0.00', max_length=15),
        ),
        migrations.AlterField(
            model_name='tags',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]
