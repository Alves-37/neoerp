#!/usr/bin/env python3
"""
Verificar locais padrões duplicados no sistema
"""

import requests

def check_duplicate_locations():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🔍 VERIFICANDO LOCAIS PADRÕES DUPLICADOS")
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
    
    # 1. Verificar estabelecimentos
    print(f"\n🏢 ESTABELECIMENTOS:")
    establishments_response = requests.get(f"{base_url}/establishments", headers=headers, params={
        "company_id": 10,
        "branch_id": 94
    })
    
    if establishments_response.status_code == 200:
        establishments = establishments_response.json()
        print(f"Total: {len(establishments)} estabelecimentos")
        
        default_establishments = []
        for est in establishments:
            is_default = est.get('is_default', False)
            print(f"   ID: {est['id']} | {est['name']} | Default: {is_default} | Ativo: {est.get('is_active', False)}")
            if is_default:
                default_establishments.append(est)
        
        if len(default_establishments) > 1:
            print(f"\n⚠️  PROBLEMA: {len(default_establishments)} estabelecimentos marcados como padrão!")
            for est in default_establishments:
                print(f"   - ID: {est['id']} | {est['name']}")
        elif len(default_establishments) == 1:
            print(f"\n✅ Apenas 1 estabelecimento padrão: {default_establishments[0]['name']} (ID: {default_establishments[0]['id']})")
        else:
            print(f"\n❌ Nenhum estabelecimento padrão encontrado!")
    
    # 2. Tentar verificar stock-locations
    print(f"\n📦 LOCALIZAÇÕES DE ESTOQUE:")
    try:
        locations_response = requests.get(f"{base_url}/stock-locations", headers=headers)
        
        if locations_response.status_code == 200:
            locations = locations_response.json()
            print(f"Total: {len(locations)} localizações")
            
            default_locations = []
            for loc in locations:
                is_default = loc.get('is_default', False)
                company_id = loc.get('company_id')
                branch_id = loc.get('branch_id')
                print(f"   ID: {loc['id']} | {loc['name']} | Tipo: {loc.get('type')} | Default: {is_default} | Empresa: {company_id} | Filial: {branch_id}")
                if is_default and company_id == 10:
                    default_locations.append(loc)
            
            if len(default_locations) > 1:
                print(f"\n⚠️  PROBLEMA: {len(default_locations)} localizações padrão para a empresa 10!")
                for loc in default_locations:
                    print(f"   - ID: {loc['id']} | {loc['name']} | Tipo: {loc.get('type')} | Filial: {loc.get('branch_id')}")
            elif len(default_locations) == 1:
                print(f"\n✅ Apenas 1 localização padrão para empresa 10: {default_locations[0]['name']} (ID: {default_locations[0]['id']})")
            else:
                print(f"\n❌ Nenhuma localização padrão encontrada para empresa 10!")
        else:
            print(f"⚠️  Endpoint stock-locations retornou: {locations_response.status_code}")
            print(f"📄 Resposta: {locations_response.text}")
            
    except Exception as e:
        print(f"❌ Erro ao verificar localizações: {e}")
    
    # 3. Verificar produtos e seus default_location_id
    print(f"\n📋 VERIFICANDO PRODUTOS E SEUS LOCAIS PADRÃO:")
    products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 50})
    
    if products_response.status_code == 200:
        products_data = products_response.json()
        if isinstance(products_data, dict) and 'data' in products_data:
            products = products_data['data']
            total = products_data.get('total', len(products))
        else:
            products = products_data if isinstance(products_data, list) else []
            total = len(products)
        
        print(f"Analisando {len(products)} produtos (total: {total})")
        
        location_counts = {}
        for product in products:
            loc_id = product.get('default_location_id')
            if loc_id:
                location_counts[loc_id] = location_counts.get(loc_id, 0) + 1
        
        print(f"\n📊 Distribuição de localizações padrão nos produtos:")
        for loc_id, count in location_counts.items():
            print(f"   Localização ID {loc_id}: {count} produtos")
        
        # Verificar se há múltiplos locais padrão sendo usados
        if len(location_counts) > 1:
            print(f"\n⚠️  PROBLEMA: Produtos usando {len(location_counts)} localizações padrão diferentes!")
            print("   Isso pode causar confusão no controle de estoque.")
        elif len(location_counts) == 1:
            print(f"\n✅ Todos os produtos usando a mesma localização padrão")
        else:
            print(f"\n❌ Nenhum produto com localização padrão definida!")
    
    # 4. Verificar estoques
    print(f"\n📦 VERIFICANDO ESTOQUES:")
    try:
        stocks_response = requests.get(f"{base_url}/product-stocks", headers=headers, params={"limit": 20})
        
        if stocks_response.status_code == 200:
            stocks_data = stocks_response.json()
            if isinstance(stocks_data, dict) and 'data' in stocks_data:
                stocks = stocks_data['data']
            else:
                stocks = stocks_data if isinstance(stocks_data, list) else []
            
            print(f"Analisando {len(stocks)} registros de estoque")
            
            location_stock_counts = {}
            for stock in stocks:
                loc_id = stock.get('location_id')
                if loc_id:
                    location_stock_counts[loc_id] = location_stock_counts.get(loc_id, 0) + 1
            
            print(f"\n📊 Distribuição de estoques por localização:")
            for loc_id, count in location_stock_counts.items():
                print(f"   Localização ID {loc_id}: {count} registros de estoque")
                
        else:
            print(f"⚠️  Endpoint product-stocks retornou: {stocks_response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao verificar estoques: {e}")
    
    print(f"\n" + "=" * 50)
    print("🔍 VERIFICAÇÃO CONCLUÍDA")
    print("🌐 Acesse: https://neoerp-production.up.railway.app")

if __name__ == "__main__":
    check_duplicate_locations()
