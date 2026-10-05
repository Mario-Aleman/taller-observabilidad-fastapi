"""Prueba de saturación: ¿qué le pasa a un endpoint sano (GET /) cuando la API
externa se cuelga y llegan muchas solicitudes POST?
    python evidencias/saturacion.py <carpeta_app> <etiqueta>
"""
import json
import os
import sys
import threading
import time

sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2]]
import medir_rendimiento as m  # noqa: E402  (reutiliza utilidades)

N_POST = 45  # > 40 hilos que usa Starlette por defecto para endpoints síncronos
m.servidor_falso(9002, 12)
m.preparar_bd()
app = m.levantar_app("http://127.0.0.1:9002/users")
cuerpo = {"nombre": "Prueba", "programa": "Sistemas", "semestre": 4, "promedio": 4.0}
try:
    base = m.medir("GET", "/", 5)["prom"]
    hilos = [threading.Thread(target=lambda: m.requests.post(
        f"http://127.0.0.1:{m.PUERTO_APP}/estudiantes/", json=cuerpo, timeout=60))
        for _ in range(N_POST)]
    [h.start() for h in hilos]
    time.sleep(1.5)  # los POST ya ocupan los hilos del servidor
    t = time.perf_counter()
    r = m.requests.get(f"http://127.0.0.1:{m.PUERTO_APP}/", timeout=60)
    espera = time.perf_counter() - t
    [h.join() for h in hilos]
    res = {"etiqueta": sys.argv[2], "post_concurrentes": N_POST,
           "get_raiz_normal_s": round(base, 4),
           "get_raiz_durante_saturacion_s": round(espera, 3), "codigo": r.status_code}
    print(json.dumps(res, indent=2))
    os.makedirs("resultados", exist_ok=True)
    json.dump(res, open(f"resultados/saturacion_{sys.argv[2]}.json", "w"), indent=2)
finally:
    app.terminate()
    app.wait()
