#!/usr/bin/env python3
"""
Criar localização e importar produtos
"""

import requests

def create_location_and_import():
    base_url = "https://neoerp-production.up.railway.app"
    
    # Login
    login = requests.post(f"{base_url}/auth/login", json={
        "email": "mutxutxu@gmail.com", 
        "password": "Mutxutxu@43"
    })
    
    token = login.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login realizado!")
    
    # Tentar diferentes endpoints para localizações
    location_endpoints = [
        "/stock-locations",
        "/locations", 
        "/establishments",
        "/branches",
        "/api/stock-locations",
        "/api/locations"
    ]
    
    print("\n🔍 Procurando endpoint de localizações...")
    
    for endpoint in location_endpoints:
        try:
            # Tentar GET
            get_resp = requests.get(f"{base_url}{endpoint}", headers=headers)
            print(f"GET {endpoint}: {get_resp.status_code}")
            
            if get_resp.status_code == 200:
                locations = get_resp.json()
                if locations:
                    print(f"✅ Encontradas {len(locations)} localizações!")
                    default_loc = locations[0]
                    default_loc_id = default_loc['id']
                    print(f"📍 Usando: {default_loc.get('name', 'N/A')} (ID: {default_loc_id})")
                    
                    # Importar produtos
                    import_products(base_url, headers, default_loc_id)
                    return
            
            # Tentar POST para criar
            post_resp = requests.post(f"{base_url}{endpoint}", headers=headers, json={
                "name": "Loja Principal",
                "type": "store",
                "is_default": True
            })
            
            print(f"POST {endpoint}: {post_resp.status_code}")
            
            if post_resp.status_code in [200, 201]:
                new_loc = post_resp.json()
                loc_id = new_loc.get('id')
                print(f"✅ Localização criada! ID: {loc_id}")
                
                # Importar produtos
                import_products(base_url, headers, loc_id)
                return
                
        except Exception as e:
            print(f"ERRO {endpoint}: {e}")
    
    print("❌ Nenhum endpoint de localização funcionou!")
    
    # Tentar importar com ID fake (pode funcionar)
    print("\n🚀 Tentando importar com location_id fake...")
    import_products(base_url, headers, 1)

def import_products(base_url, headers, location_id):
    print(f"\n🚀 Importando produtos com location_id: {location_id}")
    
    # Obter categorias
    cats = requests.get(f"{base_url}/product-categories", headers=headers).json()
    cat_map = {c['name']: c['id'] for c in cats}
    
    # Produtos de teste
    products = [
        {"name": "2M garrafa", "price": 80, "category": "Bebidas"},
        {"name": "Red Bull", "price": 150, "category": "Bebidas"},
        {"name": "Pizza", "price": 100, "category": "Pratos"},
        {"name": "Hamburguer", "price": 300, "category": "Pratos"},
        {"name": "Sobremesa", "price": 75, "category": "Sobremesas"}
    ]
    
    success = 0
    
    for i, p in enumerate(products, 1):
        payload = {
            "name": p["name"],
            "price": p["price"],
            "category_id": cat_map[p["category"]],
            "default_location_id": location_id,
            "business_type": "restaurant",
            "unit": "un",
            "is_active": True,
            "track_stock": True,
            "sku": f"RES-10-{i:03d}"
        }
        
        response = requests.post(f"{base_url}/products", headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            prod_data = response.json()
            print(f"✅ {i}. {p['name']} - MZN {p['price']} (ID: {prod_data.get('id')})")
            success += 1
        else:
            print(f"❌ {i}. {p['name']} - ERRO {response.status_code}")
            if response.status_code == 422:
                print(f"     📄 {response.text}")
    
    print(f"\n🎉 Importação concluída!")
    print(f"✅ Sucesso: {success} produtos")
    
    if success > 0:
        print(f"\n🌐 Acesse: https://neoerp-production.up.railway.app")
        print(f"📦 Os produtos devem aparecer agora!")
        print(f"🔄 Recarregue a página de produtos")

if __name__ == "__main__":
    create_location_and_import()
