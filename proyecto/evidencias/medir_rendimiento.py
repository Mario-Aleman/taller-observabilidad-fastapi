"""Mide el rendimiento REAL de la app contra un servidor uvicorn local.

Uso (desde la raíz del proyecto):
    python pruebas_rendimiento/medir_rendimiento.py <carpeta_app> <etiqueta> [url_api_externa]

Los datos NO se inventan: cada tiempo sale de una solicitud HTTP real.
La API externa se reemplaza por servidores locales controlados (latencia fija
y "colgado") para poder probar el timeout de forma reproducible.
"""
import json
import os
import socket
import sqlite3
import statistics
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests

CARPETA, ETIQUETA = sys.argv[1], sys.argv[2]
PUERTO_APP = 8765


def servidor_falso(puerto, demora):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            time.sleep(demora)
            cuerpo = json.dumps([{"id": 1, "name": "Usuario simulado"}]).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def log_message(self, *a):
            pass
    srv = ThreadingHTTPServer(("127.0.0.1", puerto), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def preparar_bd():
    ruta = os.path.join(CARPETA, "academico.db")
    if os.path.exists(ruta):
        os.remove(ruta)
    con = sqlite3.connect(ruta)
    con.execute("""CREATE TABLE IF NOT EXISTS estudiantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL,
        programa TEXT NOT NULL, semestre INTEGER NOT NULL, promedio REAL NOT NULL)""")
    con.executemany(
        "INSERT INTO estudiantes(nombre,programa,semestre,promedio) VALUES (?,?,?,?)",
        [(f"Estudiante {i}", "Sistemas", 1 + i % 10, 3.0 + (i % 20) / 10)
         for i in range(2000)])
    con.commit()
    con.close()


def levantar_app(url_externa):
    env = {**os.environ, "API_EXTERNA_URL": url_externa}
    p = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", str(PUERTO_APP),
         "--log-level", "warning"], cwd=CARPETA, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", PUERTO_APP), 0.2).close()
            return p
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("La app no arrancó")


def medir(metodo, ruta, n, json_body=None):
    tiempos, codigos = [], set()
    for _ in range(n):
        t = time.perf_counter()
        r = requests.request(metodo, f"http://127.0.0.1:{PUERTO_APP}{ruta}",
                             json=json_body, timeout=60)
        tiempos.append(time.perf_counter() - t)
        codigos.add(r.status_code)
    return {"endpoint": ruta, "metodo": metodo, "n": n,
            "min": min(tiempos), "max": max(tiempos),
            "prom": statistics.mean(tiempos),
            "codigos": sorted(codigos)}


def carga(n_hilos, ruta="/estudiantes/"):
    tiempos, lock = [], threading.Lock()

    def uno():
        t = time.perf_counter()
        requests.get(f"http://127.0.0.1:{PUERTO_APP}{ruta}", timeout=60)
        with lock:
            tiempos.append(time.perf_counter() - t)
    hilos = [threading.Thread(target=uno) for _ in range(n_hilos)]
    ini = time.perf_counter()
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    return {"hilos": n_hilos, "total": time.perf_counter() - ini,
            "min": min(tiempos), "max": max(tiempos),
            "prom": statistics.mean(tiempos)}


if __name__ == "__main__":
    ok = servidor_falso(9001, 0.2)       # API externa lenta pero sana
    colgada = servidor_falso(9002, 12)   # API externa "colgada" (12 s)
    cuerpo = {"nombre": "Prueba", "programa": "Sistemas",
              "semestre": 4, "promedio": 4.0}
    resultado = {"etiqueta": ETIQUETA, "escenarios": []}

    preparar_bd()
    app = levantar_app("http://127.0.0.1:9001/users")
    try:
        resultado["escenarios"] += [
            medir("GET", "/", 30),
            medir("GET", "/estudiantes/", 30),
            medir("GET", "/estudiantes/1000", 30),
            medir("POST", "/estudiantes/", 30, cuerpo),
        ]
        resultado["carga"] = [carga(10), carga(50)]
    finally:
        app.terminate()
        app.wait()

    # Escenario: API externa colgada (12 s). Pocas repeticiones por ser lento.
    preparar_bd()
    app = levantar_app("http://127.0.0.1:9002/users")
    try:
        r = medir("POST", "/estudiantes/", 3, cuerpo)
        r["endpoint"] = "/estudiantes/ (API externa colgada 12 s)"
        resultado["escenarios"].append(r)
    finally:
        app.terminate()
        app.wait()

    os.makedirs("resultados", exist_ok=True)
    with open(f"resultados/rendimiento_{ETIQUETA}.json", "w") as f:
        json.dump(resultado, f, indent=2)
    print(json.dumps(resultado, indent=2))
