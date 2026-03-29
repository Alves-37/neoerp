#!/usr/bin/env python3
"""
Verificação simples dos locais duplicados
"""

import requests

def simple_location_check():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🔍 VERIFICAÇÃO SIMPLES - LOCAIS DUPLICADOS")
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
        
        # Verificar produtos e seus locais
        print(f"\n📋 VERIFICANDO LOCAIS DOS PRODUTOS:")
        products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 100})
        
        if products_response.status_code == 200:
            products_data = products_response.json()
            if isinstance(products_data, dict) and 'data' in products_data:
                products = products_data['data']
            else:
                products = products_data if isinstance(products_data, list) else []
            
            location_counts = {}
            location_details = {}
            
            for product in products:
                loc_id = product.get('default_location_id')
                if loc_id:
                    location_counts[loc_id] = location_counts.get(loc_id, 0) + 1
                    if loc_id not in location_details:
                        location_details[loc_id] = []
                    location_details[loc_id].append({
                        'id': product['id'],
                        'name': product['name'],
                        'active': product.get('is_active', False)
                    })
            
            print(f"\n📊 RESUMO DOS LOCAIS:")
            for loc_id, count in sorted(location_counts.items()):
                print(f"\n📍 Localização ID {loc_id}: {count} produtos")
                
                # Mostrar alguns exemplos
                examples = location_details[loc_id][:3]
                for example in examples:
                    status = "✅" if example['active'] else "❌"
                    print(f"   {status} ID: {example['id']} | {example['name']}")
                
                if len(location_details[loc_id]) > 3:
                    print(f"   ... e mais {len(location_details[loc_id]) - 3} produtos")
                
                # Verificar se é problema
                if loc_id != 63:
                    print(f"   ⚠️  ESTE NÃO É O LOCAL PADRÃO (63)!")
            
            # Conclusão
            if len(location_counts) > 1:
                print(f"\n🚨 PROBLEMA ENCONTRADO!")
                print(f"   ❌ Há produtos em {len(location_counts)} localizações diferentes")
                print(f"   💡 Isso pode causar confusão no estoque")
                
                # Sugerir correção
                non_default_locs = [loc_id for loc_id in location_counts.keys() if loc_id != 63]
                if non_default_locs:
                    print(f"\n🔧 SUGESTÃO DE CORREÇÃO:")
                    for loc_id in non_default_locs:
                        print(f"   - Mover {location_counts[loc_id]} produtos da localização {loc_id} para 63")
                        
            elif len(location_counts) == 1:
                print(f"\n✅ TODOS OS PRODUTOS USAM A MESMA LOCALIZAÇÃO")
                print(f"   📍 Localização: {list(location_counts.keys())[0]}")
            else:
                print(f"\n❌ NENHUM PRODUTO COM LOCALIZAÇÃO DEFINIDA")
        
        else:
            print(f"❌ Erro ao obter produtos: {products_response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print(f"\n" + "=" * 50)

if __name__ == "__main__":
    simple_location_check()
