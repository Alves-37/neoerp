#!/usr/bin/env python3
"""
Usar establishments como localizações para identificar loja vs armazém
"""

import requests

def check_establishments_as_locations():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🔍 VERIFICANDO ESTABLISHMENTS COMO LOCALIZAÇÕES")
    print("=" * 60)
    
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
        
        # 1. Verificar establishments disponíveis
        print(f"\n🏢 ESTABLISHMENTS DISPONÍVEIS:")
        establishments_response = requests.get(f"{base_url}/establishments", headers=headers, params={
            "company_id": 10,
            "branch_id": 94
        })
        
        if establishments_response.status_code == 200:
            establishments = establishments_response.json()
            print(f"Total: {len(establishments)} establishments")
            
            for est in establishments:
                is_default = est.get('is_default', False)
                is_active = est.get('is_active', False)
                est_id = est['id']
                est_name = est.get('name', 'Sem nome')
                
                status = "📍 [PADRÃO]" if is_default else ""
                active = "✅" if is_active else "❌"
                
                print(f"   ID: {est_id} | {est_name} | {active} Ativo | {status}")
        
        # 2. Verificar distribuição de produtos por establishment
        print(f"\n📦 DISTRIBUIÇÃO DE PRODUTOS POR ESTABLISHMENT:")
        products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 200})
        
        if products_response.status_code == 200:
            products_data = products_response.json()
            if isinstance(products_data, dict) and 'data' in products_data:
                products = products_data['data']
            else:
                products = products_data if isinstance(products_data, list) else []
            
            # Agrupar por establishment_id e default_location_id
            establishment_counts = {}
            location_counts = {}
            
            for product in products:
                est_id = product.get('establishment_id')
                loc_id = product.get('default_location_id')
                
                if est_id:
                    establishment_counts[est_id] = establishment_counts.get(est_id, 0) + 1
                if loc_id:
                    location_counts[loc_id] = location_counts.get(loc_id, 0) + 1
            
            print(f"\n📊 Produtos por Establishment:")
            for est_id, count in establishment_counts.items():
                # Encontrar nome do establishment
                est_name = "Unknown"
                for est in establishments:
                    if est['id'] == est_id:
                        est_name = est.get('name', 'Sem nome')
                        break
                
                is_default = "📍 [PADRÃO]" if any(e['id'] == est_id and e.get('is_default') for e in establishments) else ""
                print(f"   Establishment ID {est_id} ({est_name}): {count} produtos {is_default}")
            
            print(f"\n📊 Produtos por Localização (default_location_id):")
            for loc_id, count in location_counts.items():
                print(f"   Localização ID {loc_id}: {count} produtos")
                
                # Verificar se corresponde a algum establishment
                matching_est = None
                for est in establishments:
                    if est['id'] == loc_id:
                        matching_est = est
                        break
                
                if matching_est:
                    is_default = "📍 [PADRÃO]" if matching_est.get('is_default') else ""
                    print(f"      ↔️ Corresponde a: {matching_est.get('name', 'Sem nome')} {is_default}")
        
        # 3. Verificar estoques por localização
        print(f"\n📦 VERIFICANDO ESTOQUES:")
        stocks_response = requests.get(f"{base_url}/product-stocks", headers=headers, params={"limit": 50})
        
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
            for loc_id, count in stock_location_counts.items():
                print(f"   Localização ID {loc_id}: {count} registros de estoque")
        
        # 4. Análise e recomendações
        print(f"\n🔍 ANÁLISE E RECOMENDAÇÕES:")
        
        # Identificar o establishment padrão
        default_establishment = None
        for est in establishments:
            if est.get('is_default'):
                default_establishment = est
                break
        
        if default_establishment:
            print(f"✅ Establishment padrão: {default_establishment.get('name')} (ID: {default_establishment['id']})")
            
            # Verificar se os produtos estão no establishment padrão
            default_est_products = establishment_counts.get(default_establishment['id'], 0)
            total_products = sum(establishment_counts.values())
            
            if default_est_products == total_products:
                print(f"✅ Todos os produtos estão no establishment padrão")
            else:
                print(f"⚠️  Apenas {default_est_products}/{total_products} produtos estão no establishment padrão")
                
                # Sugerir correção
                non_default_ests = [eid for eid in establishment_counts.keys() if eid != default_establishment['id']]
                if non_default_ests:
                    print(f"🔧 Produtos em outros establishments:")
                    for est_id in non_default_ests:
                        est_name = "Unknown"
                        for est in establishments:
                            if est['id'] == est_id:
                                est_name = est.get('name', 'Sem nome')
                                break
                        count = establishment_counts[est_id]
                        print(f"   - {est_name} (ID: {est_id}): {count} produtos")
                    
                    print(f"\n💡 RECOMENDAÇÃO:")
                    print(f"   Mover todos os produtos para: {default_establishment.get('name')} (ID: {default_establishment['id']})")
        
        print(f"\n" + "=" * 60)
        print("🌐 Acesse: https://neoerp-production.up.railway.app")
        
    except Exception as e:
        print(f"❌ Erro durante verificação: {e}")

if __name__ == "__main__":
    check_establishments_as_locations()
