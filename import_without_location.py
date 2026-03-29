#!/usr/bin/env python3
"""
Importar produtos sem exigir localização (endpoint específico)
"""

import requests

# Produtos do Mutxutxu mapeados para categorias existentes
products_data = [
    {"name": "2M garrafa", "price": 80.00, "stock": 100, "category": "Bebidas"},
    {"name": "2M lata", "price": 90.00, "stock": 100, "category": "Bebidas"},
    {"name": "Agua Pequena", "price": 50.00, "stock": 100, "category": "Bebidas"},
    {"name": "Agua Tonica", "price": 60.00, "stock": 100, "category": "Bebidas"},
    {"name": "Agua grande", "price": 100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Amarula", "price": 1400.00, "stock": 100, "category": "Bebidas"},
    {"name": "Azinhas", "price": 300.00, "stock": 104, "category": "Bebidas"},
    {"name": "Bife Completo", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "Bull dog", "price": 3300.00, "stock": 100, "category": "Bebidas"},
    {"name": "C double burger", "price": 500.00, "stock": 10, "category": "Pratos"}
]

def import_without_location():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🚀 IMPORTAÇÃO SEM LOCALIZAÇÃO OBRIGATÓRIA")
    print("=" * 60)
    
    # Login
    login = requests.post(f"{base_url}/auth/login", json={
        "email": "mutxutxu@gmail.com", 
        "password": "Mutxutxu@43"
    })
    
    token = login.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login realizado!")
    
    # Obter categorias
    cat_response = requests.get(f"{base_url}/product-categories", headers=headers)
    categories = cat_response.json()
    cat_name_to_id = {cat['name']: cat['id'] for cat in categories}
    
    print(f"📁 Categorias disponíveis: {len(cat_name_to_id)}")
    
    # Importar produtos
    print(f"\n🚀 Importando {len(products_data)} produtos...")
    
    success = 0
    errors = 0
    
    for i, product in enumerate(products_data, 1):
        try:
            # Verificar categoria
            if product['category'] not in cat_name_to_id:
                print(f"❌ {i}. {product['name']} - Categoria não encontrada")
                errors += 1
                continue
            
            # Tentar diferentes payloads
            payloads = [
                # Payload 1: Sem localização
                {
                    "name": product['name'],
                    "price": product['price'],
                    "category_id": cat_name_to_id[product['category']],
                    "business_type": "restaurant",
                    "unit": "un",
                    "is_active": True,
                    "track_stock": True,
                    "sku": f"RES-10-{i:03d}"
                },
                # Payload 2: Com default_location_id nulo
                {
                    "name": product['name'],
                    "price": product['price'],
                    "category_id": cat_name_to_id[product['category']],
                    "default_location_id": None,
                    "business_type": "restaurant",
                    "unit": "un",
                    "is_active": True,
                    "track_stock": True,
                    "sku": f"RES-10-{i:03d}"
                },
                # Payload 3: Mínimo possível
                {
                    "name": product['name'],
                    "price": product['price'],
                    "category_id": cat_name_to_id[product['category']],
                    "is_active": True
                }
            ]
            
            created = False
            for j, payload in enumerate(payloads, 1):
                try:
                    prod_response = requests.post(f"{base_url}/products", headers=headers, json=payload)
                    
                    if prod_response.status_code in [200, 201]:
                        prod_data = prod_response.json()
                        print(f"✅ {i}. {product['name']} - MZN {product['price']:7.2f} (Payload {j})")
                        success += 1
                        created = True
                        break
                    else:
                        print(f"⚠️  {i}. {product['name']} - Payload {j} falhou: {prod_response.status_code}")
                        if prod_response.status_code == 422:
                            print(f"     📄 {prod_response.text}")
                
                except Exception as e:
                    print(f"❌ {i}. {product['name']} - Payload {j} erro: {e}")
                    continue
            
            if not created:
                print(f"❌ {i}. {product['name']} - TODOS OS PAYLOADS FALHARAM")
                errors += 1
                
        except Exception as e:
            print(f"❌ {i}. {product['name']} - ERRO GERAL: {e}")
            errors += 1
    
    print(f"\n" + "=" * 60)
    print(f"🎉 IMPORTAÇÃO CONCLUÍDA!")
    print(f"✅ Sucesso: {success} produtos")
    print(f"❌ Erros: {errors} produtos")
    
    if success > 0:
        print(f"\n🌐 Acesse: https://neoerp-production.up.railway.app")
        print(f"📦 Os produtos devem aparecer agora!")
        print(f"🔄 Recarregue a página de produtos")
        
        # Verificar produtos criados
        print(f"\n🔍 Verificando produtos criados...")
        check_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 20})
        if check_response.status_code == 200:
            products_check = check_response.json()
            if isinstance(products_check, dict) and 'data' in products_check:
                current_products = products_check['data']
            else:
                current_products = products_check if isinstance(products_check, list) else []
            
            print(f"📦 Total de produtos no sistema: {len(current_products)}")
            for prod in current_products[-5:]:  # Últimos 5 produtos
                cat_name = next((c['name'] for c in categories if c['id'] == prod.get('category_id')), 'Unknown')
                print(f"   - {prod.get('name')} | MZN {prod.get('price', 0):.2f} | {cat_name}")

if __name__ == "__main__":
    import_without_location()
