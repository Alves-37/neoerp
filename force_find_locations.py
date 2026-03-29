#!/usr/bin/env python3
"""
Forçar descoberta das localizações tentando diferentes métodos
"""

import requests

def force_find_locations():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🔍 FORÇANDO DESCOBERTA DAS LOCALIZAÇÕES")
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
        
        # 1. Tentar diferentes endpoints para stock-locations
        print(f"\n📦 TESTANDO MÚLTIPLOS ENDPOINTS:")
        
        possible_endpoints = [
            "/stock-locations",
            "/api/stock-locations", 
            "/v1/stock-locations",
            "/locations",
            "/api/locations",
            "/v1/locations",
            "/inventory/locations",
            "/warehouse/locations"
        ]
        
        working_endpoint = None
        locations_data = None
        
        for endpoint in possible_endpoints:
            try:
                url = f"{base_url}{endpoint}"
                print(f"   Testando: {url}")
                
                response = requests.get(url, headers=headers, timeout=10)
                
                print(f"      Status: {response.status_code}")
                
                if response.status_code == 200:
                    working_endpoint = endpoint
                    locations_data = response.json()
                    print(f"      ✅ SUCESSO! Endpoint encontrado: {endpoint}")
                    break
                else:
                    print(f"      ❌ Falha")
                    
            except Exception as e:
                print(f"      ❌ Erro: {str(e)[:50]}...")
        
        if locations_data:
            print(f"\n📋 LOCALIZAÇÕES ENCONTRADAS VIA {working_endpoint}:")
            
            # Processar resposta
            if isinstance(locations_data, list):
                locations = locations_data
            elif isinstance(locations_data, dict):
                locations = locations_data.get('data', locations_data.get('items', []))
            else:
                locations = []
            
            print(f"Total: {len(locations)} localizações")
            
            # Buscar "Loja Principal"
            store_principal = None
            for loc in locations:
                if (loc.get('type') == 'store' and 
                    loc.get('is_default') and 
                    loc.get('company_id') == 10):
                    store_principal = loc
                    break
            
            if store_principal:
                print(f"\n🎯 LOJA PRINCIPAL ENCONTRADA:")
                print(f"   ID: {store_principal['id']}")
                print(f"   Nome: {store_principal.get('name')}")
                print(f"   Tipo: {store_principal.get('type')}")
                print(f"   Padrão: {store_principal.get('is_default')}")
                
                return store_principal['id']
        
        # 2. Se não funcionou, tentar criar uma localização
        print(f"\n🔧 TENTANDO CRIAR LOCALIZAÇÃO 'LOJA PRINCIPAL':")
        
        create_payload = {
            "name": "Loja Principal",
            "type": "store",
            "company_id": 10,
            "branch_id": 94,
            "is_default": True,
            "is_active": True
        }
        
        # Tentar diferentes endpoints para criar
        create_endpoints = [
            "/stock-locations",
            "/api/stock-locations",
            "/locations"
        ]
        
        for endpoint in create_endpoints:
            try:
                url = f"{base_url}{endpoint}"
                print(f"   Tentando criar em: {url}")
                
                response = requests.post(url, headers=headers, json=create_payload)
                
                if response.status_code in [200, 201]:
                    created_location = response.json()
                    print(f"   ✅ Localização criada com sucesso!")
                    print(f"   ID: {created_location.get('id')}")
                    print(f"   Nome: {created_location.get('name')}")
                    return created_location.get('id')
                else:
                    print(f"   ❌ Falha: {response.status_code}")
                    if response.status_code == 422:
                        print(f"      📄 {response.text}")
                        
            except Exception as e:
                print(f"   ❌ Erro: {str(e)[:50]}...")
        
        # 3. Tentar adivinhar o ID baseado no padrão
        print(f"\n🎲 TENTANDO DESCOBRIR ID POR PADRÃO:")
        
        # Tentar IDs comuns para loja principal
        possible_ids = [1, 2, 3, 10, 11, 12, 20, 21, 22, 30, 31, 32, 40, 41, 42, 50, 51, 52]
        
        for test_id in possible_ids:
            try:
                # Tentar atualizar um produto com este ID
                update_payload = {"default_location_id": test_id}
                
                # Pegar um produto qualquer para testar
                products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 1})
                
                if products_response.status_code == 200:
                    products_data = products_response.json()
                    if isinstance(products_data, dict) and 'data' in products_data:
                        products = products_data['data']
                    else:
                        products = products_data if isinstance(products_data, list) else []
                    
                    if products:
                        test_product = products[0]
                        product_id = test_product['id']
                        original_loc = test_product.get('default_location_id')
                        
                        print(f"   Testando ID {test_id} com produto {test_product['name']}")
                        
                        # Tentar atualizar
                        update_response = requests.put(
                            f"{base_url}/products/{product_id}",
                            headers=headers,
                            json=update_payload
                        )
                        
                        if update_response.status_code in [200, 201]:
                            print(f"      ✅ ID {test_id} parece válido!")
                            
                            # Reverter para original
                            revert_payload = {"default_location_id": original_loc}
                            requests.put(
                                f"{base_url}/products/{product_id}",
                                headers=headers,
                                json=revert_payload
                            )
                            
                            return test_id
                        else:
                            print(f"      ❌ ID {test_id} inválido")
                            
            except Exception as e:
                print(f"   ❌ Erro ao testar ID {test_id}: {str(e)[:30]}...")
        
        print(f"\n❌ NÃO FOI POSSÍVEL DESCOBRIR O ID CORRETO")
        print(f"   🔧 Opções:")
        print(f"   1. Verificar manualmente no frontend qual é o ID da 'Loja Principal'")
        print(f"   2. Pedir ao desenvolvedor o endpoint correto")
        print(f"   3. Usar ID atual (63) e verificar se corresponde à 'Loja Principal'")
        
        return None
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return None

if __name__ == "__main__":
    result = force_find_locations()
    if result:
        print(f"\n🎯 ID DA LOJA PRINCIPAL: {result}")
    else:
        print(f"\n❌ NÃO FOI POSSÍVEL DETERMINAR O ID")
