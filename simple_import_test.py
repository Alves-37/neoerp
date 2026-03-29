#!/usr/bin/env python3
"""
Teste simples de importação via API
"""

import requests

def simple_test():
    base_url = "https://neoerp-production.up.railway.app"
    
    # Login
    print("🔑 Fazendo login...")
    login_response = requests.post(f"{base_url}/auth/login", json={
        "email": "mutxutxu@gmail.com",
        "password": "Mutxutxu@43"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login falhou: {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json().get('access_token') or login_response.json().get('token')
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"✅ Token obtido: {token[:50]}...")
    
    # Testar endpoints básicos
    print("\n🔍 Testando endpoints:")
    
    endpoints = [
        "/products",
        "/product-categories", 
        "/me",
        "/auth/me",
        "/api/products",
        "/api/product-categories"
    ]
    
    for endpoint in endpoints:
        try:
            resp = requests.get(f"{base_url}{endpoint}", headers=headers)
            print(f"   {endpoint}: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    print(f"      📊 {len(data)} itens")
                elif isinstance(data, dict) and 'data' in data:
                    print(f"      📊 {len(data['data'])} itens")
                elif isinstance(data, dict) and 'total' in data:
                    print(f"      📊 {data['total']} itens totais")
        except Exception as e:
            print(f"   {endpoint}: ERRO - {e}")
    
    # Tentar criar uma categoria de teste
    print("\n📁 Criando categoria de teste...")
    cat_payload = {
        "name": "Categoria Teste API",
        "business_type": "restaurant"
    }
    
    cat_response = requests.post(f"{base_url}/product-categories", headers=headers, json=cat_payload)
    print(f"   Status: {cat_response.status_code}")
    if cat_response.status_code in [200, 201]:
        cat_data = cat_response.json()
        print(f"   ✅ Categoria criada: ID {cat_data.get('id')}")
        
        # Tentar criar um produto de teste
        print("\n📦 Criando produto de teste...")
        prod_payload = {
            "name": "Produto Teste API",
            "price": 100.00,
            "category_id": cat_data.get('id'),
            "business_type": "restaurant",
            "unit": "un",
            "is_active": True
        }
        
        prod_response = requests.post(f"{base_url}/products", headers=headers, json=prod_payload)
        print(f"   Status: {prod_response.status_code}")
        if prod_response.status_code in [200, 201]:
            prod_data = prod_response.json()
            print(f"   ✅ Produto criado: ID {prod_data.get('id')}")
            print(f"   🎉 API está funcionando!")
        else:
            print(f"   ❌ Erro ao criar produto: {prod_response.text}")
    else:
        print(f"   ❌ Erro ao criar categoria: {cat_response.text}")

if __name__ == "__main__":
    simple_test()
