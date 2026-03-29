#!/usr/bin/env python3
"""
Listar todos os pontos (establishments) da empresa Mutxutxu
"""

import requests

def list_establishments():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🏢 LISTANDO PONTOS DA EMPRESA MUTXUTXU")
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
    
    # Obter informações da empresa
    print("\n🏢 INFORMAÇÕES DA EMPRESA:")
    companies_response = requests.get(f"{base_url}/companies", headers=headers)
    
    if companies_response.status_code == 200:
        companies = companies_response.json()
        for company in companies:
            print(f"   ID: {company['id']} | {company['name']}")
    
    # Obter filiais
    print(f"\n🏪 FILIAIS DA EMPRESA:")
    branches_response = requests.get(f"{base_url}/branches", headers=headers, params={"company_id": 10})
    
    if branches_response.status_code == 200:
        branches = branches_response.json()
        for branch in branches:
            print(f"   ID: {branch['id']} | {branch['name']} | Tipo: {branch['business_type']} | Ativa: {branch.get('is_active', False)}")
    
    # Obter pontos (establishments)
    print(f"\n📍 PONTOS (ESTABLISHMENTS):")
    establishments_response = requests.get(f"{base_url}/establishments", headers=headers, params={
        "company_id": 10,
        "branch_id": 94  # Filial restaurante
    })
    
    if establishments_response.status_code == 200:
        establishments = establishments_response.json()
        print(f"Total: {len(establishments)} pontos\n")
        
        for i, est in enumerate(establishments, 1):
            default_mark = "📍 [PADRÃO]" if est.get('is_default') else ""
            active_mark = "✅" if est.get('is_active') else "❌"
            
            print(f"{i}. ID: {est['id']} | {est['name']} {default_mark}")
            print(f"   Status: {active_mark} | Filial ID: {est.get('branch_id')}")
            
            # Campos adicionais se existirem
            if est.get('address'):
                print(f"   Endereço: {est['address']}")
            if est.get('phone'):
                print(f"   Telefone: {est['phone']}")
            if est.get('email'):
                print(f"   Email: {est['email']}")
            
            print()
    
    else:
        print(f"❌ Erro ao obter pontos: {establishments_response.status_code}")
        print(f"📄 Resposta: {establishments_response.text}")
    
    # Verificar também localizações de estoque
    print(f"📦 LOCALIZAÇÕES DE ESTOQUE:")
    try:
        locations_response = requests.get(f"{base_url}/stock-locations", headers=headers)
        
        if locations_response.status_code == 200:
            locations = locations_response.json()
            print(f"Total: {len(locations)} localizações\n")
            
            for i, loc in enumerate(locations, 1):
                default_mark = "📍 [PADRÃO]" if loc.get('is_default') else ""
                active_mark = "✅" if loc.get('is_active') else "❌"
                
                print(f"{i}. ID: {loc['id']} | {loc['name']} {default_mark}")
                print(f"   Tipo: {loc.get('type')} | Status: {active_mark}")
                print(f"   Empresa ID: {loc.get('company_id')} | Filial ID: {loc.get('branch_id')}")
                print()
        else:
            print(f"⚠️  Endpoint stock-locations: {locations_response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao verificar localizações: {e}")
    
    print("=" * 50)
    print("🌐 Acesse: https://neoerp-production.up.railway.app")

if __name__ == "__main__":
    list_establishments()
