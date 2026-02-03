import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_project.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute('DELETE FROM django_migrations WHERE app = "appCore"')
cursor.execute('DELETE FROM django_migrations WHERE app = "admin"')
print('Migration history cleared')
