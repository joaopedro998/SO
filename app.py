# =========================
# IMPORTS
# =========================
# Flask → cria a API/web
# threading → permite executar várias tarefas ao mesmo tempo (threads)
# time → simula tempo de processamento
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
# saldo_conta → recurso compartilhado entre threads (ponto crítico!)
# logs → lista de mensagens exibidas no front
saldo_conta = 0.0
logs = []


# =========================
# LOCKS (CONTROLE DE CONCORRÊNCIA)
# =========================
# lock → protege o saldo (evita race condition)
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
# CLASSE TAREFA
# =========================
# Representa um PIX
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

    # ID da thread atual (apenas para log)
    worker_id = threading.get_ident()

    # Tempo proporcional ao valor (simula processamento)
    tempo_processamento = tarefa.valor / 2000

    log(f"[Worker {worker_id}] ▶ Executando T{tarefa.id} (R${tarefa.valor})")
    log(f"[Worker {worker_id}] ⏱ Tempo estimado: {tempo_processamento:.2f}s")

    # Simula tempo de execução
    time.sleep(tempo_processamento)

    # Se lock ativado → protege região crítica
    if usar_lock:
        lock.acquire()

    try:
        # Região crítica (acesso ao saldo compartilhado)
        if saldo_conta >= tarefa.valor:
            saldo_conta -= tarefa.valor
            log(f"[Worker {worker_id}] ✔ T{tarefa.id} concluída → saldo: {saldo_conta}")
        else:
            log(f"[Worker {worker_id}] ❌ T{tarefa.id} falhou (saldo insuficiente)")

    finally:
        # Libera lock
        if usar_lock:
            lock.release()


# =========================
# WORKER (THREAD CONSUMIDORA)
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
    # CABEÇALHO (LOG VISUAL)
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

    for _ in range(5):  # 5 workers concorrentes
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
