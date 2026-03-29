#!/usr/bin/env python3
"""
Mover todos os produtos para a Loja Principal (ID 62)
"""

import requests

def move_to_store_principal():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🔧 MOVENDO PRODUTOS PARA A LOJA PRINCIPAL")
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
        
        # ID correto da Loja Principal
        correct_location_id = 62
        
        print(f"\n🎯 OBJETIVO: Mover todos os produtos para a Loja Principal (ID: {correct_location_id})")
        
        # 1. Obter todos os produtos
        print(f"\n📦 OBTENDO TODOS OS PRODUTOS:")
        products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 200})
        
        if products_response.status_code != 200:
            print(f"❌ Erro ao obter produtos: {products_response.status_code}")
            return
        
        products_data = products_response.json()
        if isinstance(products_data, dict) and 'data' in products_data:
            products = products_data['data']
        else:
            products = products_data if isinstance(products_data, list) else []
        
        print(f"   Total de produtos: {len(products)}")
        
        # 2. Identificar produtos que precisam ser movidos
        products_to_move = []
        products_already_correct = []
        
        for product in products:
            current_location = product.get('default_location_id')
            if current_location != correct_location_id:
                products_to_move.append(product)
            else:
                products_already_correct.append(product)
        
        print(f"\n📊 ANÁLISE:")
        print(f"   ✅ Já na Loja Principal: {len(products_already_correct)} produtos")
        print(f"   🔄 Precisam mover: {len(products_to_move)} produtos")
        
        if products_to_move:
            print(f"\n🔄 PRODUTOS QUE SERÃO MOVIDOS:")
            for product in products_to_move[:10]:  # Mostrar apenas 10
                current_loc = product.get('default_location_id')
                print(f"   - {product['name']:<25} | De: {current_loc} → Para: {correct_location_id}")
            
            if len(products_to_move) > 10:
                print(f"   ... e mais {len(products_to_move) - 10} produtos")
        
        if not products_to_move:
            print(f"\n🎉 TODOS OS PRODUTOS JÁ ESTÃO NA LOJA PRINCIPAL!")
            return
        
        # 3. Mover os produtos
        print(f"\n🔧 MOVENDO PRODUTOS PARA A LOJA PRINCIPAL...")
        
        success_count = 0
        error_count = 0
        
        for i, product in enumerate(products_to_move, 1):
            product_id = product['id']
            product_name = product['name']
            old_location = product.get('default_location_id')
            
            print(f"   {i:3d}/{len(products_to_move)} {product_name:<25} | {old_location} → {correct_location_id}")
            
            # Preparar payload
            update_payload = {
                "default_location_id": correct_location_id
            }
            
            # Atualizar produto
            update_response = requests.put(
                f"{base_url}/products/{product_id}",
                headers=headers,
                json=update_payload
            )
            
            if update_response.status_code in [200, 201]:
                success_count += 1
                print(f"        ✅ Sucesso")
            else:
                error_count += 1
                print(f"        ❌ Erro: {update_response.status_code}")
                if update_response.status_code == 422:
                    print(f"           📄 {update_response.text}")
        
        # 4. Verificação final
        print(f"\n🔍 VERIFICAÇÃO FINAL:")
        print(f"✅ Movidos com sucesso: {success_count} produtos")
        print(f"❌ Erros: {error_count} produtos")
        
        # Verificar estado final
        final_products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 200})
        if final_products_response.status_code == 200:
            final_products_data = final_products_response.json()
            if isinstance(final_products_data, dict) and 'data' in final_products_data:
                final_products = final_products_data['data']
            else:
                final_products = final_products_data if isinstance(final_products_data, list) else []
            
            # Contar localizações finais
            final_location_counts = {}
            for product in final_products:
                loc_id = product.get('default_location_id')
                if loc_id:
                    final_location_counts[loc_id] = final_location_counts.get(loc_id, 0) + 1
            
            print(f"\n📊 DISTRIBUIÇÃO FINAL DAS LOCALIZAÇÕES:")
            for loc_id, count in sorted(final_location_counts.items()):
                location_name = {
                    62: "Loja Principal",
                    63: "Armazém", 
                    64: "Loja"
                }.get(loc_id, f"Local {loc_id}")
                
                marker = "🎯" if loc_id == correct_location_id else ""
                print(f"   ID {loc_id} ({location_name:<15}): {count:3d} produtos {marker}")
            
            # Verificar se todos estão corretos
            products_in_correct_location = final_location_counts.get(correct_location_id, 0)
            total_products = len(final_products)
            
            if products_in_correct_location == total_products:
                print(f"\n🎉 SUCESSO TOTAL!")
                print(f"   ✅ Todos os {total_products} produtos estão na Loja Principal")
                print(f"   ✅ Produtos visíveis na loja principal do frontend")
            else:
                print(f"\n⚠️  Ainda há produtos em localizações incorretas")
                print(f"   📊 {products_in_correct_location}/{total_products} na Loja Principal")
        
        # 5. Verificar estoques
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
                location_name = {
                    62: "Loja Principal",
                    63: "Armazém", 
                    64: "Loja"
                }.get(loc_id, f"Local {loc_id}")
                
                print(f"   ID {loc_id} ({location_name:<15}): {count:3d} registros")
        
        print(f"\n" + "=" * 50)
        print(f"🎉 OPERAÇÃO CONCLUÍDA!")
        print(f"🌐 Acesse: https://neoerp-production.up.railway.app")
        print(f"📦 Os produtos agora devem aparecer na 'Loja Principal' do frontend!")
        
    except Exception as e:
        print(f"❌ Erro durante operação: {e}")

if __name__ == "__main__":
    move_to_store_principal()
