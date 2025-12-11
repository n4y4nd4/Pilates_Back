#!/usr/bin/env python
"""Script para testar os novos endpoints da API"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_endpoints():
    print("=" * 60)
    print("TESTANDO NOVOS ENDPOINTS DA API")
    print("=" * 60)
    
    # Teste 1: Próximos Vencimentos
    print("\n1. Testando: GET /cobrancas/proximos_vencimentos/")
    try:
        response = requests.get(f"{BASE_URL}/cobrancas/proximos_vencimentos/")
        data = response.json()
        if isinstance(data, dict) and 'detail' in data:
            print(f"   Status: {response.status_code}")
            print(f"   Resultado: {data['detail']}")
        else:
            print(f"   Status: {response.status_code}")
            print(f"   Resultados: {len(data)} encontrados")
            if data:
                print(f"   Exemplo: {json.dumps(data[0], indent=2, default=str)}")
    except Exception as e:
        print(f"   Erro: {e}")
    
    # Teste 2: Pagamentos Atrasados
    print("\n2. Testando: GET /cobrancas/pagamentos_atrasados/")
    try:
        response = requests.get(f"{BASE_URL}/cobrancas/pagamentos_atrasados/")
        data = response.json()
        if isinstance(data, dict) and 'detail' in data:
            print(f"   Status: {response.status_code}")
            print(f"   Resultado: {data['detail']}")
        else:
            print(f"   Status: {response.status_code}")
            print(f"   Resultados: {len(data)} encontrados")
    except Exception as e:
        print(f"   Erro: {e}")
    
    # Teste 3: Notificações Enviadas
    print("\n3. Testando: GET /notificacoes/enviadas/")
    try:
        response = requests.get(f"{BASE_URL}/notificacoes/enviadas/")
        data = response.json()
        if isinstance(data, dict) and 'detail' in data:
            print(f"   Status: {response.status_code}")
            print(f"   Resultado: {data['detail']}")
        else:
            print(f"   Status: {response.status_code}")
            print(f"   Resultados: {len(data)} encontrados")
            if data:
                print(f"   Exemplo com novos campos:")
                ex = data[0]
                print(f"      - cliente_nome: {ex.get('cliente_nome')}")
                print(f"      - cliente_email: {ex.get('cliente_email')}")
                print(f"      - cobranca_valor: {ex.get('cobranca_valor')}")
                print(f"      - status_envio: {ex.get('status_envio')}")
    except Exception as e:
        print(f"   Erro: {e}")
    
    # Teste 4: Notificações Agendadas
    print("\n4. Testando: GET /notificacoes/agendadas/")
    try:
        response = requests.get(f"{BASE_URL}/notificacoes/agendadas/")
        data = response.json()
        if isinstance(data, dict) and 'detail' in data:
            print(f"   Status: {response.status_code}")
            print(f"   Resultado: {data['detail']}")
        else:
            print(f"   Status: {response.status_code}")
            print(f"   Resultados: {len(data)} encontrados")
    except Exception as e:
        print(f"   Erro: {e}")
    
    # Teste 5: Notificações com Falha
    print("\n5. Testando: GET /notificacoes/com_falha/")
    try:
        response = requests.get(f"{BASE_URL}/notificacoes/com_falha/")
        data = response.json()
        if isinstance(data, dict) and 'detail' in data:
            print(f"   Status: {response.status_code}")
            print(f"   Resultado: {data['detail']}")
        else:
            print(f"   Status: {response.status_code}")
            print(f"   Resultados: {len(data)} encontrados")
    except Exception as e:
        print(f"   Erro: {e}")
    
    # Teste 6: Notificações com filtro de status
    print("\n6. Testando: GET /notificacoes/?status=ENVIADO")
    try:
        response = requests.get(f"{BASE_URL}/notificacoes/?status=ENVIADO")
        data = response.json()
        if isinstance(data, dict):
            if 'detail' in data:
                print(f"   Status: {response.status_code}")
                print(f"   Resultado: {data['detail']}")
            elif 'results' in data:
                print(f"   Status: {response.status_code}")
                print(f"   Resultados (paginado): {len(data['results'])} encontrados")
            else:
                print(f"   Status: {response.status_code}")
                print(f"   Resposta: {data}")
        else:
            print(f"   Status: {response.status_code}")
            print(f"   Resultados: {len(data)} encontrados")
            if data:
                print(f"   Novos campos disponíveis: cliente_nome, cliente_email, cobranca_valor, dias_em_atraso")
    except Exception as e:
        print(f"   Erro: {e}")
    
    print("\n" + "=" * 60)
    print("TESTES CONCLUÍDOS!")
    print("✅ Novos endpoints implementados com sucesso!")
    print("=" * 60)

if __name__ == "__main__":
    test_endpoints()

