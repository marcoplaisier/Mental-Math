from django.db import migrations


def create_default_users(apps, schema_editor):
    UserProfile = apps.get_model('trainer', 'UserProfile')
    default_users = ['Arthur', 'Lena', 'Marco', 'Susanne']
    for name in default_users:
        UserProfile.objects.get_or_create(name=name)


def remove_default_users(apps, schema_editor):
    UserProfile = apps.get_model('trainer', 'UserProfile')
    UserProfile.objects.filter(name__in=['Arthur', 'Lena', 'Marco', 'Susanne']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("trainer", "0002_userprofile_answer_user"),
    ]

    operations = [
        migrations.RunPython(create_default_users, remove_default_users),
    ]
