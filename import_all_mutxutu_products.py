#!/usr/bin/env python3
"""
Importação completa dos 102 produtos do Mutxutxu para produção
"""

import requests

# Dados completos dos produtos do Mutxutxu
MUTXUTXU_PRODUCTS = [
    {"name": "2M garrafa", "price": 80.00, "stock": 100, "category": "Bebidas"},
    {"name": "2M lata", "price": 90.00, "stock": 100, "category": "Bebidas"},
    {"name": "Agua Pequena", "price": 50.00, "stock": 100, "category": "Bebidas"},
    {"name": "Agua Tonica", "price": 60.00, "stock": 100, "category": "Bebidas"},
    {"name": "Agua grande", "price": 100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Amarula", "price": 1400.00, "stock": 100, "category": "Bebidas"},
    {"name": "Azinhas", "price": 300.00, "stock": 104, "category": "Bebidas"},
    {"name": "Bife Completo", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "Bull dog", "price": 3300.00, "stock": 100, "category": "Bebidas"},
    {"name": "C double burger", "price": 500.00, "stock": 10, "category": "Pratos"},
    {"name": "Cabeca de Peixe", "price": 200.00, "stock": 10, "category": "Pratos"},
    {"name": "Cabeca de Vaca", "price": 200.00, "stock": 10, "category": "Pratos"},
    {"name": "Caldo verde", "price": 150.00, "stock": 10, "category": "Pratos"},
    {"name": "Cappy", "price": 80.00, "stock": 100, "category": "Bebidas"},
    {"name": "Carne de porco", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "Ceres", "price": 200.00, "stock": 100, "category": "Bebidas"},
    {"name": "Champanhe Anabela", "price": 1300.00, "stock": 100, "category": "Bebidas"},
    {"name": "Champanhe JS", "price": 1200.00, "stock": 100, "category": "Bebidas"},
    {"name": "Champanhe Martini Rose", "price": 1200.00, "stock": 100, "category": "Bebidas"},
    {"name": "Champanhe Toste", "price": 1500.00, "stock": 100, "category": "Bebidas"},
    {"name": "Chamussas", "price": 25.00, "stock": 10, "category": "Pratos"},
    {"name": "Chourico", "price": 300.00, "stock": 10, "category": "Pratos"},
    {"name": "Cochinhas", "price": 30.00, "stock": 9, "category": "Pratos"},
    {"name": "Compal", "price": 200.00, "stock": 100, "category": "Bebidas"},
    {"name": "Dobrada", "price": 200.00, "stock": 10, "category": "Pratos"},
    {"name": "Dry Lemon", "price": 150.00, "stock": 100, "category": "Bebidas"},
    {"name": "Escape Vodka", "price": 1000.00, "stock": 100, "category": "Bebidas"},
    {"name": "Four Causin Grade", "price": 1600.00, "stock": 100, "category": "Bebidas"},
    {"name": "Frango 1 quarto", "price": 300.00, "stock": 10, "category": "Pratos"},
    {"name": "Frango a Passarinho", "price": 1250.00, "stock": 10, "category": "Pratos"},
    {"name": "Frango assado 1", "price": 1200.00, "stock": 10, "category": "Pratos"},
    {"name": "Frango assado meio", "price": 600.00, "stock": 10, "category": "Pratos"},
    {"name": "Galinha Fumado", "price": 1500.00, "stock": 10, "category": "Pratos"},
    {"name": "Galo Dourado", "price": 1100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Gatao", "price": 1500.00, "stock": 100, "category": "Bebidas"},
    {"name": "Gordon", "price": 1100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Grants", "price": 1800.00, "stock": 100, "category": "Bebidas"},
    {"name": "HENICKER", "price": 100.00, "stock": 500, "category": "Bebidas"},
    {"name": "Hamburger Completo", "price": 300.00, "stock": 8, "category": "Pratos"},
    {"name": "Hanked Bannister", "price": 1100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Havelock", "price": 1100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Humburger S", "price": 250.00, "stock": 10, "category": "Pratos"},
    {"name": "Joh walker red", "price": 1800.00, "stock": 100, "category": "Bebidas"},
    {"name": "John Walker black", "price": 3500.00, "stock": 100, "category": "Bebidas"},
    {"name": "Maicgregor", "price": 1500.00, "stock": 100, "category": "Bebidas"},
    {"name": "Martine", "price": 1400.00, "stock": 100, "category": "Bebidas"},
    {"name": "Mutxutxu de galinha", "price": 200.00, "stock": 110, "category": "Pratos"},
    {"name": "Pizza 4 estacoes", "price": 100.00, "stock": 10, "category": "Pratos"},
    {"name": "Pizza de atum", "price": 700.00, "stock": 10, "category": "Pratos"},
    {"name": "Pizza de frango", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "Pizza vegetariana", "price": 700.00, "stock": 10, "category": "Pratos"},
    {"name": "Quinta da bolota", "price": 1200.00, "stock": 100, "category": "Bebidas"},
    {"name": "Red Bull", "price": 150.00, "stock": 100, "category": "Bebidas"},
    {"name": "Refresco em lata", "price": 60.00, "stock": 97, "category": "Bebidas"},
    {"name": "Rose Grande", "price": 1600.00, "stock": 100, "category": "Bebidas"},
    {"name": "Rusian", "price": 1000.00, "stock": 100, "category": "Bebidas"},
    {"name": "Silk spice", "price": 1800.00, "stock": 100, "category": "Bebidas"},
    {"name": "Sopa de Feijao", "price": 150.00, "stock": 10, "category": "Pratos"},
    {"name": "Sopa de legumes", "price": 150.00, "stock": 10, "category": "Pratos"},
    {"name": "Takeaway", "price": 30.00, "stock": 100, "category": "Pratos"},
    {"name": "Tbone", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "Tostas com batata frita", "price": 300.00, "stock": 10, "category": "Pratos"},
    {"name": "Worce", "price": 300.00, "stock": 10, "category": "Pratos"},
    {"name": "altum", "price": 800.00, "stock": 10, "category": "Bebidas"},
    {"name": "bermine", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "bife trinchado", "price": 700.00, "stock": 101, "category": "Pratos"},
    {"name": "brizer", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "brutal", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "budweiser", "price": 100.00, "stock": 10, "category": "Bebidas"},
    {"name": "cape ruby", "price": 1100.00, "stock": 10, "category": "Bebidas"},
    {"name": "casal garcia", "price": 1200.00, "stock": 10, "category": "Bebidas"},
    {"name": "castle lite", "price": 100.00, "stock": 10, "category": "Bebidas"},
    {"name": "celler cast", "price": 1100.00, "stock": 100, "category": "Bebidas"},
    {"name": "chima", "price": 100.00, "stock": 10, "category": "Sobremesas"},
    {"name": "dose de arroz", "price": 100.00, "stock": 10, "category": "Pratos"},
    {"name": "dose de batata", "price": 100.00, "stock": 10, "category": "Pratos"},
    {"name": "drosdy hof", "price": 800.00, "stock": 10, "category": "Bebidas"},
    {"name": "duas quintas", "price": 1100.00, "stock": 10, "category": "Bebidas"},
    {"name": "filetes", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "gazela", "price": 1100.00, "stock": 10, "category": "Bebidas"},
    {"name": "hunters dray", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "hunters gold", "price": 100.00, "stock": 10, "category": "Bebidas"},
    {"name": "jamson", "price": 1500.00, "stock": 100, "category": "Bebidas"},
    {"name": "lemone", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "lulas", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "mao de vaca", "price": 200.00, "stock": 9, "category": "Pratos"},
    {"name": "pandora", "price": 1100.00, "stock": 10, "category": "Bebidas"},
    {"name": "peixe chambo grande", "price": 1000.00, "stock": 10, "category": "Pratos"},
    {"name": "peixe chambo medio", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "peixe chambo pequeno", "price": 600.00, "stock": 10, "category": "Pratos"},
    {"name": "prego no pao", "price": 300.00, "stock": 10, "category": "Pratos"},
    {"name": "prego no prato", "price": 450.00, "stock": 10, "category": "Pratos"},
    {"name": "preta grande", "price": 80.00, "stock": 10, "category": "Bebidas"},
    {"name": "preta lata", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "preta pequena", "price": 100.00, "stock": 10, "category": "Bebidas"},
    {"name": "saladas", "price": 75.00, "stock": 10, "category": "Sobremesas"},
    {"name": "sande de ovo", "price": 200.00, "stock": 10, "category": "Pratos"},
    {"name": "segredo sao miguel", "price": 1200.00, "stock": 10, "category": "Bebidas"},
    {"name": "spin", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "super bock", "price": 80.00, "stock": 10, "category": "Bebidas"},
    {"name": "vinho cabriz", "price": 1200.00, "stock": 10, "category": "Bebidas"},
    {"name": "vinho portada", "price": 1200.00, "stock": 10, "category": "Bebidas"}
]

def import_all_products():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🍽️ IMPORTAÇÃO COMPLETA - RESTAURANTE MUTXUTXU")
    print("=" * 60)
    
    # Login
    login = requests.post(f"{base_url}/auth/login", json={
        "email": "mutxutxu@gmail.com", 
        "password": "Mutxutxu@43"
    })
    
    if login.status_code != 200:
        print(f"❌ Login falhou: {login.status_code}")
        return
    
    token = login.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login realizado!")
    
    # Obter informações da empresa e filial
    companies_response = requests.get(f"{base_url}/companies", headers=headers)
    company = companies_response.json()[0]  # Só existe a empresa 10
    
    branches_response = requests.get(f"{base_url}/branches", headers=headers, params={"company_id": 10})
    branch = branches_response.json()[0]  # Só existe a filial 94
    
    establishments_response = requests.get(f"{base_url}/establishments", headers=headers, params={
        "company_id": 10,
        "branch_id": branch['id']
    })
    establishments = establishments_response.json()
    establishment = next((e for e in establishments if e.get('is_default')), establishments[0])
    
    print(f"🏢 Empresa: {company['name']} (ID: {company['id']})")
    print(f"🏪 Filial: {branch['name']} (ID: {branch['id']})")
    print(f"🏢 Estabelecimento: {establishment['name']} (ID: {establishment['id']})")
    
    # Obter categorias
    categories_response = requests.get(f"{base_url}/product-categories", headers=headers)
    categories = categories_response.json()
    category_map = {cat['name']: cat['id'] for cat in categories}
    
    print(f"\n📁 Categorias: {len(category_map)} disponíveis")
    
    # Verificar produtos existentes
    products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 1})
    if products_response.status_code == 200:
        products_data = products_response.json()
        existing_count = products_data.get('total', 0) if isinstance(products_data, dict) else len(products_data)
        print(f"\n📦 Produtos existentes: {existing_count}")
    
    # Importar produtos
    print(f"\n🚀 Importando {len(MUTXUTXU_PRODUCTS)} produtos...")
    
    success = 0
    errors = 0
    skipped = 0
    
    for i, product in enumerate(MUTXUTXU_PRODUCTS, 1):
        try:
            # Verificar se categoria existe
            if product['category'] not in category_map:
                print(f"❌ {i:3d}. {product['name']} - Categoria não encontrada: {product['category']}")
                errors += 1
                continue
            
            # Verificar se produto já existe
            existing_response = requests.get(
                f"{base_url}/products", 
                headers=headers, 
                params={"q": product['name'], "limit": 1}
            )
            
            if existing_response.status_code == 200:
                existing_data = existing_response.json()
                if isinstance(existing_data, dict) and existing_data.get('data'):
                    if existing_data['data']:
                        print(f"⚠️  {i:3d}. {product['name']} - JÁ EXISTE")
                        skipped += 1
                        continue
            
            # Criar produto
            payload = {
                "name": product['name'],
                "price": product['price'],
                "cost": product['price'] * 0.7,
                "category_id": category_map[product['category']],
                "default_location_id": establishment['id'],
                "business_type": "restaurant",
                "unit": "un",
                "is_active": True,
                "track_stock": True,
                "min_stock": max(1, product['stock'] // 4),
                "sku": f"RES-10-{i:03d}"
            }
            
            response = requests.post(f"{base_url}/products", headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                prod_data = response.json()
                print(f"✅ {i:3d}. {product['name']} - MZN {product['price']:7.2f} | {product['category']} (ID: {prod_data.get('id')})")
                success += 1
            else:
                print(f"❌ {i:3d}. {product['name']} - ERRO {response.status_code}")
                if response.status_code == 422:
                    print(f"     📄 {response.text}")
                errors += 1
                
        except Exception as e:
            print(f"❌ {i:3d}. {product['name']} - ERRO: {e}")
            errors += 1
    
    print(f"\n" + "=" * 60)
    print(f"🎉 IMPORTAÇÃO CONCLUÍDA!")
    print(f"✅ Sucesso: {success} produtos")
    print(f"⚠️  Pulados: {skipped} produtos")
    print(f"❌ Erros: {errors} produtos")
    print(f"📊 Total processado: {success + skipped + errors} produtos")
    
    if success > 0:
        print(f"\n🌐 Acesse: {base_url}")
        print(f"📦 Os produtos do Mutxutxu estão disponíveis!")
        print(f"🔄 Recarregue a página de produtos no frontend")
        
        # Verificação final
        print(f"\n🔍 VERIFICAÇÃO FINAL:")
        final_check = requests.get(f"{base_url}/products", headers=headers, params={"limit": 20})
        if final_check.status_code == 200:
            final_data = final_check.json()
            if isinstance(final_data, dict) and 'data' in final_data:
                total_products = final_data.get('total', 0)
                print(f"📦 Total de produtos no sistema: {total_products}")

if __name__ == "__main__":
    import_all_products()
