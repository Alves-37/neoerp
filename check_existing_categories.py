#!/usr/bin/env python3
"""
Verificar categorias existentes no ERP de produção
"""

import requests

def check_categories():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🔍 VERIFICANDO CATEGORIAS EXISTENTES NO ERP")
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
    
    # Obter categorias
    print("\n📁 CATEGORIAS EXISTENTES:")
    cat_response = requests.get(f"{base_url}/product-categories", headers=headers)
    
    if cat_response.status_code != 200:
        print(f"❌ Erro ao obter categorias: {cat_response.status_code}")
        return
    
    categories = cat_response.json()
    print(f"Total: {len(categories)} categorias\n")
    
    for i, cat in enumerate(categories, 1):
        print(f"{i:2d}. ID: {cat.get('id')} | {cat.get('name')}")
        if cat.get('business_type'):
            print(f"     Tipo: {cat.get('business_type')}")
    
    # Obter produtos existentes
    print(f"\n📦 PRODUTOS EXISTENTES:")
    prod_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 20})
    
    if prod_response.status_code == 200:
        products_data = prod_response.json()
        
        if isinstance(products_data, dict) and 'data' in products_data:
            products = products_data['data']
            total = products_data.get('total', len(products))
        else:
            products = products_data if isinstance(products_data, list) else []
            total = len(products)
        
        print(f"Total: {total} produtos (mostrando primeiros {len(products)})\n")
        
        for i, prod in enumerate(products[:10], 1):
            print(f"{i:2d}. ID: {prod.get('id')} | {prod.get('name')}")
            print(f"     💰 MZN {prod.get('price', 0):.2f}")
            if prod.get('category_id'):
                cat_name = next((c.get('name') for c in categories if c.get('id') == prod.get('category_id')), 'Unknown')
                print(f"     📁 Categoria: {cat_name}")
    
    # Obter localizações
    print(f"\n📍 LOCALIZAÇÕES:")
    loc_response = requests.get(f"{base_url}/stock-locations", headers=headers)
    
    if loc_response.status_code == 200:
        locations = loc_response.json()
        print(f"Total: {len(locations)} localizações\n")
        
        for i, loc in enumerate(locations, 1):
            is_default = " (PADRÃO)" if loc.get('is_default') else ""
            print(f"{i:2d}. ID: {loc.get('id')} | {loc.get('name')}{is_default}")
            print(f"     Tipo: {loc.get('type')}")
    
    print(f"\n🎯 ANÁLISE CONCLUÍDA!")
    print(f"🌐 URL do sistema: {base_url}")
    print(f"📊 Use estas informações para importar os produtos corretamente!")

if __name__ == "__main__":
    check_categories()
