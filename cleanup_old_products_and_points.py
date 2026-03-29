#!/usr/bin/env python3
"""
Limpar produtos antigos e pontos indesejados
"""

import requests

def cleanup_old_products_and_points():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🧹 LIMPANDO PRODUTOS ANTIGOS E PONTOS INDESEJADOS")
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
        
        # 1. Identificar produtos para deletar (localização 62)
        print(f"\n🗑️ IDENTIFICANDO PRODUTOS ANTIGOS PARA DELETAR:")
        products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 200})
        
        if products_response.status_code == 200:
            products_data = products_response.json()
            if isinstance(products_data, dict) and 'data' in products_data:
                products = products_data['data']
            else:
                products = products_data if isinstance(products_data, list) else []
            
            # Encontrar produtos com localização 62
            old_products = [p for p in products if p.get('default_location_id') == 62]
            
            print(f"📦 Encontrados {len(old_products)} produtos antigos:")
            for product in old_products:
                print(f"   - ID: {product['id']} | {product['name']} | Local: {product.get('default_location_id')} | Ativo: {product.get('is_active', False)}")
            
            if old_products:
                print(f"\n🗑️ DELETANDO PRODUTOS ANTIGOS...")
                deleted_count = 0
                errors_count = 0
                
                for product in old_products:
                    product_id = product['id']
                    product_name = product['name']
                    
                    print(f"   Deletando: {product_name} (ID: {product_id})")
                    
                    delete_response = requests.delete(
                        f"{base_url}/products/{product_id}",
                        headers=headers
                    )
                    
                    if delete_response.status_code in [200, 204]:
                        print(f"      ✅ Deletado com sucesso")
                        deleted_count += 1
                    else:
                        print(f"      ❌ Erro: {delete_response.status_code}")
                        errors_count += 1
                
                print(f"\n📊 RESUMO DA DELEÇÃO DE PRODUTOS:")
                print(f"   ✅ Deletados: {deleted_count}")
                print(f"   ❌ Erros: {errors_count}")
            else:
                print(f"✅ Nenhum produto antigo encontrado para deletar")
        
        # 2. Identificar e deletar pontos indesejados
        print(f"\n🏢 VERIFICANDO PONTOS (ESTABLISHMENTS):")
        establishments_response = requests.get(f"{base_url}/establishments", headers=headers, params={
            "company_id": 10,
            "branch_id": 94
        })
        
        if establishments_response.status_code == 200:
            establishments = establishments_response.json()
            print(f"📍 Total de pontos: {len(establishments)}")
            
            for est in establishments:
                is_default = est.get('is_default', False)
                is_active = est.get('is_active', False)
                status = "📍 [PADRÃO]" if is_default else ""
                active_status = "✅" if is_active else "❌"
                print(f"   ID: {est['id']} | {est['name'] or '(SEM NOME)'} | {active_status} Ativo | {status}")
            
            # Encontrar pontos indesejados (não padrão e inativos)
            unwanted_points = [est for est in establishments if not est.get('is_default', False) and not est.get('is_active', False)]
            
            if unwanted_points:
                print(f"\n🗑️ PONTOS INDESEJADOS ENCONTRADOS:")
                for point in unwanted_points:
                    print(f"   - ID: {point['id']} | {point['name'] or '(SEM NOME)'} | Inativo | Não padrão")
                
                # Tentar deletar pontos indesejados
                print(f"\n🗑️ TENTANDO DELETAR PONTOS INDESEJADOS...")
                for point in unwanted_points:
                    point_id = point['id']
                    point_name = point['name'] or '(SEM NOME)'
                    
                    print(f"   Tentando deletar: {point_name} (ID: {point_id})")
                    
                    # Tentar diferentes endpoints para deletar establishments
                    delete_response = requests.delete(
                        f"{base_url}/establishments/{point_id}",
                        headers=headers
                    )
                    
                    if delete_response.status_code in [200, 204]:
                        print(f"      ✅ Ponto deletado com sucesso")
                    elif delete_response.status_code == 404:
                        print(f"      ⚠️  Ponto não encontrado (já pode ter sido deletado)")
                    elif delete_response.status_code == 403:
                        print(f"      🔒 Sem permissão para deletar pontos")
                    elif delete_response.status_code == 422:
                        print(f"      ⚠️  Ponto não pode ser deletado (pode ter dependências)")
                        print(f"         📄 {delete_response.text}")
                    else:
                        print(f"      ❌ Erro ao deletar: {delete_response.status_code}")
                        print(f"         📄 {delete_response.text}")
            else:
                print(f"\n✅ Nenhum ponto indesejado encontrado")
        
        # 3. Verificação final
        print(f"\n🔍 VERIFICAÇÃO FINAL:")
        
        # Verificar produtos restantes
        final_products_response = requests.get(f"{base_url}/products", headers=headers, params={"limit": 50})
        if final_products_response.status_code == 200:
            final_products_data = final_products_response.json()
            if isinstance(final_products_data, dict) and 'data' in final_products_data:
                final_products = final_products_data['data']
                total_products = final_products_data.get('total', len(final_products))
            else:
                final_products = final_products_data if isinstance(final_products_data, list) else []
                total_products = len(final_products)
            
            # Verificar localizações dos produtos restantes
            location_counts = {}
            for product in final_products:
                loc_id = product.get('default_location_id')
                if loc_id:
                    location_counts[loc_id] = location_counts.get(loc_id, 0) + 1
            
            print(f"📦 Produtos restantes: {total_products}")
            print(f"📍 Localizações dos produtos:")
            for loc_id, count in location_counts.items():
                print(f"   - Localização {loc_id}: {count} produtos")
            
            if len(location_counts) == 1 and list(location_counts.keys())[0] == 63:
                print(f"✅ PERFEITO! Todos os produtos usam a localização correta (63)")
            else:
                print(f"⚠️  Ainda há múltiplas localizações")
        
        # Verificar pontos restantes
        final_establishments_response = requests.get(f"{base_url}/establishments", headers=headers, params={
            "company_id": 10,
            "branch_id": 94
        })
        
        if final_establishments_response.status_code == 200:
            final_establishments = final_establishments_response.json()
            print(f"\n🏢 Pontos restantes: {len(final_establishments)}")
            
            for est in final_establishments:
                is_default = est.get('is_default', False)
                is_active = est.get('is_active', False)
                status = "📍 [PADRÃO]" if is_default else ""
                active_status = "✅" if is_active else "❌"
                print(f"   ID: {est['id']} | {est['name'] or '(SEM NOME)'} | {active_status} | {status}")
        
        print(f"\n" + "=" * 60)
        print(f"🧹 LIMPEZA CONCLUÍDA!")
        print(f"🌐 Acesse: {base_url}")
        print(f"📦 Verifique a página de produtos no frontend")
        
    except Exception as e:
        print(f"❌ Erro durante a limpeza: {e}")

if __name__ == "__main__":
    cleanup_old_products_and_points()
