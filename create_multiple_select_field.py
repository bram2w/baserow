"""
Script para crear campo de opción múltiple en tabla Colabs
"""
from django.contrib.auth import get_user_model
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import SelectOption

User = get_user_model()

# Obtener tabla Colabs (ID: 738)
table = TableHandler().get_table(738)

# Obtener usuario admin (ID: 3)
user = User.objects.get(id=3)

print(f"📋 Tabla: {table.name} (ID: {table.id})")
print(f"👤 Usuario: {user.email}")

# Crear campo de opción múltiple
field = FieldHandler().create_field(
    user=user,
    table=table,
    type_name='multiple_select',
    name='Coordinador',
    select_options=[
        {'value': 'Brenda', 'color': 'blue'},
        {'value': 'Anetth', 'color': 'green'},
        {'value': 'Andrea', 'color': 'orange'},
        {'value': 'Hugo', 'color': 'red'},
    ]
)

print(f"\n✅ Campo creado exitosamente!")
print(f"🆔 Field ID: {field.id}")
print(f"📝 Nombre: {field.name}")
print(f"🔧 Tipo: {field.get_type().type}")

# Mostrar las opciones creadas
options = SelectOption.objects.filter(field=field)
print(f"\n🎨 Opciones creadas:")
for opt in options:
    print(f"  - {opt.value} (color: {opt.color})")
