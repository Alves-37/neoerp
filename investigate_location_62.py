#!/usr/bin/env python3
"""
Investigar localização ID 62 e seus estoques
"""

import requests

def investigate_location_62():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🔍 INVESTIGANDO LOCALIZAÇÃO ID 62")
    print("=" * 50)
    
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
    
    # 1. Verificar estoques na localização 62
    print(f"\n📦 ESTOQUES NA LOCALIZAÇÃO ID 62:")
    stocks_response = requests.get(f"{base_url}/product-stocks", headers=headers, params={
        "location_id": 62,
        "limit": 50
    })
    
    if stocks_response.status_code == 200:
        stocks_data = stocks_response.json()
        if isinstance(stocks_data, dict) and 'data' in stocks_data:
            stocks = stocks_data['data']
        else:
            stocks = stocks_data if isinstance(stocks_data, list) else []
        
        print(f"Total: {len(stocks)} registros de estoque na localização 62")
        
        for i, stock in enumerate(stocks, 1):
            product_id = stock.get('product_id')
            qty = stock.get('qty_on_hand', 0)
            print(f"   {i}. Produto ID: {product_id} | Quantidade: {qty}")
            
            # Tentar obter nome do produto
            try:
                product_response = requests.get(f"{base_url}/products/{product_id}", headers=headers)
                if product_response.status_code == 200:
                    product = product_response.json()
                    print(f"      Nome: {product.get('name', 'Unknown')}")
                    print(f"      Ativo: {product.get('is_active', False)}")
            except:
                print(f"      Não foi possível obter detalhes do produto")
    
    # 2. Verificar estoques na localização 63 (nossos produtos)
    print(f"\n📦 ESTOQUES NA LOCALIZAÇÃO ID 63 (NOSSOS PRODUTOS):")
    stocks_63_response = requests.get(f"{base_url}/product-stocks", headers=headers, params={
        "location_id": 63,
        "limit": 10
    })
    
    if stocks_63_response.status_code == 200:
        stocks_63_data = stocks_63_response.json()
        if isinstance(stocks_63_data, dict) and 'data' in stocks_63_data:
            stocks_63 = stocks_63_data['data']
        else:
            stocks_63 = stocks_63_data if isinstance(stocks_63_data, list) else []
        
        print(f"Total: {len(stocks_63)} registros de estoque na localização 63")
        
        for i, stock in enumerate(stocks_63[:5], 1):  # Mostrar apenas 5 exemplos
            product_id = stock.get('product_id')
            qty = stock.get('qty_on_hand', 0)
            print(f"   {i}. Produto ID: {product_id} | Quantidade: {qty}")
            
            # Tentar obter nome do produto
            try:
                product_response = requests.get(f"{base_url}/products/{product_id}", headers=headers)
                if product_response.status_code == 200:
                    product = product_response.json()
                    print(f"      Nome: {product.get('name', 'Unknown')}")
            except:
                print(f"      Não foi possível obter detalhes do produto")
        
        if len(stocks_63) > 5:
            print(f"   ... e mais {len(stocks_63) - 5} produtos")
    
    # 3. Tentar acessar stock-locations diretamente
    print(f"\n🔍 TENTANDO ACESSAR STOCK-LOCATIONS DIRETAMENTE:")
    try:
        # Tentar sem autenticação primeiro
        locations_response = requests.get(f"{base_url}/stock-locations")
        print(f"Sem autenticação: {locations_response.status_code}")
        
        # Tentar com diferentes headers
        headers_test = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        locations_response_auth = requests.get(f"{base_url}/stock-locations", headers=headers_test)
        print(f"Com autenticação: {locations_response_auth.status_code}")
        
        if locations_response_auth.status_code == 200:
            locations = locations_response_auth.json()
            print(f"✅ Sucesso! {len(locations)} localizações encontradas:")
            
            for loc in locations:
                is_default = loc.get('is_default', False)
                company_id = loc.get('company_id')
                branch_id = loc.get('branch_id')
                marker = "📍 [PADRÃO]" if is_default else ""
                print(f"   ID: {loc['id']} | {loc['name']} | Tipo: {loc.get('type')} | Empresa: {company_id} | Filial: {branch_id} {marker}")
                
                if company_id == 10 and is_default:
                    print(f"      ⚠️  ESTE É O PADRÃO DA EMPRESA 10!")
        else:
            print(f"❌ Falha: {locations_response_auth.text}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # 4. Verificar se há produtos com default_location_id = 62
    print(f"\n📋 PRODUTOS COM DEFAULT_LOCATION_ID = 62:")
    products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 200})
    
    if products_response.status_code == 200:
        products_data = products_response.json()
        if isinstance(products_data, dict) and 'data' in products_data:
            products = products_data['data']
        else:
            products = products_data if isinstance(products_data, list) else []
        
        products_62 = [p for p in products if p.get('default_location_id') == 62]
        products_63 = [p for p in products if p.get('default_location_id') == 63]
        
        print(f"Produtos com default_location_id = 62: {len(products_62)}")
        for p in products_62:
            print(f"   - ID: {p['id']} | {p['name']} | Ativo: {p.get('is_active', False)}")
        
        print(f"\nProdutos com default_location_id = 63: {len(products_63)}")
        for p in products_63[:5]:  # Mostrar apenas 5 exemplos
            print(f"   - ID: {p['id']} | {p['name']}")
        
        if len(products_63) > 5:
            print(f"   ... e mais {len(products_63) - 5} produtos")
    
    print(f"\n" + "=" * 50)
    print("🔍 INVESTIGAÇÃO CONCLUÍDA")

if __name__ == "__main__":
    investigate_location_62()
