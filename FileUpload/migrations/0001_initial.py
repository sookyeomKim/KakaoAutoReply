# Generated by Django 2.1 on 2018-08-27 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FileUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='cookies/')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='CREATE_DATE')),
                ('modify_date', models.DateTimeField(auto_now=True, verbose_name='MODIFY_DATE')),
            ],
            options={
                'db_table': 'FileUpload',
            },
        ),
    ]
