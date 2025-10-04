import requests
import json

# URL de login (desde dentro del contenedor backend)
login_url = "http://localhost:8000/api/user/token-auth/"

# Credenciales
credentials = {
    "email": "test@test.com",
    "password": "test123"
}

print(f"🔐 Intentando login en: {login_url}")
print(f"📧 Email: {credentials['email']}")
print(f"🔑 Password: {credentials['password']}")
print("-" * 60)

try:
    # Hacer POST request
    response = requests.post(login_url, json=credentials)
    
    print(f"📊 Status Code: {response.status_code}")
    print(f"📄 Response Headers:")
    for key, value in response.headers.items():
        print(f"   {key}: {value}")
    
    print("\n📝 Response Body:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ LOGIN EXITOSO!")
        print(f"🎟️  Token: {data.get('token', 'N/A')}")
        print(f"👤 User ID: {data.get('user', {}).get('id', 'N/A')}")
        print(f"📧 Email: {data.get('user', {}).get('email', 'N/A')}")
        print(f"👨‍💼 Username: {data.get('user', {}).get('username', 'N/A')}")
        
        # Guardar token para usar después
        with open('/tmp/test_token.txt', 'w') as f:
            f.write(data.get('token', ''))
        print("\n💾 Token guardado en /tmp/test_token.txt")
        
    else:
        print("\n❌ LOGIN FALLIDO!")
        
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ Error de conexión: {e}")
except Exception as e:
    print(f"\n❌ Error inesperado: {e}")
    import traceback
    traceback.print_exc()
