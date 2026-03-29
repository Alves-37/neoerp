#!/usr/bin/env python3
"""
Importação final simplificada
"""

import requests

def final_import():
    base_url = "https://neoerp-production.up.railway.app"
    
    # Login
    login = requests.post(f"{base_url}/auth/login", json={
        "email": "mutxutxu@gmail.com", 
        "password": "Mutxutxu@43"
    })
    
    token = login.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login realizado!")
    
    # Obter categorias
    cats = requests.get(f"{base_url}/product-categories", headers=headers).json()
    cat_map = {c['name']: c['id'] for c in cats}
    
    # 5 produtos simples
    products = [
        {"name": "2M garrafa", "price": 80, "category": "Bebidas"},
        {"name": "Red Bull", "price": 150, "category": "Bebidas"},
        {"name": "Pizza", "price": 100, "category": "Pratos"},
        {"name": "Hamburguer", "price": 300, "category": "Pratos"},
        {"name": "Sobremesa", "price": 75, "category": "Sobremesas"}
    ]
    
    print(f"🚀 Importando {len(products)} produtos...")
    
    for i, p in enumerate(products, 1):
        payload = {
            "name": p["name"],
            "price": p["price"],
            "category_id": cat_map[p["category"]],
            "is_active": True
        }
        
        r = requests.post(f"{base_url}/products", headers=headers, json=payload)
        
        if r.status_code in [200, 201]:
            print(f"✅ {i}. {p['name']} - MZN {p['price']}")
        else:
            print(f"❌ {i}. {p['name']} - ERRO {r.status_code}")
    
    print(f"\n🌐 Acesse: https://neoerp-production.up.railway.app")
    print(f"📦 Verifique os produtos!")

if __name__ == "__main__":
    final_import()
