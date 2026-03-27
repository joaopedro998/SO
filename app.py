# Import Flask
from flask import Flask, request, jsonify, render_template

# Import threading para usar múltiplas threads
import threading

# Importa time para usar os delays e medir tempo
import time


# Cria a app Flask
app = Flask(__name__)


# Variável global do saldo da conta
saldo_conta = 0.0

# Lista para os logs das operações
logs = []


# Função para registrar mensagens no log
def log(msg):
    logs.append(msg)


# Função que será executada por cada thread simulando um PIX
def processar_pix(id_thread, valor_pix):

    # Usando a variavel global do saldo
    global saldo_conta
    
    # Log indicando que a thread começou
    log(f"[Thread {id_thread}] Iniciando PIX de {valor_pix}")

    # Delay de processamento para rodar todas as threads
    time.sleep(0.01)

    # Verifica se tem saldo suficiente
    if saldo_conta >= valor_pix:

        # Log do saldo OK
        log(f"[Thread {id_thread}] Saldo OK ({saldo_conta}) aguardando horário...")

        # Delay que simula o agendamento de todos os pix para o mesmo horário
        time.sleep(0.01)

        # Threads descontando o valor do pix diretamente do saldo lido por elas
        saldo_conta -= valor_pix

        # Log mostrando novo saldo
        log(f"[Thread {id_thread}] PIX enviado. Novo saldo: {saldo_conta}")

    else:
        # Caso não tenha saldo suficiente
        log(f"[Thread {id_thread}] ERRO saldo insuficiente")


# Rota principal do site
@app.route("/")
def home():

    # Arquivo HTML da interface
    return render_template("index.html")


# Rota que executa a simulação
@app.route("/executar", methods=["POST"])
def executar():

    # Indicando variaveis globais do saldo e logs
    global saldo_conta, logs
    
    # Limpando a lista de logs
    logs = []

    # ⏱️ INÍCIO DA MEDIÇÃO DE TEMPO
    inicio = time.time()
    
    # Recebe os dados inseridos em JSON
    data = request.json
    
    # Define o saldo inicial da conta
    saldo_conta = float(data["saldo"])

    # Valor de cada PIX
    valor_pix = float(data["valor"])

    # Quantidade de PIX ao mesmo tempo
    qtd = int(data["qtd"])


    # Lista para armazenar as threads
    threads = []


    # Cria várias threads simulando vários PIX ao mesmo tempo
    for i in range(qtd):

        # Cria a thread
        t = threading.Thread(
            target=processar_pix,
            args=(i+1, valor_pix)
        )

        # Adiciona na lista
        threads.append(t)

        # Inicia a thread
        t.start()


    # Aguarda todas as threads terminarem
    for t in threads:
        t.join()


    # ⏱️ FIM DA MEDIÇÃO DE TEMPO
    fim = time.time()

    # ⏱️ CÁLCULO DO TEMPO TOTAL DE EXECUÇÃO
    tempo_execucao = fim - inicio


    # Retorna resultado para o frontend
    return jsonify({

        # Retorna os logs das threads
        "logs": logs,

        # Retorna saldo final da conta
        "saldo_final": saldo_conta,

        # Retorna tempo total de execução (arredondado)
        "tempo_execucao": round(tempo_execucao, 4)
    })


# Inicia o servidor Flask
app.run(debug=True)
