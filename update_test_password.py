#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baserow.config.settings.base')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(email='test@test.com')
user.set_password('test123')
user.save()

print("✅ Password updated for test@test.com")
print(f"   Email: {user.email}")
print(f"   Active: {user.is_active}")
print(f"   Staff: {user.is_staff}")
