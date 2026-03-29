#!/usr/bin/env python3
"""
Descobrir o ID correto da "Loja Principal" (tipo: loja, padrão: sim)
"""

import requests

def find_store_principal_id():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🔍 DESCOBRINDO ID DA 'LOJA PRINCIPAL'")
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
        
        # 1. Tentar acessar stock-locations de diferentes formas
        print(f"\n📦 TENTANDO ACESSAR STOCK-LOCATIONS:")
        
        # Tentar com headers diferentes
        headers_with_content = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        endpoints = [
            f"{base_url}/stock-locations",
            f"{base_url}/api/stock-locations",
            f"{base_url}/v1/stock-locations"
        ]
        
        locations_data = None
        
        for endpoint in endpoints:
            try:
                print(f"   Testando: {endpoint}")
                response = requests.get(endpoint, headers=headers_with_content)
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    locations_data = response.json()
                    print(f"   ✅ SUCESSO! Dados obtidos")
                    break
                elif response.status_code == 401:
                    print(f"   ❌ Não autorizado")
                elif response.status_code == 404:
                    print(f"   ❌ Não encontrado")
                else:
                    print(f"   ❌ Outro erro: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Exceção: {e}")
        
        if locations_data:
            print(f"\n📋 LOCALIZAÇÕES ENCONTRADAS:")
            
            # Processar diferentes formatos de resposta
            if isinstance(locations_data, list):
                locations = locations_data
            elif isinstance(locations_data, dict):
                if 'data' in locations_data:
                    locations = locations_data['data']
                elif 'items' in locations_data:
                    locations = locations_data['items']
                else:
                    locations = []
            else:
                locations = []
            
            print(f"Total de localizações: {len(locations)}")
            
            # Encontrar a "Loja Principal" (tipo: loja, padrão: sim)
            store_principal = None
            all_stores = []
            all_warehouses = []
            
            for loc in locations:
                loc_id = loc['id']
                loc_name = loc.get('name', 'Sem nome')
                loc_type = loc.get('type', 'unknown')
                is_default = loc.get('is_default', False)
                company_id = loc.get('company_id')
                
                # Formatar para exibição
                default_marker = "📍 [PADRÃO]" if is_default else ""
                company_marker = f"Empresa: {company_id}" if company_id else ""
                
                print(f"   ID: {loc_id} | {loc_name} | Tipo: {loc_type} | {default_marker} {company_marker}")
                
                # Categorizar
                if loc_type == 'store':
                    all_stores.append(loc)
                    if is_default and company_id == 10:
                        store_principal = loc
                elif loc_type == 'warehouse':
                    all_warehouses.append(loc)
            
            print(f"\n🏪 LOJAS (Tipo: store):")
            for store in all_stores:
                is_default = "📍 [PADRÃO]" if store.get('is_default') else ""
                company_id = store.get('company_id')
                company_marker = f"(Empresa: {company_id})" if company_id else ""
                print(f"   ID: {store['id']} | {store.get('name', 'Sem nome')} {is_default} {company_marker}")
            
            print(f"\n📦 ARMAZÉNS (Tipo: warehouse):")
            for warehouse in all_warehouses:
                is_default = "📍 [PADRÃO]" if warehouse.get('is_default') else ""
                company_id = warehouse.get('company_id')
                company_marker = f"(Empresa: {company_id})" if company_id else ""
                print(f"   ID: {warehouse['id']} | {warehouse.get('name', 'Sem nome')} {is_default} {company_marker}")
            
            if store_principal:
                print(f"\n🎯 LOJA PRINCIPAL ENCONTRADA:")
                print(f"   ID: {store_principal['id']}")
                print(f"   Nome: {store_principal.get('name', 'Sem nome')}")
                print(f"   Tipo: {store_principal.get('type')}")
                print(f"   Empresa: {store_principal.get('company_id')}")
                print(f"   Padrão: {store_principal.get('is_default')}")
                
                # Verificar produtos atuais
                print(f"\n📋 VERIFICANDO PRODUTOS ATUAIS:")
                products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 10})
                
                if products_response.status_code == 200:
                    products_data = products_response.json()
                    if isinstance(products_data, dict) and 'data' in products_data:
                        products = products_data['data']
                    else:
                        products = products_data if isinstance(products_data, list) else []
                    
                    print(f"   Amostra de produtos e suas localizações:")
                    for product in products[:5]:
                        current_loc = product.get('default_location_id')
                        is_correct = "✅" if current_loc == store_principal['id'] else "❌"
                        print(f"   {is_correct} {product['name']} | Local: {current_loc} (deveria ser {store_principal['id']})")
                
                print(f"\n🔧 RECOMENDAÇÃO:")
                print(f"   Mover todos os produtos para a localização ID: {store_principal['id']}")
                
            else:
                print(f"\n❌ LOJA PRINCIPAL NÃO ENCONTRADA!")
                print(f"   Não há localização do tipo 'store' marcada como padrão para empresa 10")
                
                # Sugerir criar uma
                print(f"\n💡 SUGESTÃO:")
                print(f"   Criar uma nova localização:")
                print(f"   - Nome: 'Loja Principal'")
                print(f"   - Tipo: 'store'")
                print(f"   - Empresa: 10")
                print(f"   - Padrão: true")
        
        else:
            print(f"\n❌ NÃO FOI POSSÍVEL ACESSAR AS LOCALIZAÇÕES")
            print(f"   Tentando abordagem alternativa...")
            
            # Tentar usar establishments como referência
            print(f"\n🏢 USANDO ESTABLISHMENTS COMO REFERÊNCIA:")
            establishments_response = requests.get(f"{base_url}/establishments", headers=headers, params={
                "company_id": 10,
                "branch_id": 94
            })
            
            if establishments_response.status_code == 200:
                establishments = establishments_response.json()
                print(f"   Establishments disponíveis:")
                
                for est in establishments:
                    is_default = "📍 [PADRÃO]" if est.get('is_default') else ""
                    print(f"   ID: {est['id']} | {est.get('name', 'Sem nome')} {is_default}")
        
        print(f"\n" + "=" * 50)
        print("🌐 Acesse: https://neoerp-production.up.railway.app")
        
    except Exception as e:
        print(f"❌ Erro durante verificação: {e}")

if __name__ == "__main__":
    find_store_principal_id()
