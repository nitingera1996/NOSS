# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apis', '0005_auto_20160224_1202'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userdetails',
            old_name='key',
            new_name='private_key',
        ),
        migrations.AddField(
            model_name='userdetails',
            name='public_key',
            field=models.CharField(default='qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvb', max_length=50),
            preserve_default=False,
        ),
    ]
