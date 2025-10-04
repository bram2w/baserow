from django.contrib.auth import get_user_model

User = get_user_model()

# Obtener usuario test
test_user = User.objects.get(email="test@test.com")

# Establecer contraseña
test_user.set_password("test123")
test_user.save()

print(f"✅ Contraseña actualizada para: {test_user.email}")
print(f"🔑 Nueva contraseña: test123")
print(f"📧 Email: test@test.com")
