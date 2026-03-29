#!/usr/bin/env python3
"""
Verificar estrutura do banco de produção e criar importação via API
"""

import requests

def check_production_structure():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🔍 VERIFICANDO ESTRUTURA DO BANCO DE PRODUÇÃO")
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
    
    # Verificar empresas
    print("\n🏢 VERIFICANDO EMPRESAS:")
    companies_response = requests.get(f"{base_url}/companies", headers=headers)
    
    if companies_response.status_code == 200:
        companies = companies_response.json()
        print(f"Total: {len(companies)} empresas")
        
        mutxutxu = None
        for company in companies:
            print(f"   ID: {company['id']} | {company['name']}")
            if company['id'] == 10:
                mutxutxu = company
        
        if mutxutxu:
            print(f"\n✅ Mutxutxu encontrada: {mutxutxu['name']}")
        else:
            print(f"\n❌ Empresa ID 10 não encontrada!")
            return
    else:
        print(f"❌ Erro ao buscar empresas: {companies_response.status_code}")
        return
    
    # Verificar filiais
    print(f"\n🏪 VERIFICANDO FILIAIS DA EMPRESA 10:")
    branches_response = requests.get(f"{base_url}/branches", headers=headers, params={"company_id": 10})
    
    if branches_response.status_code == 200:
        branches = branches_response.json()
        print(f"Total: {len(branches)} filiais")
        
        restaurant_branch = None
        for branch in branches:
            print(f"   ID: {branch['id']} | {branch['name']} | Tipo: {branch['business_type']}")
            if branch['business_type'] == 'restaurant':
                restaurant_branch = branch
        
        if restaurant_branch:
            print(f"\n✅ Filial restaurante encontrada: {restaurant_branch['name']} (ID: {restaurant_branch['id']})")
        else:
            print(f"\n❌ Filial restaurante não encontrada!")
            return
    else:
        print(f"❌ Erro ao buscar filiais: {branches_response.status_code}")
        return
    
    # Verificar estabelecimentos
    print(f"\n🏢 VERIFICANDO ESTABELECIMENTOS:")
    establishments_response = requests.get(f"{base_url}/establishments", headers=headers, params={
        "company_id": 10,
        "branch_id": restaurant_branch['id']
    })
    
    if establishments_response.status_code == 200:
        establishments = establishments_response.json()
        print(f"Total: {len(establishments)} estabelecimentos")
        
        default_establishment = None
        for est in establishments:
            print(f"   ID: {est['id']} | {est['name']} | Default: {est.get('is_default', False)}")
            if est.get('is_default'):
                default_establishment = est
        
        if default_establishment:
            print(f"\n✅ Estabelecimento padrão: {default_establishment['name']} (ID: {default_establishment['id']})")
        else:
            default_establishment = establishments[0] if establishments else None
            if default_establishment:
                print(f"\n⚠️  Usando primeiro estabelecimento: {default_establishment['name']} (ID: {default_establishment['id']})")
    else:
        print(f"❌ Erro ao buscar estabelecimentos: {establishments_response.status_code}")
        default_establishment = None
    
    # Verificar localizações de estoque
    print(f"\n📍 VERIFICANDO LOCALIZAÇÕES:")
    try:
        locations_response = requests.get(f"{base_url}/stock-locations", headers=headers)
        
        if locations_response.status_code == 200:
            locations = locations_response.json()
            print(f"Total: {len(locations)} localizações")
            
            for loc in locations:
                print(f"   ID: {loc['id']} | {loc['name']} | Tipo: {loc['type']} | Default: {loc.get('is_default', False)}")
        else:
            print(f"⚠️  Endpoint stock-locations: {locations_response.status_code}")
            
            # Tentar establishments como localizações
            if default_establishment:
                print(f"\n📍 USANDO ESTABELECIMENTO COMO LOCALIZAÇÃO:")
                print(f"   ID: {default_establishment['id']} | {default_establishment['name']}")
                
    except Exception as e:
        print(f"❌ Erro ao verificar localizações: {e}")
        if default_establishment:
            print(f"📍 USANDO ESTABELECIMENTO COMO LOCALIZAÇÃO: ID {default_establishment['id']}")
    
    print(f"\n🎯 ESTRUTURA IDENTIFICADA!")
    print(f"🏢 Empresa: Mutxutxu (ID: 10)")
    print(f"🏪 Filial: {restaurant_branch['name']} (ID: {restaurant_branch['id']})")
    print(f"🏢 Estabelecimento: {default_establishment['name'] if default_establishment else 'N/A'} (ID: {default_establishment['id'] if default_establishment else 'N/A'})")
    
    # Agora criar importação correta
    create_production_import(base_url, headers, restaurant_branch, default_establishment)

