#!/usr/bin/env python3
"""
Script para importar produtos do Mutxutxu para o servidor de produção
"""

import requests
import json

# Dados dos produtos extraídos do PDF
products_data = [
    {"name": "2M garrafa", "price": 80.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "2M lata", "price": 90.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Agua Pequena", "price": 50.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Agua Tonica", "price": 60.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Agua grande", "price": 100.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Amarula", "price": 1400.00, "stock": 100, "category": "Outos"},
    {"name": "Azinhas", "price": 300.00, "stock": 104, "category": "Outos"},
    {"name": "Bife Completo", "price": 800.00, "stock": 10, "category": "Congelados"},
    {"name": "Bull dog", "price": 3300.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "C double burger", "price": 500.00, "stock": 10, "category": "Bolos e salgados"},
    {"name": "Cabeca de Peixe", "price": 200.00, "stock": 10, "category": "Outos"},
    {"name": "Cabeca de Vaca", "price": 200.00, "stock": 10, "category": "Outos"},
    {"name": "Caldo verde", "price": 150.00, "stock": 10, "category": "Azeites"},
    {"name": "Cappy", "price": 80.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Carne de porco", "price": 800.00, "stock": 10, "category": "Congelados"},
    {"name": "Ceres", "price": 200.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Champanhe Anabela", "price": 1300.00, "stock": 100, "category": "Outos"},
    {"name": "Champanhe JS", "price": 1200.00, "stock": 100, "category": "Outos"},
    {"name": "Champanhe Martini Rose", "price": 1200.00, "stock": 100, "category": "Outos"},
    {"name": "Champanhe Toste", "price": 1500.00, "stock": 100, "category": "Outos"},
    {"name": "Chamussas", "price": 25.00, "stock": 10, "category": "Outos"},
    {"name": "Chourico", "price": 300.00, "stock": 10, "category": "Outos"},
    {"name": "Cochinhas", "price": 30.00, "stock": 9, "category": "Outos"},
    {"name": "Compal", "price": 200.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Dobrada", "price": 200.00, "stock": 10, "category": "Outos"},
    {"name": "Dry Lemon", "price": 150.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Escape Vodka", "price": 1000.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Four Causin Grade", "price": 1600.00, "stock": 100, "category": "Outos"},
    {"name": "Frango 1 quarto", "price": 300.00, "stock": 10, "category": "Congelados"},
    {"name": "Frango a Passarinho", "price": 1250.00, "stock": 10, "category": "Congelados"},
    {"name": "Frango assado 1", "price": 1200.00, "stock": 10, "category": "Congelados"},
    {"name": "Frango assado meio", "price": 600.00, "stock": 10, "category": "Congelados"},
    {"name": "Galinha Fumado", "price": 1500.00, "stock": 10, "category": "Congelados"},
    {"name": "Galo Dourado", "price": 1100.00, "stock": 100, "category": "Outos"},
    {"name": "Gatao", "price": 1500.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Gordon", "price": 1100.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Grants", "price": 1800.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "HENICKER", "price": 100.00, "stock": 500, "category": "Outos"},
    {"name": "Hamburger Completo", "price": 300.00, "stock": 8, "category": "Bolos e salgados"},
    {"name": "Hanked Bannister", "price": 1100.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Havelock", "price": 1100.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Humburger S", "price": 250.00, "stock": 10, "category": "Bolos e salgados"},
    {"name": "Joh walker red", "price": 1800.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "John Walker black", "price": 3500.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Maicgregor", "price": 1500.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Martine", "price": 1400.00, "stock": 100, "category": "Outos"},
    {"name": "Mutxutxu de galinha", "price": 200.00, "stock": 110, "category": "Outos"},
    {"name": "Pizza 4 estacoes", "price": 100.00, "stock": 10, "category": "pizzas"},
    {"name": "Pizza de atum", "price": 700.00, "stock": 10, "category": "pizzas"},
    {"name": "Pizza de frango", "price": 800.00, "stock": 10, "category": "pizzas"},
    {"name": "Pizza vegetariana", "price": 700.00, "stock": 10, "category": "pizzas"},
    {"name": "Quinta da bolota", "price": 1200.00, "stock": 100, "category": "Outos"},
    {"name": "Red Bull", "price": 150.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Refresco em lata", "price": 60.00, "stock": 97, "category": "Sumos, agua e refrescos"},
    {"name": "Rose Grande", "price": 1600.00, "stock": 100, "category": "Outos"},
    {"name": "Rusian", "price": 1000.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "Silk spice", "price": 1800.00, "stock": 100, "category": "Outos"},
    {"name": "Sopa de Feijao", "price": 150.00, "stock": 10, "category": "Azeites"},
    {"name": "Sopa de legumes", "price": 150.00, "stock": 10, "category": "Azeites"},
    {"name": "Takeaway", "price": 30.00, "stock": 100, "category": "Outos"},
    {"name": "Tbone", "price": 800.00, "stock": 10, "category": "Congelados"},
    {"name": "Tostas com batata frita", "price": 300.00, "stock": 10, "category": "Outos"},
    {"name": "Worce", "price": 300.00, "stock": 10, "category": "Outos"},
    {"name": "altum", "price": 800.00, "stock": 10, "category": "Outos"},
    {"name": "bermine", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "bife trinchado", "price": 700.00, "stock": 101, "category": "Outos"},
    {"name": "brizer", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "brutal", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "budweiser", "price": 100.00, "stock": 10, "category": "Outos"},
    {"name": "cape ruby", "price": 1100.00, "stock": 10, "category": "Outos"},
    {"name": "casal garcia", "price": 1200.00, "stock": 10, "category": "Outos"},
    {"name": "castle lite", "price": 100.00, "stock": 10, "category": "Outos"},
    {"name": "celler cast", "price": 1100.00, "stock": 100, "category": "Outos"},
    {"name": "chima", "price": 100.00, "stock": 10, "category": "Bolachas,doces"},
    {"name": "dose de arroz", "price": 100.00, "stock": 10, "category": "Bolachas,doces"},
    {"name": "dose de batata", "price": 100.00, "stock": 10, "category": "Bolachas,doces"},
    {"name": "drosdy hof", "price": 800.00, "stock": 10, "category": "Outos"},
    {"name": "duas quintas", "price": 1100.00, "stock": 10, "category": "Outos"},
    {"name": "filetes", "price": 800.00, "stock": 10, "category": "Temperos"},
    {"name": "gazela", "price": 1100.00, "stock": 10, "category": "Outos"},
    {"name": "hunters dray", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "hunters gold", "price": 100.00, "stock": 10, "category": "Outos"},
    {"name": "jamson", "price": 1500.00, "stock": 100, "category": "Sumos, agua e refrescos"},
    {"name": "lemone", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "lulas", "price": 800.00, "stock": 10, "category": "Temperos"},
    {"name": "mao de vaca", "price": 200.00, "stock": 9, "category": "Outos"},
    {"name": "pandora", "price": 1100.00, "stock": 10, "category": "Outos"},
    {"name": "peixe chambo grande", "price": 1000.00, "stock": 10, "category": "Temperos"},
    {"name": "peixe chambo medio", "price": 800.00, "stock": 10, "category": "Temperos"},
    {"name": "peixe chambo pequeno", "price": 600.00, "stock": 10, "category": "Temperos"},
    {"name": "prego no pao", "price": 300.00, "stock": 10, "category": "Bolos e salgados"},
    {"name": "prego no prato", "price": 450.00, "stock": 10, "category": "Bolos e salgados"},
    {"name": "preta grande", "price": 80.00, "stock": 10, "category": "Outos"},
    {"name": "preta lata", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "preta pequena", "price": 100.00, "stock": 10, "category": "Outos"},
    {"name": "saladas", "price": 75.00, "stock": 10, "category": "Bolachas,doces"},
    {"name": "sande de ovo", "price": 200.00, "stock": 10, "category": "Bolos e salgados"},
    {"name": "segredo sao miguel", "price": 1200.00, "stock": 10, "category": "Outos"},
    {"name": "spin", "price": 120.00, "stock": 10, "category": "Outos"},
    {"name": "super bock", "price": 80.00, "stock": 10, "category": "Outos"},
    {"name": "vinho cabriz", "price": 1200.00, "stock": 10, "category": "Outos"},
    {"name": "vinho portada", "price": 1200.00, "stock": 10, "category": "Outos"}
]

def import_to_production():
    """
    Importa produtos para o servidor de produção via API
    """
    print("🚀 IMPORTANDO PRODUTOS PARA SERVIDOR DE PRODUÇÃO")
    print("=" * 60)
    
    base_url = "https://neoerp-production.up.railway.app"
    
    # Você precisa fornecer um token válido
    print("⚠️  ATENÇÃO: Você precisa de um token de autenticação válido!")
    print("📝 Passos:")
    print("   1. Faça login no sistema")
    print("   2. Abra o DevTools (F12)")
    print("   3. Vá para Application > Local Storage")
    print("   4. Copie o valor de 'token'")
    print("   5. Cole abaixo:")
    
    token = input("🔑 Token de autenticação: ").strip()
    
    if not token:
        print("❌ Token não fornecido. Operação cancelada.")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Testar conexão
        print("\n🔍 Testando conexão com produção...")
        response = requests.get(f"{base_url}/me", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Falha na autenticação: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            return
        
        user_data = response.json()
        print(f"✅ Conectado como: {user_data.get('email', 'Unknown')}")
        
        # Obter categorias existentes
        print("\n📁 Verificando categorias existentes...")
        response = requests.get(f"{base_url}/product-categories", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Erro ao buscar categorias: {response.status_code}")
            return
        
        categories = response.json()
        category_map = {}
        
        for cat in categories:
            category_map[cat['name']] = cat['id']
        
        print(f"✅ {len(categories)} categorias encontradas")
        
        # Contar produtos existentes
        response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 1})
        
        if response.status_code == 200:
            existing_count = response.json().get('total', 0)
            print(f"📦 Produtos existentes: {existing_count}")
        
        # Importar produtos
        print(f"\n🚀 Importando {len(products_data)} produtos...")
        
        success_count = 0
        error_count = 0
        
        for i, product in enumerate(products_data, 1):
            try:
                # Preparar payload
                payload = {
                    "name": product['name'],
                    "price": product['price'],
                    "cost": product['price'] * 0.7,  # 70% do preço
                    "unit": "un",
                    "business_type": "restaurant",
                    "track_stock": True,
                    "is_active": True,
                    "min_stock": max(1, product['stock'] // 4),
                    "category_id": category_map.get(product['category']),
                    "sku": f"RES-10-{i:03d}"
                }
                
                # Criar produto
                response = requests.post(f"{base_url}/products", headers=headers, json=payload)
                
                if response.status_code == 201:
                    product_id = response.json()['id']
                    
                    # Criar registro de estoque
                    stock_payload = {
                        "qty_on_hand": product['stock'],
                        "min_quantity": max(1, product['stock'] // 4)
                    }
                    
                    stock_response = requests.post(
                        f"{base_url}/products/{product_id}/stock", 
                        headers=headers, 
                        json=stock_payload
                    )
                    
                    print(f"✅ {i:3d}. {product['name']} - MZN {product['price']:7.2f}")
                    success_count += 1
                    
                else:
                    print(f"❌ {i:3d}. {product['name']} - ERRO: {response.status_code}")
                    if response.status_code == 422:
                        print(f"     📄 {response.text}")
                    error_count += 1
                
                # Pequena pausa para não sobrecarregar
                if i % 10 == 0:
                    print(f"   📊 Progresso: {i}/{len(products_data)}")
                    
            except Exception as e:
                print(f"❌ {i:3d}. {product['name']} - ERRO: {e}")
                error_count += 1
        
        print(f"\n" + "=" * 60)
        print(f"🎉 IMPORTAÇÃO CONCLUÍDA!")
        print(f"✅ Sucesso: {success_count} produtos")
        print(f"❌ Erros: {error_count} produtos")
        print(f"📊 Total: {success_count + error_count} produtos")
        
        if success_count > 0:
            print(f"\n🌐 Acesse o sistema em: {base_url}")
            print(f"📦 Os produtos devem aparecer agora!")
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    import_to_production()
