# Generated by Django 4.2.3 on 2024-10-09 23:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ArtiQuityapp', '0003_alter_user_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=255),
        ),
    ]