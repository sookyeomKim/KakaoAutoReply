# Generated by Django 2.1 on 2018-08-27 17:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Post', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-post_register_date']},
        ),
    ]
