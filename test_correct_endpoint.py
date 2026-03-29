#!/usr/bin/env python3
"""
Testar o endpoint correto com barra final
"""

import requests

def test_correct_endpoint():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🎯 TESTANDO ENDPOINT CORRETO COM BARRA FINAL")
    print("=" * 60)
    
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
        
        # 1. Testar endpoint correto
        print(f"\n📦 TESTANDO /stock-locations/ (COM BARRA FINAL):")
        
        response = requests.get(f"{base_url}/stock-locations/", headers=headers)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            locations_data = response.json()
            print(f"✅ SUCESSO! Endpoint correto encontrado!")
            
            # Processar dados
            if isinstance(locations_data, dict) and 'data' in locations_data:
                locations = locations_data['data']
            elif isinstance(locations_data, dict) and 'results' in locations_data:
                locations = locations_data['results']
            else:
                locations = locations_data if isinstance(locations_data, list) else []
            
            print(f"\n📋 LOCALIZAÇÕES ENCONTRADAS ({len(locations)}):")
            
            # Encontrar a "Loja Principal"
            store_principal = None
            all_locations = []
            
            for loc in locations:
                loc_id = loc['id']
                loc_name = loc.get('name', 'Sem nome')
                loc_type = loc.get('type', 'unknown')
                is_default = loc.get('is_default', False)
                company_id = loc.get('company_id')
                is_active = loc.get('is_active', True)
                
                all_locations.append(loc)
                
                # Formatar para exibição
                default_marker = "📍 [PADRÃO]" if is_default else ""
                active_marker = "✅" if is_active else "❌"
                company_marker = f"Emp:{company_id}" if company_id else ""
                
                print(f"   ID: {loc_id:3d} | {loc_name:<20} | Tipo: {loc_type:<10} | {active_marker} | {default_marker} {company_marker}")
                
                # Procurar pela Loja Principal
                if (loc_type == 'store' and 
                    is_default and 
                    company_id == 10 and
                    is_active):
                    store_principal = loc
            
            print(f"\n🔍 ANÁLISE DAS LOCALIZAÇÕES:")
            
            # Agrupar por tipo
            stores = [loc for loc in all_locations if loc.get('type') == 'store']
            warehouses = [loc for loc in all_locations if loc.get('type') == 'warehouse']
            
            print(f"\n🏪 LOJAS (Tipo: store):")
            for store in stores:
                is_default = "📍 [PADRÃO]" if store.get('is_default') else ""
                is_active = "✅" if store.get('is_active') else "❌"
                company_id = store.get('company_id')
                print(f"   ID: {store['id']:3d} | {store.get('name', 'Sem nome'):<20} | {is_active} | {is_default} (Emp: {company_id})")
            
            print(f"\n📦 ARMAZÉNS (Tipo: warehouse):")
            for warehouse in warehouses:
                is_default = "📍 [PADRÃO]" if warehouse.get('is_default') else ""
                is_active = "✅" if warehouse.get('is_active') else "❌"
                company_id = warehouse.get('company_id')
                print(f"   ID: {warehouse['id']:3d} | {warehouse.get('name', 'Sem nome'):<20} | {is_active} | {is_default} (Emp: {company_id})")
            
            if store_principal:
                print(f"\n🎯 LOJA PRINCIPAL ENCONTRADA!")
                print(f"   ✅ ID: {store_principal['id']}")
                print(f"   ✅ Nome: {store_principal.get('name')}")
                print(f"   ✅ Tipo: {store_principal.get('type')}")
                print(f"   ✅ Empresa: {store_principal.get('company_id')}")
                print(f"   ✅ Padrão: {store_principal.get('is_default')}")
                print(f"   ✅ Ativo: {store_principal.get('is_active')}")
                
                # Verificar produtos atuais
                print(f"\n📋 VERIFICANDO PRODUTOS ATUAIS:")
                products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 10})
                
                if products_response.status_code == 200:
                    products_data = products_response.json()
                    if isinstance(products_data, dict) and 'data' in products_data:
                        products = products_data['data']
                    else:
                        products = products_data if isinstance(products_data, list) else []
                    
                    print(f"   Amostra de produtos:")
                    for product in products[:5]:
                        current_loc = product.get('default_location_id')
                        is_correct = "✅" if current_loc == store_principal['id'] else "❌"
                        print(f"   {is_correct} {product['name']:<20} | Local atual: {current_loc} | Deveria ser: {store_principal['id']}")
                
                return store_principal['id']
                
            else:
                print(f"\n❌ LOJA PRINCIPAL NÃO ENCONTRADA!")
                print(f"   Não há localização do tipo 'store' que seja:")
                print(f"   - Tipo: 'store'")
                print(f"   - Padrão: true")
                print(f"   - Empresa: 10")
                print(f"   - Ativa: true")
                
                # Mostrar as stores disponíveis para análise
                if stores:
                    print(f"\n🏪 LOJAS DISPONÍVEIS PARA ANÁLISE:")
                    for store in stores:
                        print(f"   ID: {store['id']} | {store.get('name')} | Padrão: {store.get('is_default')} | Empresa: {store.get('company_id')}")
                
                return None
        
        else:
            print(f"❌ Falha: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

if __name__ == "__main__":
    result = test_correct_endpoint()
    if result:
        print(f"\n🎯 ID CORRETO DA LOJA PRINCIPAL: {result}")
        print(f"🔧 Use este ID para mover os produtos!")
    else:
        print(f"\n❌ Não foi possível determinar o ID correto")
