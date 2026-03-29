#!/usr/bin/env python3
"""
Debug da autenticação
"""

import requests

def debug_auth():
    base_url = "https://neoerp-production.up.railway.app"
    
    print("🔍 DEBUG DA AUTENTICAÇÃO")
    print("=" * 40)
    
    # Login
    login_response = requests.post(f"{base_url}/auth/login", json={
        "email": "mutxutxu@gmail.com", 
        "password": "Mutxutxu@43"
    })
    
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"Erro login: {login_response.text}")
        return
    
    login_data = login_response.json()
    print(f"Login response: {login_data}")
    
    token = login_data.get('access_token') or login_data.get('token')
    print(f"Token: {token[:50] if token else 'NONE'}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Testar endpoints
    endpoints = [
        "/auth/me",
        "/stock-locations",
        "/product-categories"
    ]
    
    for endpoint in endpoints:
        try:
            resp = requests.get(f"{base_url}{endpoint}", headers=headers)
            print(f"{endpoint}: {resp.status_code}")
            if resp.status_code != 200:
                print(f"  Erro: {resp.text}")
        except Exception as e:
            print(f"{endpoint}: ERRO - {e}")

if __name__ == "__main__":
    debug_auth()
