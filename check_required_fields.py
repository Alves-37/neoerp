#!/usr/bin/env python3
"""
Verificar campos obrigatórios para criar produto
"""

import requests

def check_required_fields():
    base_url = "https://neoerp-production.up.railway.app"
    
    # Login
    login = requests.post(f"{base_url}/auth/login", json={
        "email": "mutxutxu@gmail.com", 
        "password": "Mutxutxu@43"
    })
    
    token = login.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 VERIFICANDO CAMPOS OBRIGATÓRIOS")
    print("=" * 50)
    
    # Obter categorias
    cats = requests.get(f"{base_url}/product-categories", headers=headers).json()
    cat_map = {c['name']: c['id'] for c in cats}
    first_cat_id = list(cat_map.values())[0]
    
    print(f"📁 Usando categoria ID: {first_cat_id}")
    
    # Testar diferentes payloads
    test_payloads = [
        {
            "name": "Teste Produto",
            "price": 100,
            "category_id": first_cat_id,
            "is_active": True
        },
        {
            "name": "Teste Produto",
            "price": 100,
            "category_id": first_cat_id,
            "business_type": "restaurant",
            "unit": "un",
            "is_active": True
        },
        {
            "name": "Teste Produto",
            "price": 100,
            "cost": 70,
            "category_id": first_cat_id,
            "business_type": "restaurant",
            "unit": "un",
            "is_active": True,
            "track_stock": True
        },
        {
            "name": "Teste Produto",
            "price": 100,
            "cost": 70,
            "category_id": first_cat_id,
            "business_type": "restaurant",
            "unit": "un",
            "is_active": True,
            "track_stock": True,
            "min_stock": 5,
            "sku": "TEST-001"
        }
    ]
    
    for i, payload in enumerate(test_payloads, 1):
        print(f"\n🧪 Teste {i}:")
        print(f"Payload: {payload}")
        
        response = requests.post(f"{base_url}/products", headers=headers, json=payload)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("✅ SUCESSO!")
            prod_data = response.json()
            print(f"Produto criado: ID {prod_data.get('id')}")
            break
        else:
            print(f"❌ ERRO: {response.text}")
    
    # Verificar produtos existentes para entender a estrutura
    print(f"\n📦 Analisando produtos existentes...")
    existing = requests.get(f"{base_url}/products", headers=headers, params={"limit": 1})
    
    if existing.status_code == 200:
        data = existing.json()
        if isinstance(data, dict) and 'data' in data and data['data']:
            sample = data['data'][0]
            print(f"Exemplo de produto existente:")
            for key, value in sample.items():
                print(f"  {key}: {value}")

if __name__ == "__main__":
    check_required_fields()
