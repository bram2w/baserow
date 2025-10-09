"""
Script para crear 10 registros ficticios en la tabla Colabs
"""
from django.contrib.auth import get_user_model
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.fields.models import Field, SelectOption
import random

User = get_user_model()

# Obtener tabla Colabs (ID: 738)
table = TableHandler().get_table(738)
user = User.objects.get(id=3)

# Obtener los campos
fields = Field.objects.filter(table=table).order_by('id')
field_dict = {f.name: f for f in fields}

# Obtener las opciones del campo Coordinador
coordinador_field = field_dict['Coordinador']
coordinadores_options = list(SelectOption.objects.filter(field=coordinador_field))

print(f"📋 Creando 10 registros en tabla: {table.name}")
print(f"🔧 Campos disponibles: {[f.name for f in fields]}")
print(f"👥 Coordinadores: {[opt.value for opt in coordinadores_options]}\n")

# Datos ficticios
nombres = [
    "María González",
    "Carlos Rodríguez",
    "Ana Martínez",
    "José López",
    "Laura Hernández",
    "Pedro Sánchez",
    "Carmen Torres",
    "Miguel Flores",
    "Isabel Ramírez",
    "Roberto Jiménez"
]

nombres_cortos = [
    "María",
    "Carlos", 
    "Ana",
    "José",
    "Laura",
    "Pedro",
    "Carmen",
    "Miguel",
    "Isabel",
    "Roberto"
]

telefonos = [
    "+52 777 123 4501",
    "+52 777 123 4502",
    "+52 777 123 4503",
    "+52 777 123 4504",
    "+52 777 123 4505",
    "+52 777 123 4506",
    "+52 777 123 4507",
    "+52 777 123 4508",
    "+52 777 123 4509",
    "+52 777 123 4510"
]

instagrams = [
    "@maria.gonzalez",
    "@carlos.rodriguez",
    "@ana.martinez",
    "@jose.lopez",
    "@laura.hernandez",
    "@pedro.sanchez",
    "@carmen.torres",
    "@miguel.flores",
    "@isabel.ramirez",
    "@roberto.jimenez"
]

# Crear los 10 registros
created_rows = []
for i in range(10):
    # Seleccionar 1-2 coordinadores aleatorios
    num_coordinadores = random.randint(1, 2)
    selected_coordinadores = random.sample(coordinadores_options, num_coordinadores)
    
    # Preparar los valores usando el modelo de la tabla
    model = table.get_model()
    
    row_values = {
        f'field_{field_dict["Name"].id}': nombres[i],
        f'field_{field_dict["nombre"].id}': nombres_cortos[i],
        f'field_{field_dict["telefono"].id}': telefonos[i],
        f'field_{field_dict["instagram"].id}': instagrams[i],
    }
    
    row = RowHandler().create_row(
        user=user,
        table=table,
        values=row_values
    )
    
    # Añadir los coordinadores usando el campo many-to-many
    coordinador_field_attr = f'field_{field_dict["Coordinador"].id}'
    getattr(row, coordinador_field_attr).set([opt.id for opt in selected_coordinadores])
    row.save()
    
    coordinador_names = ", ".join([opt.value for opt in selected_coordinadores])
    created_rows.append(row)
    
    print(f"✅ Registro {i+1} creado:")
    print(f"   👤 Nombre: {nombres[i]}")
    print(f"   📱 Teléfono: {telefonos[i]}")
    print(f"   📷 Instagram: {instagrams[i]}")
    print(f"   👥 Coordinadores: {coordinador_names}")
    print()

print(f"\n🎉 ¡{len(created_rows)} registros creados exitosamente!")
