# Generated by Django 4.2.3 on 2024-11-15 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ArtiQuityapp', '0013_progress'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='profile_pictures/'),
        ),
    ]
