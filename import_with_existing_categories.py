#!/usr/bin/env python3
"""
Importar produtos usando as categorias existentes do ERP
"""

import requests

# Mapeamento das categorias do PDF para as categorias existentes
category_mapping = {
    "Sumos, agua e refrescos": "Bebidas",
    "Outos": "Outros", 
    "Congelados": "Pratos",
    "Bolos e salgados": "Pratos",
    "Azeites": "Outros",
    "pizzas": "Pratos",
    "Bolachas,doces": "Sobremesas",
    "Temperos": "Outros"
}

# Produtos do Mutxutxu com mapeamento de categorias
products_data = [
    {"name": "2M garrafa", "price": 80.00, "stock": 100, "category": "Bebidas"},
    {"name": "2M lata", "price": 90.00, "stock": 100, "category": "Bebidas"},
    {"name": "Agua Pequena", "price": 50.00, "stock": 100, "category": "Bebidas"},
    {"name": "Agua Tonica", "price": 60.00, "stock": 100, "category": "Bebidas"},
    {"name": "Agua grande", "price": 100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Amarula", "price": 1400.00, "stock": 100, "category": "Bebidas"},
    {"name": "Azinhas", "price": 300.00, "stock": 104, "category": "Bebidas"},
    {"name": "Bife Completo", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "Bull dog", "price": 3300.00, "stock": 100, "category": "Bebidas"},
    {"name": "C double burger", "price": 500.00, "stock": 10, "category": "Pratos"},
    {"name": "Cabeca de Peixe", "price": 200.00, "stock": 10, "category": "Pratos"},
    {"name": "Cabeca de Vaca", "price": 200.00, "stock": 10, "category": "Pratos"},
    {"name": "Caldo verde", "price": 150.00, "stock": 10, "category": "Pratos"},
    {"name": "Cappy", "price": 80.00, "stock": 100, "category": "Bebidas"},
    {"name": "Carne de porco", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "Ceres", "price": 200.00, "stock": 100, "category": "Bebidas"},
    {"name": "Champanhe Anabela", "price": 1300.00, "stock": 100, "category": "Bebidas"},
    {"name": "Champanhe JS", "price": 1200.00, "stock": 100, "category": "Bebidas"},
    {"name": "Champanhe Martini Rose", "price": 1200.00, "stock": 100, "category": "Bebidas"},
    {"name": "Champanhe Toste", "price": 1500.00, "stock": 100, "category": "Bebidas"},
    {"name": "Chamussas", "price": 25.00, "stock": 10, "category": "Pratos"},
    {"name": "Chourico", "price": 300.00, "stock": 10, "category": "Pratos"},
    {"name": "Cochinhas", "price": 30.00, "stock": 9, "category": "Pratos"},
    {"name": "Compal", "price": 200.00, "stock": 100, "category": "Bebidas"},
    {"name": "Dobrada", "price": 200.00, "stock": 10, "category": "Pratos"},
    {"name": "Dry Lemon", "price": 150.00, "stock": 100, "category": "Bebidas"},
    {"name": "Escape Vodka", "price": 1000.00, "stock": 100, "category": "Bebidas"},
    {"name": "Four Causin Grade", "price": 1600.00, "stock": 100, "category": "Bebidas"},
    {"name": "Frango 1 quarto", "price": 300.00, "stock": 10, "category": "Pratos"},
    {"name": "Frango a Passarinho", "price": 1250.00, "stock": 10, "category": "Pratos"},
    {"name": "Frango assado 1", "price": 1200.00, "stock": 10, "category": "Pratos"},
    {"name": "Frango assado meio", "price": 600.00, "stock": 10, "category": "Pratos"},
    {"name": "Galinha Fumado", "price": 1500.00, "stock": 10, "category": "Pratos"},
    {"name": "Galo Dourado", "price": 1100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Gatao", "price": 1500.00, "stock": 100, "category": "Bebidas"},
    {"name": "Gordon", "price": 1100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Grants", "price": 1800.00, "stock": 100, "category": "Bebidas"},
    {"name": "HENICKER", "price": 100.00, "stock": 500, "category": "Bebidas"},
    {"name": "Hamburger Completo", "price": 300.00, "stock": 8, "category": "Pratos"},
    {"name": "Hanked Bannister", "price": 1100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Havelock", "price": 1100.00, "stock": 100, "category": "Bebidas"},
    {"name": "Humburger S", "price": 250.00, "stock": 10, "category": "Pratos"},
    {"name": "Joh walker red", "price": 1800.00, "stock": 100, "category": "Bebidas"},
    {"name": "John Walker black", "price": 3500.00, "stock": 100, "category": "Bebidas"},
    {"name": "Maicgregor", "price": 1500.00, "stock": 100, "category": "Bebidas"},
    {"name": "Martine", "price": 1400.00, "stock": 100, "category": "Bebidas"},
    {"name": "Mutxutxu de galinha", "price": 200.00, "stock": 110, "category": "Pratos"},
    {"name": "Pizza 4 estacoes", "price": 100.00, "stock": 10, "category": "Pratos"},
    {"name": "Pizza de atum", "price": 700.00, "stock": 10, "category": "Pratos"},
    {"name": "Pizza de frango", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "Pizza vegetariana", "price": 700.00, "stock": 10, "category": "Pratos"},
    {"name": "Quinta da bolota", "price": 1200.00, "stock": 100, "category": "Bebidas"},
    {"name": "Red Bull", "price": 150.00, "stock": 100, "category": "Bebidas"},
    {"name": "Refresco em lata", "price": 60.00, "stock": 97, "category": "Bebidas"},
    {"name": "Rose Grande", "price": 1600.00, "stock": 100, "category": "Bebidas"},
    {"name": "Rusian", "price": 1000.00, "stock": 100, "category": "Bebidas"},
    {"name": "Silk spice", "price": 1800.00, "stock": 100, "category": "Bebidas"},
    {"name": "Sopa de Feijao", "price": 150.00, "stock": 10, "category": "Pratos"},
    {"name": "Sopa de legumes", "price": 150.00, "stock": 10, "category": "Pratos"},
    {"name": "Takeaway", "price": 30.00, "stock": 100, "category": "Pratos"},
    {"name": "Tbone", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "Tostas com batata frita", "price": 300.00, "stock": 10, "category": "Pratos"},
    {"name": "Worce", "price": 300.00, "stock": 10, "category": "Pratos"},
    {"name": "altum", "price": 800.00, "stock": 10, "category": "Bebidas"},
    {"name": "bermine", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "bife trinchado", "price": 700.00, "stock": 101, "category": "Pratos"},
    {"name": "brizer", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "brutal", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "budweiser", "price": 100.00, "stock": 10, "category": "Bebidas"},
    {"name": "cape ruby", "price": 1100.00, "stock": 10, "category": "Bebidas"},
    {"name": "casal garcia", "price": 1200.00, "stock": 10, "category": "Bebidas"},
    {"name": "castle lite", "price": 100.00, "stock": 10, "category": "Bebidas"},
    {"name": "celler cast", "price": 1100.00, "stock": 100, "category": "Bebidas"},
    {"name": "chima", "price": 100.00, "stock": 10, "category": "Sobremesas"},
    {"name": "dose de arroz", "price": 100.00, "stock": 10, "category": "Pratos"},
    {"name": "dose de batata", "price": 100.00, "stock": 10, "category": "Pratos"},
    {"name": "drosdy hof", "price": 800.00, "stock": 10, "category": "Bebidas"},
    {"name": "duas quintas", "price": 1100.00, "stock": 10, "category": "Bebidas"},
    {"name": "filetes", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "gazela", "price": 1100.00, "stock": 10, "category": "Bebidas"},
    {"name": "hunters dray", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "hunters gold", "price": 100.00, "stock": 10, "category": "Bebidas"},
    {"name": "jamson", "price": 1500.00, "stock": 100, "category": "Bebidas"},
    {"name": "lemone", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "lulas", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "mao de vaca", "price": 200.00, "stock": 9, "category": "Pratos"},
    {"name": "pandora", "price": 1100.00, "stock": 10, "category": "Bebidas"},
    {"name": "peixe chambo grande", "price": 1000.00, "stock": 10, "category": "Pratos"},
    {"name": "peixe chambo medio", "price": 800.00, "stock": 10, "category": "Pratos"},
    {"name": "peixe chambo pequeno", "price": 600.00, "stock": 10, "category": "Pratos"},
    {"name": "prego no pao", "price": 300.00, "stock": 10, "category": "Pratos"},
    {"name": "prego no prato", "price": 450.00, "stock": 10, "category": "Pratos"},
    {"name": "preta grande", "price": 80.00, "stock": 10, "category": "Bebidas"},
    {"name": "preta lata", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "preta pequena", "price": 100.00, "stock": 10, "category": "Bebidas"},
    {"name": "saladas", "price": 75.00, "stock": 10, "category": "Sobremesas"},
    {"name": "sande de ovo", "price": 200.00, "stock": 10, "category": "Pratos"},
    {"name": "segredo sao miguel", "price": 1200.00, "stock": 10, "category": "Bebidas"},
    {"name": "spin", "price": 120.00, "stock": 10, "category": "Bebidas"},
    {"name": "super bock", "price": 80.00, "stock": 10, "category": "Bebidas"},
    {"name": "vinho cabriz", "price": 1200.00, "stock": 10, "category": "Bebidas"},
    {"name": "vinho portada", "price": 1200.00, "stock": 10, "category": "Bebidas"}
]

def import_with_existing_categories():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🚀 IMPORTANDO PRODUTOS COM CATEGORIAS EXISTENTES")
    print("=" * 60)
    
    # Login
    login = requests.post(f"{base_url}/auth/login", json={
        "email": "mutxutxu@gmail.com", 
        "password": "Mutxutxu@43"
    })
    
    token = login.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login realizado!")
    
    # Obter categorias existentes
    cat_response = requests.get(f"{base_url}/product-categories", headers=headers)
    categories = cat_response.json()
    
    # Mapear nome da categoria para ID
    cat_name_to_id = {cat['name']: cat['id'] for cat in categories}
    
    print(f"\n📁 Categorias disponíveis: {len(cat_name_to_id)}")
    for name, id in cat_name_to_id.items():
        print(f"   {name} (ID: {id})")
    
    # Criar localização padrão se não existir
    loc_response = requests.get(f"{base_url}/stock-locations", headers=headers)
    if loc_response.status_code == 200 and loc_response.json():
        locations = loc_response.json()
        default_loc = next((l for l in locations if l.get('is_default')), locations[0])
        default_loc_id = default_loc['id']
        print(f"\n📍 Usando localização: {default_loc['name']} (ID: {default_loc_id})")
    else:
        print("\n❌ Nenhuma localização encontrada")
        return
    
    # Importar produtos
    print(f"\n🚀 Importando {len(products_data)} produtos...")
    
    success = 0
    errors = 0
    skipped = 0
    
    for i, product in enumerate(products_data, 1):
        try:
            # Verificar se categoria existe
            if product['category'] not in cat_name_to_id:
                print(f"⚠️  {i:3d}. {product['name']} - Categoria '{product['category']}' não encontrada")
                errors += 1
                continue
            
            # Verificar se produto já existe
            existing_response = requests.get(
                f"{base_url}/products", 
                headers=headers, 
                params={"q": product['name'], "limit": 1}
            )
            
            if existing_response.status_code == 200:
                existing_data = existing_response.json()
                if isinstance(existing_data, dict) and existing_data.get('data'):
                    if existing_data['data']:
                        print(f"⚠️  {i:3d}. {product['name']} - JÁ EXISTE")
                        skipped += 1
                        continue
            
            # Criar produto
            payload = {
                "name": product['name'],
                "price": product['price'],
                "cost": product['price'] * 0.7,
                "category_id": cat_name_to_id[product['category']],
                "default_location_id": default_loc_id,
                "business_type": "restaurant",
                "unit": "un",
                "is_active": True,
                "track_stock": True,
                "min_stock": max(1, product['stock'] // 4),
                "sku": f"RES-10-{i:03d}"
            }
            
            prod_response = requests.post(f"{base_url}/products", headers=headers, json=payload)
            
            if prod_response.status_code in [200, 201]:
                prod_data = prod_response.json()
                prod_id = prod_data.get('id')
                
                # Criar estoque
                stock_payload = {
                    "product_id": prod_id,
                    "location_id": default_loc_id,
                    "qty_on_hand": product['stock'],
                    "min_quantity": max(1, product['stock'] // 4)
                }
                
                stock_response = requests.post(f"{base_url}/product-stocks", headers=headers, json=stock_payload)
                
                print(f"✅ {i:3d}. {product['name']} - MZN {product['price']:7.2f} | {product['category']}")
                success += 1
                
            else:
                print(f"❌ {i:3d}. {product['name']} - ERRO {prod_response.status_code}")
                if prod_response.status_code == 422:
                    print(f"     📄 {prod_response.text}")
                errors += 1
                
        except Exception as e:
            print(f"❌ {i:3d}. {product['name']} - ERRO: {e}")
            errors += 1
    
    print(f"\n" + "=" * 60)
    print(f"🎉 IMPORTAÇÃO CONCLUÍDA!")
    print(f"✅ Sucesso: {success} produtos")
    print(f"⚠️  Pulados: {skipped} produtos")
    print(f"❌ Erros: {errors} produtos")
    print(f"📊 Total: {success + skipped + errors} produtos")
    
    if success > 0:
        print(f"\n🌐 Acesse: https://neoerp-production.up.railway.app")
        print(f"📦 Os produtos devem aparecer agora!")
        print(f"🔄 Recarregue a página de produtos no frontend")

if __name__ == "__main__":
    import_with_existing_categories()
