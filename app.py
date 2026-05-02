# =========================
# IMPORTS
# =========================
# Flask → cria a WEB
# threading → permite executar várias threads
# time → simulação do tempo dos processos
# heapq → estrutura de fila de prioridade (usada no SJF e PS)
from flask import Flask, request, jsonify, render_template
import threading
import time
import heapq


# =========================
# INICIALIZAÇÃO DO APP
# =========================
app = Flask(__name__)


# =========================
# VARIÁVEIS GLOBAIS
# =========================
# saldo_conta → variavel do saldo da conta
# logs → lista de mensagens exibidas
saldo_conta = 0.0
logs = []


# =========================
# LOCKS
# =========================
# lock → protege o saldo (evita race condition quando habilitado)
# fila_lock → protege o acesso à fila (evita duas threads pegarem a mesma tarefa)
lock = threading.Lock()
fila_lock = threading.Lock()


# =========================
# CENÁRIOS PRONTOS
# =========================
# Cada cenário representa vários PIX a serem executados
CENARIOS = {
    "cenario1": [500, 350, 175, 100],
    "cenario2": [10, 10, 10, 10, 10],
    "cenario3": [800, 50, 60, 70, 1000]
}


# =========================
# FUNÇÃO DE LOG
# =========================
# Centraliza os logs para facilitar exibição no front
def log(msg):
    logs.append(msg)


# =========================
# CLASSE TAREFA (PIX)
# =========================
class Tarefa:
    def __init__(self, id, valor, prioridade):
        self.id = id              # identificador da tarefa
        self.valor = valor        # valor do PIX
        self.prioridade = prioridade  # usado no heap (SJF ou PS)

    # Define como comparar tarefas (necessário para heapq)
    def __lt__(self, other):
        return self.prioridade < other.prioridade


# =========================
# PROCESSAMENTO DO PIX
# =========================
def processar_pix(tarefa, usar_lock):
    global saldo_conta
    worker_id = threading.get_ident()
    tempo_processamento = tarefa.valor / 2000

    log(f"[Worker {worker_id}] ▶ Executando T{tarefa.id} (R${tarefa.valor})")

    if usar_lock:
        lock.acquire()

    try:
        # Garantia que a thread fique esperando a de maior prioridade terminar antes
        time.sleep(tempo_processamento)

        if saldo_conta >= tarefa.valor:
            # Sleep para o cenario caotico garantir o bug de concorrencia
            time.sleep(0.5) 
            
            saldo_conta -= tarefa.valor
            log(f"[Worker {worker_id}] ✔ T{tarefa.id} concluída → saldo: {saldo_conta:.2f}")
        else:
            log(f"[Worker {worker_id}] ❌ T{tarefa.id} falhou (saldo insuficiente)")

    finally:
        if usar_lock:
            lock.release()


# =========================
# WORKER
# =========================
def worker(fila, algoritmo, usar_lock):

    worker_id = threading.get_ident()

    log(f"[Worker {worker_id}] 🟢 iniciado")

    while True:
        # Protege acesso à fila
        with fila_lock:

            # Se não tem mais tarefas → thread encerra
            if not fila:
                log(f"[Worker {worker_id}] 🔴 fila vazia → encerrando")
                return

            # Seleção da tarefa conforme algoritmo
            if algoritmo == "fcfs":
                tarefa = fila.pop(0)           # ordem de chegada
            else:
                tarefa = heapq.heappop(fila)  # menor prioridade primeiro

            log(f"[Worker {worker_id}] → pegou T{tarefa.id} (R${tarefa.valor})")

        # Processa fora do lock da fila (importante!)
        processar_pix(tarefa, usar_lock)


# =========================
# ROTAS
# =========================

# Página principal
@app.route("/")
def home():
    return render_template("index.html")


# Execução da simulação
@app.route("/executar", methods=["POST"])
def executar():

    global saldo_conta, logs

    logs = []
    inicio = time.time()

    data = request.json

    # Define saldo inicial
    saldo_conta = float(data["saldo"])

    # Escolhe cenário
    cenario = data.get("cenario", "cenario1")
    valores = CENARIOS.get(cenario, CENARIOS["cenario1"])

    algoritmo = data.get("algoritmo", "fcfs")
    usar_lock = data.get("lock", True)

    fila = []

    # =========================
    # CABEÇALHO do LOG
    # =========================
    log("===================================")
    log(f"🚀 CENÁRIO: {cenario.upper()}")
    log(f"🧠 ALGORITMO: {algoritmo.upper()}")
    log(f"🔒 LOCK: {'ATIVO' if usar_lock else 'DESATIVADO'}")
    log("===================================\n")

    # =========================
    # CRIAÇÃO DAS TAREFAS
    # =========================
    for i, valor in enumerate(valores):

        valor = float(valor)

        # Define prioridade conforme algoritmo
        if algoritmo == "sjf":
            prioridade = valor          # menor valor primeiro
        elif algoritmo == "ps":
            prioridade = -valor         # maior valor primeiro
        else:
            prioridade = i              # FCFS

        tarefa = Tarefa(i + 1, valor, prioridade)

        # Insere na fila
        if algoritmo == "fcfs":
            fila.append(tarefa)
        else:
            heapq.heappush(fila, tarefa)

    # =========================
    # VISUALIZAÇÃO DA FILA
    # =========================
    log("📦 FILA (ORDEM DE EXECUÇÃO)")
    log("-----------------------------------")

    if algoritmo == "fcfs":
        for t in fila:
            log(f"→ T{t.id} | R${t.valor}")
    else:
        # Copia para não destruir a fila original
        fila_temp = fila.copy()
        heapq.heapify(fila_temp)

        while fila_temp:
            t = heapq.heappop(fila_temp)
            log(f"→ T{t.id} | R${t.valor}")

    log("\n⚙️ INICIANDO WORKERS")
    log("-----------------------------------")

    # =========================
    # CRIAÇÃO DAS THREADS
    # =========================
    threads = []

    for _ in range(5):  # 5 workers (Com base no numero de valores que temos em casa cenário padrão)
        t = threading.Thread(target=worker, args=(fila, algoritmo, usar_lock))
        threads.append(t)
        t.start()

    # Aguarda todas terminarem
    for t in threads:
        t.join()

    fim = time.time()

    # =========================
    # RESULTADO FINAL
    # =========================
    log("\n===================================")
    log(f"💰 SALDO FINAL: {saldo_conta}")
    log(f"⏱ TEMPO TOTAL: {round(fim - inicio, 4)}s")
    log("===================================")

    return jsonify({
        "logs": logs,
        "saldo_final": saldo_conta,
        "tempo_execucao": round(fim - inicio, 4)
    })


# =========================
# START
# =========================
app.run(debug=False)
