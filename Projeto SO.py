import threading
import time

saldo_conta = 0.0

def processar_pix(id_thread, valor_pix):
    global saldo_conta
    
    print(f"[Thread {id_thread}] Iniciando verificação... PIX agendado de R${valor_pix:.2f}")
    time.sleep(0.5) 
    
    if saldo_conta >= valor_pix:
        print(f"[Thread {id_thread}] OK! Saldo lido: R${saldo_conta:.2f} >= R${valor_pix:.2f}. Aguardando horário...")
        
        time.sleep(3) 
        
        # O DESCONTO
        saldo_conta = saldo_conta - valor_pix
        print(f"[Thread {id_thread}] HORÁRIO ATINGIDO! PIX enviado. Novo saldo: R${saldo_conta:.2f}")
    else:
        print(f"[Thread {id_thread}] ERRO: Saldo de R${saldo_conta:.2f} é insuficiente para o PIX de R${valor_pix:.2f}.")

def main():
    global saldo_conta
    
    print("="*50)
    print("      CONFIGURAÇÃO DO AMBIENTE DE TESTE (BURLA)")
    print("="*50)
    
    try:
        saldo_conta = float(input("Digite o saldo inicial da conta (ex: 150): "))
        valor_pix = float(input("Digite o valor de CADA PIX agendado (ex: 100): "))
        qtd_pix = int(input("Digite a quantidade de PIX simultâneos (ex: 5): "))
    except ValueError:
        print("Por favor, digite apenas números válidos.")
        return

    # Montando o vetor de agendamentos dinamicamente
    agendamentos_pix = [valor_pix] * qtd_pix

    print("\n" + "="*50)
    print("           SISTEMA BANCÁRIO INICIADO")
    print(f"           SALDO INICIAL: R$ {saldo_conta:.2f}")
    print("="*50)
    print(f"\n[SISTEMA] Processando vetor com {qtd_pix} agendamentos PIX...\n")
    
    threads = []
    
    for i, valor in enumerate(agendamentos_pix):
        t = threading.Thread(target=processar_pix, args=(i+1, valor))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    # 3. RESULTADO FINAL
    print("\n" + "="*50)
    print("                RELATÓRIO FINAL")
    print(f"           SALDO FINAL DA CONTA: R$ {saldo_conta:.2f}")
    
    if saldo_conta < 0:
        print("    [ALERTA CRÍTICO] SISTEMA BURLADO! SALDO NEGATIVO.")
    else:
        print("    [INFO] Sistema operou dentro da normalidade.")
    print("="*50)

if __name__ == "__main__":
    main()