def create_production_import(base_url, headers, branch, establishment):
    print(f"\n🚀 CRIANDO IMPORTAÇÃO PARA PRODUÇÃO")
    print("=" * 60)
    
    # Obter categorias
    categories_response = requests.get(f"{base_url}/product-categories", headers=headers)
    if categories_response.status_code != 200:
        print(f"❌ Erro ao buscar categorias: {categories_response.status_code}")
        return
    
    categories = categories_response.json()
    category_map = {cat['name']: cat['id'] for cat in categories}
    
    print(f"📁 Categorias disponíveis: {len(category_map)}")
    for name, id in category_map.items():
        print(f"   {name} (ID: {id})")
    
    # Produtos de teste
    test_products = [
        {"name": "2M garrafa", "price": 80, "category": "Bebidas"},
        {"name": "Red Bull", "price": 150, "category": "Bebidas"},
        {"name": "Pizza", "price": 100, "category": "Pratos"},
        {"name": "Hamburguer", "price": 300, "category": "Pratos"},
        {"name": "Sobremesa", "price": 75, "category": "Sobremesas"}
    ]
    
    print(f"\n🚀 Importando {len(test_products)} produtos de teste...")
    
    success = 0
    errors = 0
    
    for i, product in enumerate(test_products, 1):
        try:
            if product['category'] not in category_map:
                print(f"❌ {i}. {product['name']} - Categoria não encontrada: {product['category']}")
                errors += 1
                continue
            
            # Payload completo seguindo o padrão do sistema
            payload = {
                "name": product['name'],
                "price": product['price'],
                "cost": product['price'] * 0.7,
                "category_id": category_map[product['category']],
                "business_type": "restaurant",
                "unit": "un",
                "is_active": True,
                "track_stock": True,
                "min_stock": 5,
                "sku": f"RES-10-{i:03d}"
            }
            
            # Tentar diferentes abordagens para localização
            payloads_to_try = [
                {**payload, "default_location_id": establishment['id']} if establishment else payload,
                {**payload, "establishment_id": establishment['id']} if establishment else payload,
                payload  # Sem localização
            ]
            
            created = False
            for j, test_payload in enumerate(payloads_to_try, 1):
                try:
                    response = requests.post(f"{base_url}/products", headers=headers, json=test_payload)
                    
                    if response.status_code in [200, 201]:
                        prod_data = response.json()
                        print(f"✅ {i}. {product['name']} - MZN {product['price']} (Payload {j}, ID: {prod_data.get('id')})")
                        success += 1
                        created = True
                        break
                    else:
                        print(f"⚠️  {i}. {product['name']} - Payload {j} falhou: {response.status_code}")
                        if response.status_code == 422:
                            print(f"     📄 {response.text}")
                
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
    print(f"🎉 TESTE CONCLUÍDO!")
    print(f"✅ Sucesso: {success} produtos")
    print(f"❌ Erros: {errors} produtos")
    
    if success > 0:
        print(f"\n🌐 FUNCIONOU! Acesse: {base_url}")
        print(f"📦 Os produtos devem aparecer agora!")
        print(f"🔄 Recarregue a página de produtos")
        
        # Listar produtos criados
        print(f"\n📦 VERIFICANDO PRODUTOS CRIADOS:")
        products_check = requests.get(f"{base_url}/products", headers=headers, params={"limit": 10})
        if products_check.status_code == 200:
            products_data = products_check.json()
            if isinstance(products_data, dict) and 'data' in products_data:
                products_list = products_data['data']
            else:
                products_list = products_data if isinstance(products_data, list) else []
            
            print(f"Total de produtos: {len(products_list)}")
            for prod in products_list[-5:]:  # Últimos 5
                cat_name = next((c['name'] for c in categories if c['id'] == prod.get('category_id')), 'Unknown')
                print(f"   - {prod.get('name')} | MZN {prod.get('price', 0):.2f} | {cat_name}")

if __name__ == "__main__":
    check_production_structure()
