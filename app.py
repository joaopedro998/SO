# =========================
# IMPORTS
# =========================
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
saldo_conta = 0.0
logs = []


# =========================
# LOCKS
# =========================
lock = threading.Lock()
fila_lock = threading.Lock()


# =========================
# CENÁRIOS PRONTOS
# =========================
CENARIOS = {
    "cenario1": [500, 350, 175, 100],
    "cenario2": [100, 200, 300, 400, 50],
    "cenario3": [800, 50, 60, 70, 1000]
}


# =========================
# FUNÇÃO DE LOG
# =========================
def log(msg):
    logs.append(msg)


# =========================
# CLASSE TAREFA
# =========================
class Tarefa:
    def __init__(self, id, valor, prioridade):
        self.id = id
        self.valor = valor
        self.prioridade = prioridade

    def __lt__(self, other):
        return self.prioridade < other.prioridade


# =========================
# PROCESSAMENTO DO PIX
# =========================
def processar_pix(tarefa, usar_lock):
    global saldo_conta

    # Tempo proporcional ao valor
    tempo_processamento = tarefa.valor / 2000

    log(f"[Thread {tarefa.id}] Iniciando PIX de {tarefa.valor}")
    log(f"[Thread {tarefa.id}] Tempo estimado: {tempo_processamento:.2f}s")

    time.sleep(tempo_processamento)

    if usar_lock:
        lock.acquire()

    try:
        if saldo_conta >= tarefa.valor:
            log(f"[Thread {tarefa.id}] Saldo OK ({saldo_conta})")

            time.sleep(tempo_processamento)

            saldo_conta -= tarefa.valor

            log(f"[Thread {tarefa.id}] PIX enviado. Novo saldo: {saldo_conta}")
        else:
            log(f"[Thread {tarefa.id}] ERRO saldo insuficiente")

    finally:
        if usar_lock:
            lock.release()


# =========================
# WORKER
# =========================
def worker(fila, algoritmo, usar_lock):

    while True:
        with fila_lock:

            if not fila:
                return

            if algoritmo == "fcfs":
                tarefa = fila.pop(0)
            else:
                tarefa = heapq.heappop(fila)

            # 🔥 LOG DO ESCALONADOR
            log(f"[ESCALONADOR] Tarefa {tarefa.id} selecionada (valor {tarefa.valor})")

        processar_pix(tarefa, usar_lock)


# =========================
# ROTAS
# =========================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/executar", methods=["POST"])
def executar():

    global saldo_conta, logs

    logs = []
    inicio = time.time()

    data = request.json

    saldo_conta = float(data["saldo"])

    # 🔥 USO DE CENÁRIO
    cenario = data.get("cenario", "cenario1")
    valores = CENARIOS.get(cenario, CENARIOS["cenario1"])

    algoritmo = data.get("algoritmo", "fcfs")
    usar_lock = data.get("lock", True)

    fila = []

    # =========================
    # CRIAÇÃO DAS TAREFAS
    # =========================
    for i, valor in enumerate(valores):

        valor = float(valor)  # 🔥 CORREÇÃO IMPORTANTE

        if algoritmo == "sjf":
            prioridade = valor  # menor primeiro

        elif algoritmo == "ps":
            prioridade = -valor  # maior primeiro

        else:
            prioridade = i  # ordem de chegada

        tarefa = Tarefa(i + 1, valor, prioridade)

        if algoritmo == "fcfs":
            fila.append(tarefa)
        else:
            heapq.heappush(fila, tarefa)

    # 🔥 DEBUG (mostra ordem da fila antes de executar)
    log("\n[DEBUG] Ordem inicial da fila:")
    if algoritmo == "fcfs":
        for t in fila:
            log(f"→ Tarefa {t.id} | Valor {t.valor}")
    else:
        fila_temp = fila.copy()
        heapq.heapify(fila_temp)
        while fila_temp:
            t = heapq.heappop(fila_temp)
            log(f"→ Tarefa {t.id} | Valor {t.valor}")

    # =========================
    # THREADS
    # =========================
    threads = []

    for _ in range(5):
        t = threading.Thread(target=worker, args=(fila, algoritmo, usar_lock))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    fim = time.time()

    return jsonify({
        "logs": logs,
        "saldo_final": saldo_conta,
        "tempo_execucao": round(fim - inicio, 4)
    })


# =========================
# START
# =========================
app.run(debug=False)
