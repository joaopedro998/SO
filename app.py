from flask import Flask, request, jsonify, render_template
import threading
import time

app = Flask(__name__)

saldo_conta = 0.0
logs = []

def log(msg):
    logs.append(msg)

def processar_pix(id_thread, valor_pix):
    global saldo_conta
    
    log(f"[Thread {id_thread}] Iniciando PIX de {valor_pix}")
    time.sleep(0.5)

    if saldo_conta >= valor_pix:
        log(f"[Thread {id_thread}] Saldo OK ({saldo_conta}) aguardando horário...")
        time.sleep(3)

        saldo_conta -= valor_pix
        log(f"[Thread {id_thread}] PIX enviado. Novo saldo: {saldo_conta}")
    else:
        log(f"[Thread {id_thread}] ERRO saldo insuficiente")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/executar", methods=["POST"])
def executar():
    global saldo_conta, logs
    
    logs = []
    
    data = request.json
    
    saldo_conta = float(data["saldo"])
    valor_pix = float(data["valor"])
    qtd = int(data["qtd"])

    threads = []

    for i in range(qtd):
        t = threading.Thread(target=processar_pix, args=(i+1, valor_pix))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return jsonify({
        "logs": logs,
        "saldo_final": saldo_conta
    })

app.run(debug=True)