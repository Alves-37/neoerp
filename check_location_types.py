#!/usr/bin/env python3
"""
Verificar tipos de localizações para encontrar a "Loja Principal"
"""

import requests

def check_location_types():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🔍 VERIFICANDO TIPOS DE LOCALIZAÇÕES")
    print("=" * 50)
    
    # Login
    try:
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
        
        # 1. Tentar acessar stock-locations
        print(f"\n📦 TENTANDO ACESSAR STOCK-LOCATIONS:")
        
        # Tentar diferentes abordagens
        endpoints_to_try = [
            f"{base_url}/stock-locations",
            f"{base_url}/api/stock-locations", 
            f"{base_url}/v1/stock-locations",
            f"{base_url}/locations"
        ]
        
        locations_data = None
        
        for endpoint in endpoints_to_try:
            try:
                print(f"   Tentando: {endpoint}")
                response = requests.get(endpoint, headers=headers)
                
                if response.status_code == 200:
                    locations_data = response.json()
                    print(f"   ✅ SUCESSO! Endpoint: {endpoint}")
                    break
                else:
                    print(f"   ❌ Status: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Erro: {e}")
        
        if locations_data:
            print(f"\n📋 LOCALIZAÇÕES ENCONTRADAS:")
            
            if isinstance(locations_data, list):
                locations = locations_data
            elif isinstance(locations_data, dict) and 'data' in locations_data:
                locations = locations_data['data']
            else:
                locations = []
            
            store_locations = []
            warehouse_locations = []
            default_location = None
            
            for loc in locations:
                loc_type = loc.get('type', 'unknown')
                loc_name = loc.get('name', 'Sem nome')
                loc_id = loc['id']
                is_default = loc.get('is_default', False)
                company_id = loc.get('company_id')
                
                marker = "📍 [PADRÃO]" if is_default else ""
                
                print(f"   ID: {loc_id} | {loc_name} | Tipo: {loc_type} | Empresa: {company_id} {marker}")
                
                if is_default and company_id == 10:
                    default_location = loc
                
                if loc_type == 'store':
                    store_locations.append(loc)
                elif loc_type == 'warehouse':
                    warehouse_locations.append(loc)
            
            print(f"\n🏪 LOJAS (Tipo: store):")
            for store in store_locations:
                is_default = "📍 [PADRÃO]" if store.get('is_default') else ""
                print(f"   ID: {store['id']} | {store['name']} {is_default}")
            
            print(f"\n📦 ARMAZÉNS (Tipo: warehouse):")
            for warehouse in warehouse_locations:
                is_default = "📍 [PADRÃO]" if warehouse.get('is_default') else ""
                print(f"   ID: {warehouse['id']} | {warehouse['name']} {is_default}")
            
            if default_location:
                print(f"\n✅ LOCALIZAÇÃO PADRÃO DA EMPRESA 10:")
                print(f"   ID: {default_location['id']} | {default_location['name']} | Tipo: {default_location.get('type')}")
                
                if default_location.get('type') != 'store':
                    print(f"   ⚠️  PROBLEMA: A localização padrão não é uma 'loja'!")
            else:
                print(f"\n❌ Nenhuma localização padrão encontrada para empresa 10")
        
        # 2. Verificar produtos e suas localizações atuais
        print(f"\n📋 VERIFICANDO LOCALIZAÇÕES ATUAIS DOS PRODUTOS:")
        products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 10})
        
        if products_response.status_code == 200:
            products_data = products_response.json()
            if isinstance(products_data, dict) and 'data' in products_data:
                products = products_data['data']
            else:
                products = products_data if isinstance(products_data, list) else []
            
            print(f"   Amostra de produtos e suas localizações:")
            for product in products[:5]:
                loc_id = product.get('default_location_id')
                print(f"   - {product['name']} | Localização: {loc_id}")
        
        # 3. Tentar criar uma localização do tipo "store" se não existir
        if locations_data and store_locations:
            print(f"\n✅ JÁ EXISTEM LOJAS DISPONÍVEIS")
            print(f"   Podemos mover os produtos para uma loja existente")
        else:
            print(f"\n🔧 PRECISAMOS CRIAR UMA LOJA")
            print(f"   Não há localizações do tipo 'store' disponíveis")
        
        print(f"\n" + "=" * 50)
        print("🌐 Acesse: https://neoerp-production.up.railway.app")
        
    except Exception as e:
        print(f"❌ Erro durante verificação: {e}")

if __name__ == "__main__":
    check_location_types()
