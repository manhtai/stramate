# Generated by Django 3.2.8 on 2021-10-18 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0003_auto_20211016_0943'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='name',
            field=models.TextField(blank=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='activity',
            name='start_location',
            field=models.TextField(blank=True, db_index=True),
        ),
    ]
