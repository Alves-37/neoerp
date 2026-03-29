#!/usr/bin/env python3
"""
Script corrigido para importar produtos para produção
"""

import requests
import json

# Dados dos produtos (primeiros 10 para teste)
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
    {"name": "C double burger", "price": 500.00, "stock": 10, "category": "Bolos e salgados"}
]

def import_to_production_fixed():
    """
    Importa produtos para produção com endpoints corrigidos
    """
    print("🚀 IMPORTANDO PRODUTOS PARA PRODUÇÃO (VERSÃO CORRIGIDA)")
    print("=" * 60)
    
    base_url = "https://neoerp-production.up.railway.app"
    
    # Credenciais
    credentials = {
        "email": "mutxutxu@gmail.com",
        "password": "Mutxutxu@43"
    }
    
    try:
        # 1. Obter token
        print("🔑 Fazendo login...")
        login_response = requests.post(f"{base_url}/auth/login", json=credentials)
        
        if login_response.status_code != 200:
            print(f"❌ Falha no login: {login_response.status_code}")
            print(f"📄 Resposta: {login_response.text}")
            return
        
        login_data = login_response.json()
        token = login_data.get('access_token') or login_data.get('token')
        
        if not token:
            print("❌ Token não encontrado")
            return
        
        print(f"✅ Login realizado com sucesso!")
        
        # Headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 2. Testar endpoints disponíveis
        print("\n🔍 Testando endpoints...")
        
        endpoints_to_test = [
            "/me",
            "/auth/me", 
            "/users/me",
            "/api/me"
        ]
        
        user_info = None
        for endpoint in endpoints_to_test:
            try:
                test_response = requests.get(f"{base_url}{endpoint}", headers=headers)
                if test_response.status_code == 200:
                    user_info = test_response.json()
                    print(f"✅ Endpoint funcionando: {endpoint}")
                    break
            except:
                continue
        
        if user_info:
            print(f"👤 Usuário: {user_info.get('email', 'Unknown')}")
        else:
            print("⚠️  Não foi possível obter informações do usuário, mas continuando...")
        
        # 3. Verificar categorias
        print("\n📁 Verificando categorias...")
        
        category_endpoints = [
            "/product-categories",
            "/categories",
            "/api/product-categories",
            "/api/categories"
        ]
        
        categories = []
        for endpoint in category_endpoints:
            try:
                cat_response = requests.get(f"{base_url}{endpoint}", headers=headers)
                if cat_response.status_code == 200:
                    categories = cat_response.json()
                    print(f"✅ Categorias encontradas via: {endpoint}")
                    break
            except:
                continue
        
        if not categories:
            print("❌ Não foi possível obter categorias")
            return
        
        print(f"📁 {len(categories)} categorias encontradas")
        
        # Mapear categorias
        category_map = {}
        unique_categories = list(set(product['category'] for product in products_data))
        
        for cat_name in unique_categories:
            # Procurar categoria existente (case insensitive)
            existing_cat = next((c for c in categories if c.get('name', '').lower() == cat_name.lower()), None)
            
            if existing_cat:
                category_map[cat_name] = existing_cat['id']
                print(f"   ✅ {cat_name} -> ID: {existing_cat['id']}")
            else:
                print(f"   ⚠️  Categoria não encontrada: {cat_name}")
        
        # 4. Verificar produtos existentes
        print("\n📦 Verificando produtos existentes...")
        
        product_endpoints = [
            "/products",
            "/api/products"
        ]
        
        for endpoint in product_endpoints:
            try:
                prod_response = requests.get(f"{base_url}{endpoint}", headers=headers, params={"limit": 1})
                if prod_response.status_code == 200:
                    products_data_existing = prod_response.json()
                    total_count = products_data_existing.get('total', 0) if isinstance(products_data_existing, dict) else len(products_data_existing)
                    print(f"✅ Produtos existentes: {total_count}")
                    break
            except:
                continue
        
        # 5. Importar produtos
        print(f"\n🚀 Importando {len(products_data)} produtos (teste)...")
        
        success_count = 0
        error_count = 0
        
        for i, product in enumerate(products_data, 1):
            try:
                # Preparar payload
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
                    "sku": f"RES-10-{i:03d}"
                }
                
                # Tentar criar produto
                create_endpoints = [
                    "/products",
                    "/api/products"
                ]
                
                created = False
                for endpoint in create_endpoints:
                    try:
                        create_response = requests.post(f"{base_url}{endpoint}", headers=headers, json=payload)
                        
                        if create_response.status_code == 201:
                            product_data = create_response.json()
                            product_id = product_data.get('id')
                            
                            print(f"✅ {i:3d}. {product['name']} - MZN {product['price']:7.2f} (ID: {product_id})")
                            success_count += 1
                            created = True
                            break
                        elif create_response.status_code == 422:
                            print(f"⚠️  {i:3d}. {product['name']} - VALIDATION ERROR")
                            print(f"     📄 {create_response.text}")
                            break
                            
                    except Exception as e:
                        continue
                
                if not created:
                    print(f"❌ {i:3d}. {product['name']} - FALHA AO CRIAR")
                    error_count += 1
                
            except Exception as e:
                print(f"❌ {i:3d}. {product['name']} - ERRO: {e}")
                error_count += 1
        
        print(f"\n" + "=" * 60)
        print(f"🎉 TESTE CONCLUÍDO!")
        print(f"✅ Sucesso: {success_count} produtos")
        print(f"❌ Erros: {error_count} produtos")
        
        if success_count > 0:
            print(f"\n🌐 Funcionou! Acesse: {base_url}")
            print(f"📦 Os produtos devem aparecer no frontend!")
            print(f"🔄 Recarregue a página de produtos")
        else:
            print(f"\n❌ Nenhum produto foi criado. Verifique os endpoints e permissões.")
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    import_to_production_fixed()
