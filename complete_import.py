#!/usr/bin/env python3
"""
Importação completa para produção com todos os campos necessários
"""

import requests

# Dados completos dos produtos
products_data = [
    {"name": "2M garrafa", "price": 80.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "2M lata", "price": 90.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Agua Pequena", "price": 50.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Agua Tonica", "price": 60.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Agua grande", "price": 100.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Amarula", "price": 1400.00, "stock": 100, "category": "Outos"},
    {"name": "Azinhas", "price": 300.00, "stock": 104, "category": "Outos"},
    {"name": "Bife Completo", "price": 800.00, "stock": 10, "category": "Congelados"},
    {"name": "Bull dog", "price": 3300.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "C double burger", "price": 500.00, "stock": 10, "category": "Bolos e salgados"},
    {"name": "Cabeca de Peixe", "price": 200.00, "stock": 10, "category": "Outos"},
    {"name": "Cabeca de Vaca", "price": 200.00, "stock": 10, "category": "Outos"},
    {"name": "Caldo verde", "price": 150.00, "stock": 10, "category": "Azeites"},
    {"name": "Cappy", "price": 80.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Carne de porco", "price": 800.00, "stock": 10, "category": "Congelados"},
    {"name": "Ceres", "price": 200.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Champanhe Anabela", "price": 1300.00, "stock": 100, "category": "Outos"},
    {"name": "Champanhe JS", "price": 1200.00, "stock": 100, "category": "Outos"},
    {"name": "Champanhe Martini Rose", "price": 1200.00, "stock": 100, "category": "Outos"},
    {"name": "Champanhe Toste", "price": 1500.00, "stock": 100, "category": "Outos"},
    {"name": "Chamussas", "price": 25.00, "stock": 10, "category": "Outos"},
    {"name": "Chourico", "price": 300.00, "stock": 10, "category": "Outos"},
    {"name": "Cochinhas", "price": 30.00, "stock": 9, "category": "Outos"},
    {"name": "Compal", "price": 200.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Dobrada", "price": 200.00, "stock": 10, "category": "Outos"},
    {"name": "Dry Lemon", "price": 150.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Escape Vodka", "price": 1000.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Four Causin Grade", "price": 1600.00, "stock": 100, "category": "Outos"},
    {"name": "Frango 1 quarto", "price": 300.00, "stock": 10, "category": "Congelados"},
    {"name": "Frango a Passarinho", "price": 1250.00, "stock": 10, "category": "Congelados"},
    {"name": "Frango assado 1", "price": 1200.00, "stock": 10, "category": "Congelados"},
    {"name": "Frango assado meio", "price": 600.00, "stock": 10, "category": "Congelados"},
    {"name": "Galinha Fumado", "price": 1500.00, "stock": 10, "category": "Congelados"},
    {"name": "Galo Dourado", "price": 1100.00, "stock": 100, "category": "Outos"},
    {"name": "Gatao", "price": 1500.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Gordon", "price": 1100.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Grants", "price": 1800.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "HENICKER", "price": 100.00, "stock": 500, "category": "Outos"},
    {"name": "Hamburger Completo", "price": 300.00, "stock": 8, "category": "Bolos e salgados"},
    {"name": "Hanked Bannister", "price": 1100.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Havelock", "price": 1100.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Humburger S", "price": 250.00, "stock": 10, "category": "Bolos e salgados"},
    {"name": "Joh walker red", "price": 1800.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "John Walker black", "price": 3500.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Maicgregor", "price": 1500.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Martine", "price": 1400.00, "stock": 100, "category": "Outos"},
    {"name": "Mutxutxu de galinha", "price": 200.00, "stock": 110, "category": "Outos"},
    {"name": "Pizza 4 estacoes", "price": 100.00, "stock": 10, "category": "pizzas"},
    {"name": "Pizza de atum", "price": 700.00, "stock": 10, "category": "pizzas"},
    {"name": "Pizza de frango", "price": 800.00, "stock": 10, "category": "pizzas"},
    {"name": "Pizza vegetariana", "price": 700.00, "stock": 10, "category": "pizzas"},
    {"name": "Quinta da bolota", "price": 1200.00, "stock": 100, "category": "Outos"},
    {"name": "Red Bull", "price": 150.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Refresco em lata", "price": 60.00, "stock": 97, "category": "Sumos, agua e refrescos"},
    {"name": "Rose Grande", "price": 1600.00, "stock": 100, "category": "Outos"},
    {"name": "Rusian", "price": 1000.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Silk spice", "price": 1800.00, "stock": 100, "category": "Outos"},
    {"name": "Sopa de Feijao", "price": 150.00, "stock": 10, "category": "Azeites"},
    {"name": "Sopa de legumes", "price": 150.00, "stock": 10, "category": "Azeites"},
    {"name": "Takeaway", "price": 30.00, "stock": 100, "category": "Outos"},
    {"name": "Tbone", "price": 800.00, "stock": 10, "category": "Congelados"},
    {"name": "Tostas com batata frita", "price": 300.00, "stock": 10, "category": "Outos"},
    {"name": "Worce", "price": 300.00, "stock": 10, "category": "Outos"},
    {"name": "altum", "price": 800.00, "stock": 10, "category": "Outos"},
    {"name": "bermine", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "bife trinchado", "price": 700.00, "stock": 101, "category": "Outos"},
    {"name": "brizer", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "brutal", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "budweiser", "price": 100.00, "stock": 10, "category": "Outos"},
    {"name": "cape ruby", "price": 1100.00, "stock": 10, "category": "Outos"},
    {"name": "casal garcia", "price": 1200.00, "stock": 10, "category": "Outos"},
    {"name": "castle lite", "price": 100.00, "stock": 10, "category": "Outos"},
    {"name": "celler cast", "price": 1100.00, "stock": 100, "category": "Outos"},
    {"name": "chima", "price": 100.00, "stock": 10, "category": "Bolachas,doces"},
    {"name": "dose de arroz", "price": 100.00, "stock": 10, "category": "Bolachas,doces"},
    {"name": "dose de batata", "price": 100.00, "stock": 10, "category": "Bolachas,doces"},
    {"name": "drosdy hof", "price": 800.00, "stock": 10, "category": "Outos"},
    {"name": "duas quintas", "price": 1100.00, "stock": 10, "category": "Outos"},
    {"name": "filetes", "price": 800.00, "stock": 10, "category": "Temperos"},
    {"name": "gazela", "price": 1100.00, "stock": 10, "category": "Outos"},
    {"name": "hunters dray", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "hunters gold", "price": 100.00, "stock": 10, "category": "Outos"},
    {"name": "jamson", "price": 1500.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "lemone", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "lulas", "price": 800.00, "stock": 10, "category": "Temperos"},
    {"name": "mao de vaca", "price": 200.00, "stock": 9, "category": "Outos"},
    {"name": "pandora", "price": 1100.00, "stock": 10, "category": "Outos"},
    {"name": "peixe chambo grande", "price": 1000.00, "stock": 10, "category": "Temperos"},
    {"name": "peixe chambo medio", "price": 800.00, "stock": 10, "category": "Temperos"},
    {"name": "peixe chambo pequeno", "price": 600.00, "stock": 10, "category": "Temperos"},
    {"name": "prego no pao", "price": 300.00, "stock": 10, "category": "Bolos e salgados"},
    {"name": "prego no prato", "price": 450.00, "stock": 10, "category": "Bolos e salgados"},
    {"name": "preta grande", "price": 80.00, "stock": 10, "category": "Outos"},
    {"name": "preta lata", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "preta pequena", "price": 100.00, "stock": 10, "category": "Outos"},
    {"name": "saladas", "price": 75.00, "stock": 10, "category": "Bolachas,doces"},
    {"name": "sande de ovo", "price": 200.00, "stock": 10, "category": "Bolos e salgados"},
    {"name": "segredo sao miguel", "price": 1200.00, "stock": 10, "category": "Outos"},
    {"name": "spin", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "super bock", "price": 80.00, "stock": 10, "category": "Outos"},
    {"name": "vinho cabriz", "price": 1200.00, "stock": 10, "category": "Outos"},
    {"name": "vinho portada", "price": 1200.00, "stock": 10, "category": "Outos"}
]

def complete_import():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🚀 IMPORTAÇÃO COMPLETA PARA PRODUÇÃO")
    print("=" * 60)
    
    # Login
    print("🔑 Fazendo login...")
    login_response = requests.post(f"{base_url}/auth/login", json={
        "email": "mutxutxu@gmail.com",
        "password": "Mutxutxu@43"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login falhou: {login_response.status_code}")
        return
    
    token = login_response.json().get('access_token')
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login realizado!")
    
    # Obter informações do usuário
    user_response = requests.get(f"{base_url}/auth/me", headers=headers)
    if user_response.status_code == 200:
        user_data = user_response.json()
        print(f"👤 Usuário: {user_data.get('email')}")
        print(f"🏢 Empresa: {user_data.get('company_name')}")
    
    # Obter localizações (stock locations)
    print("\n📍 Obtendo localizações...")
    locations_response = requests.get(f"{base_url}/stock-locations", headers=headers)
    
    default_location_id = None
    if locations_response.status_code == 200:
        locations = locations_response.json()
        print(f"📍 {len(locations)} localizações encontradas")
        
        # Procurar localização padrão
        for loc in locations:
            if loc.get('is_default') or loc.get('type') == 'store':
                default_location_id = loc.get('id')
                print(f"✅ Localização padrão: {loc.get('name')} (ID: {default_location_id})")
                break
    
    if not default_location_id:
        # Criar localização padrão
        print("⚠️  Criando localização padrão...")
        loc_payload = {
            "name": "Loja Principal",
            "type": "store",
            "is_default": True
        }
        
        loc_response = requests.post(f"{base_url}/stock-locations", headers=headers, json=loc_payload)
        if loc_response.status_code in [200, 201]:
            new_loc = loc_response.json()
            default_location_id = new_loc.get('id')
            print(f"✅ Localização criada: ID {default_location_id}")
        else:
            print(f"❌ Erro ao criar localização: {loc_response.text}")
            return
    
    # Obter categorias existentes
    print("\n📁 Obtendo categorias...")
    cat_response = requests.get(f"{base_url}/product-categories", headers=headers)
    
    if cat_response.status_code != 200:
        print(f"❌ Erro ao obter categorias: {cat_response.status_code}")
        return
    
    categories = cat_response.json()
    category_map = {}
    
    # Criar categorias necessárias
    unique_categories = list(set(product['category'] for product in products_data))
    
    for cat_name in unique_categories:
        # Procurar categoria existente
        existing = next((c for c in categories if c.get('name', '').lower() == cat_name.lower()), None)
        
        if existing:
            category_map[cat_name] = existing['id']
            print(f"   ✅ {cat_name} (ID: {existing['id']})")
        else:
            # Criar categoria
            cat_payload = {
                "name": cat_name,
                "business_type": "restaurant"
            }
            
            create_cat = requests.post(f"{base_url}/product-categories", headers=headers, json=cat_payload)
            if create_cat.status_code in [200, 201]:
                new_cat = create_cat.json()
                category_map[cat_name] = new_cat['id']
                print(f"   🆕 {cat_name} (ID: {new_cat['id']})")
            else:
                print(f"   ❌ Erro ao criar {cat_name}: {create_cat.text}")
    
    # Importar produtos
    print(f"\n🚀 Importando {len(products_data)} produtos...")
    
    success = 0
    errors = 0
    
    for i, product in enumerate(products_data, 1):
        try:
            payload = {
                "name": product['name'],
                "price": product['price'],
                "cost": product['price'] * 0.7,
                "unit": "un",
                "business_type": "restaurant",
                "track_stock": True,
                "is_active": True,
                "min_stock": max(1, product['stock'] // 4),
                "category_id": category_map.get(product['category']),
                "default_location_id": default_location_id,
                "sku": f"RES-10-{i:03d}"
            }
            
            # Criar produto
            prod_response = requests.post(f"{base_url}/products", headers=headers, json=payload)
            
            if prod_response.status_code in [200, 201]:
                prod_data = prod_response.json()
                prod_id = prod_data.get('id')
                
                # Criar registro de estoque
                stock_payload = {
                    "product_id": prod_id,
                    "location_id": default_location_id,
                    "qty_on_hand": product['stock'],
                    "min_quantity": max(1, product['stock'] // 4)
                }
                
                stock_response = requests.post(f"{base_url}/product-stocks", headers=headers, json=stock_payload)
                
                print(f"✅ {i:3d}. {product['name']} - MZN {product['price']:7.2f}")
                success += 1
                
            else:
                print(f"❌ {i:3d}. {product['name']} - ERRO {prod_response.status_code}")
                errors += 1
                
        except Exception as e:
            print(f"❌ {i:3d}. {product['name']} - ERRO: {e}")
            errors += 1
    
    print(f"\n" + "=" * 60)
    print(f"🎉 IMPORTAÇÃO CONCLUÍDA!")
    print(f"✅ Sucesso: {success} produtos")
    print(f"❌ Erros: {errors} produtos")
    
    if success > 0:
        print(f"\n🌐 Acesse: https://neoerp-production.up.railway.app")
        print(f"📦 Os produtos devem aparecer agora!")
        print(f"🔄 Recarregue a página de produtos no frontend")

if __name__ == "__main__":
    complete_import()
