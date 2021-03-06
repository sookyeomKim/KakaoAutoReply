# Generated by Django 2.1 on 2018-08-27 16:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Post', '0001_initial'),
        ('Channel', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reply',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('execute_time', models.DateTimeField()),
                ('interval_time', models.IntegerField()),
                ('trigger', models.BooleanField(default=False)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('modify_date', models.DateTimeField(auto_now=True)),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Channel.Channel')),
                ('post', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='Post.Post')),
            ],
            options={
                'db_table': 'Reply',
            },
        ),
    ]
