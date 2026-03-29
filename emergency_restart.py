#!/usr/bin/env python3
"""
Tentativa emergencial de restart do sistema
"""

import requests
import time

def emergency_restart():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🚨 TENTATIVA EMERGENCIAL DE RESTART")
    print("=" * 50)
    
    # Estratégia: Tentar sobrecarregar com requisições válidas para forçar restart
    print("\n🔄 SOBRECARGANDO SISTEMA PARA FORÇAR RESTART")
    
    def login_attempt():
        try:
            response = requests.post(f"{base_url}/auth/login", 
                                   json={"email": "mutxutxu@gmail.com", "password": "Mutxutxu@43"}, 
                                   timeout=2)
            return response.status_code
        except:
            return "timeout"
    
    def api_call():
        try:
            response = requests.get(f"{base_url}/products", timeout=2)
            return response.status_code
        except:
            return "timeout"
    
    # Fazer muitas tentativas rápidas
    print("   Enviando múltiplas requisições rápidas...")
    
    for i in range(20):
        print(f"   Tentativa {i+1}/20...")
        
        # Login attempt
        login_status = login_attempt()
        print(f"      Login: {login_status}")
        
        # API call
        api_status = api_call()
        print(f"      API: {api_status}")
        
        time.sleep(0.1)  # Pequena pausa
    
    print("\n⏱️ AGUARDANDO RESTART...")
    print("   Aguardando 15 segundos para o sistema restartar...")
    
    for i in range(15):
        time.sleep(1)
        print(f"   Aguardando... {15-i}s")
    
    print("\n🔍 VERIFICANDO SE SISTEMA VOLTOU:")
    
    # Verificar se sistema voltou
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            print(f"   Tentativa {attempt+1}/{max_attempts}:")
            
            # Tentar login
            login_response = requests.post(f"{base_url}/auth/login", 
                                         json={"email": "mutxutxu@gmail.com", "password": "Mutxutxu@43"}, 
                                         timeout=10)
            
            print(f"      Login Status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                print("      ✅ LOGIN FUNCIONANDO!")
                
                # Tentar API
                api_response = requests.get(f"{base_url}/products", 
                                          headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
                                          timeout=10)
                
                print(f"      API Status: {api_response.status_code}")
                
                if api_response.status_code == 200:
                    print("      ✅ API FUNCIONANDO!")
                    print("   🎉 SISTEMA TOTALMENTE RECUPERADO!")
                    return True
                else:
                    print("      ⚠️  Login ok, mas API ainda instável")
            else:
                print(f"      ❌ Login ainda falhando: {login_response.status_code}")
                
        except requests.exceptions.Timeout:
            print("      ❌ Timeout (ainda instável)")
        except Exception as e:
            print(f"      ❌ Erro: {str(e)[:30]}...")
        
        print("   Aguardando 5 segundos antes da próxima tentativa...")
        time.sleep(5)
    
    print("\n❌ SISTEMA AINDA INSTÁVEL APÓS TENTATIVAS")
    print("🔧 RECOMENDAÇÕES:")
    print("   1. Acesse Railway Dashboard e faça restart manual")
    print("   2. Verifique se há memory leaks no código")
    print("   3. Considere aumentar pool de conexões")
    
    return False

if __name__ == "__main__":
    success = emergency_restart()
    
    if success:
        print("\n🎉 SUCESSO! Sistema está operacional novamente!")
        print("🌐 Acesse: https://neoerp-production.up.railway.app")
    else:
        print("\n🚨 FALHA! Sistema precisa de intervenção manual!")
        print("🔧 Acesse Railway Dashboard para restart manual")
