#!/usr/bin/env python3
"""
Ativar produtos e configurar estoque corretamente
"""

import requests

def activate_products_and_fix_stock():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🔧 ATIVANDO PRODUTOS E CONFIGURANDO ESTOQUE")
    print("=" * 60)
    
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
    
    # Obter todos os produtos
    print("\n📦 Obtendo todos os produtos...")
    products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 200})
    
    if products_response.status_code != 200:
        print(f"❌ Erro ao obter produtos: {products_response.status_code}")
        return
    
    products_data = products_response.json()
    if isinstance(products_data, dict) and 'data' in products_data:
        products = products_data['data']
        total_count = products_data.get('total', len(products))
    else:
        products = products_data if isinstance(products_data, list) else []
        total_count = len(products)
    
    print(f"📦 Total de produtos: {total_count}")
    
    # Obter estabelecimento padrão
    establishments_response = requests.get(f"{base_url}/establishments", headers=headers, params={
        "company_id": 10,
        "branch_id": 94
    })
    
    if establishments_response.status_code == 200:
        establishments = establishments_response.json()
        establishment = next((e for e in establishments if e.get('is_default')), establishments[0])
        print(f"🏢 Estabelecimento padrão: {establishment['name']} (ID: {establishment['id']})")
    else:
        print("❌ Erro ao obter estabelecimento")
        return
    
    # Atualizar cada produto
    print(f"\n🚀 Ativando produtos e configurando estoque...")
    
    success = 0
    errors = 0
    
    for i, product in enumerate(products, 1):
        try:
            product_id = product['id']
            product_name = product['name']
            is_active = product.get('is_active', False)
            
            print(f"🔄 {i:3d}. {product_name} - Atualmente: {'Ativo' if is_active else 'Inativo'}")
            
            # 1. Ativar produto
            update_payload = {
                "is_active": True,
                "show_in_menu": True  # Mostrar no menu
            }
            
            update_response = requests.put(
                f"{base_url}/products/{product_id}", 
                headers=headers, 
                json=update_payload
            )
            
            if update_response.status_code in [200, 201]:
                print(f"   ✅ Produto ativado")
            else:
                print(f"   ❌ Erro ao ativar: {update_response.status_code}")
                if update_response.status_code == 422:
                    print(f"      📄 {update_response.text}")
            
            # 2. Verificar/criar estoque
            stock_response = requests.get(
                f"{base_url}/product-stocks",
                headers=headers,
                params={
                    "product_id": product_id,
                    "location_id": establishment['id']
                }
            )
            
            if stock_response.status_code == 200:
                stocks = stock_response.json()
                if isinstance(stocks, dict) and 'data' in stocks:
                    stock_list = stocks['data']
                else:
                    stock_list = stocks if isinstance(stocks, list) else []
                
                if not stock_list:
                    # Criar registro de estoque
                    stock_payload = {
                        "product_id": product_id,
                        "location_id": establishment['id'],
                        "qty_on_hand": 100,  # Estoque padrão
                        "min_quantity": 10
                    }
                    
                    create_stock = requests.post(
                        f"{base_url}/product-stocks",
                        headers=headers,
                        json=stock_payload
                    )
                    
                    if create_stock.status_code in [200, 201]:
                        print(f"   ✅ Estoque criado: 100 unidades")
                    else:
                        print(f"   ❌ Erro ao criar estoque: {create_stock.status_code}")
                else:
                    current_stock = stock_list[0].get('qty_on_hand', 0)
                    print(f"   📊 Estoque atual: {current_stock} unidades")
                    
                    if current_stock == 0:
                        # Atualizar estoque
                        update_stock = requests.put(
                            f"{base_url}/product-stocks/{stock_list[0]['id']}",
                            headers=headers,
                            json={"qty_on_hand": 100}
                        )
                        
                        if update_stock.status_code in [200, 201]:
                            print(f"   ✅ Estoque atualizado: 100 unidades")
                        else:
                            print(f"   ❌ Erro ao atualizar estoque: {update_stock.status_code}")
            
            success += 1
            
        except Exception as e:
            print(f"❌ {i:3d}. {product.get('name', 'Unknown')} - ERRO: {e}")
            errors += 1
            continue
    
    print(f"\n" + "=" * 60)
    print(f"🎉 ATUALIZAÇÃO CONCLUÍDA!")
    print(f"✅ Processados: {success} produtos")
    print(f"❌ Erros: {errors} produtos")
    
    # Verificação final
    print(f"\n🔍 VERIFICAÇÃO FINAL:")
    final_check = requests.get(f"{base_url}/products", headers=headers, params={"limit": 5})
    if final_check.status_code == 200:
        final_data = final_check.json()
        if isinstance(final_data, dict) and 'data' in final_data:
            sample_products = final_data['data']
            print(f"📦 Amostra de produtos:")
            for prod in sample_products:
                status = "✅ Ativo" if prod.get('is_active') else "❌ Inativo"
                print(f"   - {prod.get('name')} | {status}")
    
    print(f"\n🌐 Acesse: {base_url}")
    print(f"📦 Recarregue a página - os produtos devem estar ativos!")

if __name__ == "__main__":
    activate_products_and_fix_stock()
