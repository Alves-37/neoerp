#!/usr/bin/env python3
"""
Corrigir localizações dos produtos para a loja principal
"""

import requests

def fix_product_locations():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🔧 CORRIGINDO LOCALIZAÇÕES DOS PRODUTOS")
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
        
        # 1. Identificar produtos com localização incorreta
        print(f"\n🔍 IDENTIFICANDO PRODUTOS COM LOCALIZAÇÃO INCORRETA:")
        products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 200})
        
        if products_response.status_code != 200:
            print(f"❌ Erro ao obter produtos: {products_response.status_code}")
            return
        
        products_data = products_response.json()
        if isinstance(products_data, dict) and 'data' in products_data:
            products = products_data['data']
        else:
            products = products_data if isinstance(products_data, list) else []
        
        # Localização correta é 63 (Ponto Principal)
        correct_location = 63
        incorrect_products = []
        
        for product in products:
            loc_id = product.get('default_location_id')
            if loc_id and loc_id != correct_location:
                incorrect_products.append(product)
        
        print(f"📦 Encontrados {len(incorrect_products)} produtos com localização incorreta:")
        
        for product in incorrect_products:
            loc_id = product.get('default_location_id')
            print(f"   - ID: {product['id']} | {product['name']} | Local: {loc_id} (deveria ser {correct_location})")
        
        if not incorrect_products:
            print("✅ Todos os produtos já estão na localização correta!")
            return
        
        # 2. Corrigir localização dos produtos
        print(f"\n🔧 CORRIGINDO LOCALIZAÇÕES...")
        
        success_count = 0
        error_count = 0
        
        for product in incorrect_products:
            product_id = product['id']
            product_name = product['name']
            old_location = product.get('default_location_id')
            
            print(f"\n   Corrigindo: {product_name}")
            print(f"      De: Localização {old_location}")
            print(f"      Para: Localização {correct_location}")
            
            # Preparar payload para atualização
            update_payload = {
                "default_location_id": correct_location
            }
            
            # Atualizar produto
            update_response = requests.put(
                f"{base_url}/products/{product_id}",
                headers=headers,
                json=update_payload
            )
            
            if update_response.status_code in [200, 201]:
                print(f"      ✅ Atualizado com sucesso")
                success_count += 1
            else:
                print(f"      ❌ Erro: {update_response.status_code}")
                print(f"         📄 {update_response.text}")
                error_count += 1
        
        # 3. Verificação final
        print(f"\n🔍 VERIFICAÇÃO FINAL:")
        print(f"✅ Corrigidos: {success_count} produtos")
        print(f"❌ Erros: {error_count} produtos")
        
        # Verificar estado atual
        final_products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 200})
        if final_products_response.status_code == 200:
            final_products_data = final_products_response.json()
            if isinstance(final_products_data, dict) and 'data' in final_products_data:
                final_products = final_products_data['data']
            else:
                final_products = final_products_data if isinstance(final_products_data, list) else []
            
            # Contar localizações
            location_counts = {}
            for product in final_products:
                loc_id = product.get('default_location_id')
                if loc_id:
                    location_counts[loc_id] = location_counts.get(loc_id, 0) + 1
            
            print(f"\n📊 Distribuição final das localizações:")
            for loc_id, count in sorted(location_counts.items()):
                print(f"   Localização {loc_id}: {count} produtos")
            
            if len(location_counts) == 1 and list(location_counts.keys())[0] == correct_location:
                print(f"\n🎉 PERFEITO! Todos os produtos estão na localização correta ({correct_location})")
            else:
                print(f"\n⚠️  Ainda há produtos em localizações incorretas")
        
        # 4. Verificar estoques
        print(f"\n📦 VERIFICANDO ESTOQUES:")
        stocks_response = requests.get(f"{base_url}/product-stocks", headers=headers, params={"limit": 200})
        
        if stocks_response.status_code == 200:
            stocks_data = stocks_response.json()
            if isinstance(stocks_data, dict) and 'data' in stocks_data:
                stocks = stocks_data['data']
            else:
                stocks = stocks_data if isinstance(stocks_data, list) else []
            
            stock_location_counts = {}
            for stock in stocks:
                loc_id = stock.get('location_id')
                if loc_id:
                    stock_location_counts[loc_id] = stock_location_counts.get(loc_id, 0) + 1
            
            print(f"📊 Estoque por localização:")
            for loc_id, count in sorted(stock_location_counts.items()):
                print(f"   Localização {loc_id}: {count} registros de estoque")
        
        print(f"\n" + "=" * 50)
        print(f"🔧 CORREÇÃO CONCLUÍDA!")
        print(f"🌐 Acesse: https://neoerp-production.up.railway.app")
        print(f"📦 Verifique se os produtos agora aparecem na 'Loja Principal'")
        
    except Exception as e:
        print(f"❌ Erro durante correção: {e}")

if __name__ == "__main__":
    fix_product_locations()
