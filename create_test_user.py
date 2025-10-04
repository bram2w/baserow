from django.contrib.auth import get_user_model
from baserow.core.models import Workspace, WorkspaceUser

User = get_user_model()

# Crear usuario test
test_user = User.objects.create_user(
    email="test@test.com",
    username="test@test.com",
    password="test123",
    first_name="Test",
    last_name="User"
)

print(f"✅ Usuario test creado")
print(f"🆔 User ID: {test_user.id}")
print(f"📧 Email: test@test.com")
print(f"🔑 Password: test123")

# Agregar al workspace Las Mañanitas
workspace = Workspace.objects.get(id=129)
WorkspaceUser.objects.create(
    workspace=workspace,
    user=test_user,
    permissions="MEMBER"
)

print(f"✅ Agregado al workspace: {workspace.name}")
