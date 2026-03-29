#!/usr/bin/env python3
"""
Forçar limpeza de conexões do banco de dados
"""

import requests
import time
import concurrent.futures

def force_cleanup_connections():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🧹 FORÇANDO LIMPEZA DE CONEXÕES")
    print("=" * 50)
    
    # Estratégia 1: Tentar múltiplas requisições para forçar timeout
    print("\n🔄 ESTRATÉGIA 1: Forçar timeout das conexões")
    
    def make_request(url):
        try:
            response = requests.get(url, timeout=5)
            return f"Status: {response.status_code}"
        except requests.exceptions.Timeout:
            return "Timeout (esperado)"
        except requests.exceptions.ConnectionError:
            return "Connection Error (esperado)"
        except Exception as e:
            return f"Erro: {str(e)[:30]}..."
    
    # Fazer múltiplas requisições simultâneas para sobrecarregar e forçar limpeza
    urls = [
        f"{base_url}/health",
        f"{base_url}/",
        f"{base_url}/api/health",
        f"{base_url}/status"
    ]
    
    print("   Enviando requisições simultâneas...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_request, url) for url in urls * 5]
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            print(f"   {result}")
    
    # Estratégia 2: Tentar endpoints de admin
    print("\n🔧 ESTRATÉGIA 2: Tentar endpoints de administração")
    
    admin_endpoints = [
        f"{base_url}/admin/connections/clear",
        f"{base_url}/admin/db/reset-pool",
        f"{base_url}/debug/connections",
        f"{base_url}/system/health"
    ]
    
    for endpoint in admin_endpoints:
        try:
            print(f"   Tentando: {endpoint}")
            response = requests.post(endpoint, timeout=3)
            print(f"      Status: {response.status_code}")
            if response.status_code == 200:
                print(f"      ✅ Sucesso!")
        except Exception as e:
            print(f"      ❌ Erro: {str(e)[:30]}...")
    
    # Estratégia 3: Tentar login múltiplas vezes
    print("\n🔐 ESTRATÉGIA 3: Tentar establish novas conexões")
    
    login_attempts = 5
    for i in range(login_attempts):
        try:
            print(f"   Tentativa {i+1}/{login_attempts}")
            login = requests.post(f"{base_url}/auth/login", 
                                json={"email": "test@test.com", "password": "wrong"}, 
                                timeout=3)
            print(f"      Status: {login.status_code}")
        except Exception as e:
            print(f"      Erro (esperado): {str(e)[:30]}...")
    
    # Estratégia 4: Verificar status atual
    print("\n🔍 ESTRATÉGIA 4: Verificar status atual")
    
    try:
        print("   Verificando se sistema responde...")
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"   Status principal: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Sistema respondendo!")
        else:
            print("   ⚠️  Sistema ainda instável")
            
    except Exception as e:
        print(f"   ❌ Ainda sem resposta: {str(e)[:30]}...")
    
    # Estratégia 5: Esperar e verificar novamente
    print("\n⏱️ ESTRATÉGIA 5: Esperar e verificar recuperação")
    
    print("   Aguardando 10 segundos para recuperação...")
    time.sleep(10)
    
    try:
        print("   Verificação final...")
        response = requests.get(f"{base_url}/", timeout=15)
        print(f"   Status final: {response.status_code}")
        
        if response.status_code == 200:
            print("   🎉 SISTEMA RECUPERADO!")
        else:
            print("   ⚠️  Sistema ainda precisa de mais tempo")
            
    except Exception as e:
        print(f"   ❌ Ainda instável: {str(e)[:30]}...")
    
    print("\n" + "=" * 50)
    print("🧹 LIMPEZA FORÇADA CONCLUÍDA")
    print("💡 Se o sistema ainda estiver instável, considere:")
    print("   1. Aguardar mais 2-3 minutos")
    print("   2. Fazer restart manual no Railway")
    print("   3. Contactar suporte Railway")

if __name__ == "__main__":
    force_cleanup_connections()
