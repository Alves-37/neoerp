#!/usr/bin/env python3
"""
Apagar todos os produtos adicionados do Mutxutxu
"""

import requests

def delete_mutxutxu_products():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🗑️ APAGANDO PRODUTOS DO MUTXUTXU")
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
    
    # Obter todos os produtos da empresa
    print("\n📦 Obtendo produtos para apagar...")
    products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 500})
    
    if products_response.status_code != 200:
        print(f"❌ Erro ao obter produtos: {products_response.status_code}")
        return
    
    products_data = products_response.json()
    if isinstance(products_data, dict) and 'data' in products_data:
        products = products_data['data']
    else:
        products = products_data if isinstance(products_data, list) else []
    
    print(f"📦 Total de produtos encontrados: {len(products)}")
    
    if not products:
        print("✅ Nenhum produto para apagar!")
        return
    
    # Apagar cada produto
    print(f"\n🗑️ Apagando produtos...")
    
    success = 0
    errors = 0
    
    for i, product in enumerate(products, 1):
        try:
            product_id = product['id']
            product_name = product['name']
            
            print(f"🗑️ {i:3d}. {product_name} (ID: {product_id})")
            
            # Apagar produto
            delete_response = requests.delete(
                f"{base_url}/products/{product_id}",
                headers=headers
            )
            
            if delete_response.status_code in [200, 204]:
                print(f"   ✅ Apagado")
                success += 1
            else:
                print(f"   ❌ Erro: {delete_response.status_code}")
                errors += 1
                
        except Exception as e:
            print(f"❌ {i:3d}. {product.get('name', 'Unknown')} - ERRO: {e}")
            errors += 1
            continue
    
    print(f"\n" + "=" * 50)
    print(f"🎉 EXCLUSÃO CONCLUÍDA!")
    print(f"✅ Apagados: {success} produtos")
    print(f"❌ Erros: {errors} produtos")
    
    # Verificação final
    print(f"\n🔍 VERIFICAÇÃO FINAL:")
    final_check = requests.get(f"{base_url}/products", headers=headers, params={"limit": 1})
    if final_check.status_code == 200:
        final_data = final_check.json()
        if isinstance(final_data, dict) and 'data' in final_data:
            remaining = final_data.get('total', 0)
        else:
            remaining = len(final_data) if isinstance(final_data, list) else 0
        
        print(f"📦 Produtos restantes: {remaining}")
    
    print(f"\n🌐 Acesse: {base_url}")
    print(f"📦 A página de produtos deve estar vazia agora!")

if __name__ == "__main__":
    delete_mutxutxu_products()
