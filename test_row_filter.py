#!/usr/bin/env python
"""
Test row filter - Ver solo registros con Coordinador=Anetth
"""

import requests
import json

BASE_URL = "http://localhost:4000"
TOKEN = "test_user_token_123456"  # Token del usuario test@test.com

# Get rows from table 738 (Colabs)
print("📊 Getting rows from table 738 (Colabs) as test@test.com...")
headers = {
    "Authorization": f"Token {TOKEN}"
}

rows_response = requests.get(
    f"{BASE_URL}/api/database/rows/table/738/",
    headers=headers
)

if rows_response.status_code != 200:
    print(f"❌ Get rows failed: {rows_response.status_code}")
    print(rows_response.text)
    exit(1)

data = rows_response.json()
print(f"\n✅ Response received!")
print(f"Total registros visibles: {data['count']}")
print(f"\nRegistros:")

for row in data['results']:
    # Buscar el valor del coordinador (field_7105)
    coordinador_id = row.get('field_7105')
    coordinador_nombre = "?"
    if coordinador_id == 3044:
        coordinador_nombre = "Brenda"
    elif coordinador_id == 3045:
        coordinador_nombre = "Anetth"
    elif coordinador_id == 3046:
        coordinador_nombre = "Andrea"
    elif coordinador_id == 3047:
        coordinador_nombre = "Hugo"
    
    print(f"  - ID {row['id']}: {row.get('field_7102', 'Sin nombre')} | Coordinador: {coordinador_nombre} (ID: {coordinador_id})")

print("\n" + "="*80)
if data['count'] == 3:
    print("✅ ¡FILTRO FUNCIONA! Solo se muestran 3 registros (los de Anetth)")
else:
    print(f"⚠️  Se esperaban 3 registros, pero se obtuvieron {data['count']}")
