"""Evalua el dataset de audio: transcripcion, montos, latencia y costo.

Uso:
    py -3 tools/evaluar_dataset.py

Recorre ``datasets/eval_audio/manifest.csv``, transcribe cada clip con el
proveedor configurado y compara contra la verdad conocida. Genera un reporte
con WER, exactitud de montos, exactitud de intención y latencia.
"""

import argparse
import csv
import json
import re
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend import ai, nlp  # noqa: E402

DATASET = ROOT / "datasets" / "eval_audio"
MANIFEST = DATASET / "manifest.csv"
REPORTE = DATASET / "reporte.json"
UMBRAL_WER = 0.15
UMBRAL_MONTOS = 0.90
UMBRAL_INTENCION = 0.90


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluar el dataset de audio")
    parser.add_argument("--modelo", default=None, help="Modelo de Gemini a probar")
    parser.add_argument("--sin-wer", action="store_true", help="No calcular el WER")
    parser.add_argument(
        "--audio-dir",
        default=None,
        help="Carpeta alterna de audio (por defecto datasets/eval_audio/audio)",
    )
    parser.add_argument(
        "--pausa",
        type=float,
        default=2.0,
        help="Pausa entre clips para respetar la cuota de la capa gratuita",
    )
    return parser.parse_args()


def normalizar(texto):
    return nlp.normalize(texto)


def normalizar_para_wer(texto):
    """Normaliza para comparar textos: sin tildes, sin puntuacion y con los
    montos en un mismo formato (5 mil, 5.000, 5,000 y 5000 son el mismo numero)."""
    limpio = nlp.normalize(texto)
    limpio = re.sub(r"[^\w\s]", " ", limpio)
    limpio = re.sub(r"\b(\d{1,3}(?:\.\d{3})+)\b", lambda m: m.group(1).replace(".", ""), limpio)
    limpio = re.sub(r"\b(\d{1,3}(?:,\d{3})+)\b", lambda m: m.group(1).replace(",", ""), limpio)
    limpio = re.sub(r"\b(\d+)\s+(mil|k)\b", lambda m: str(int(m.group(1)) * 1000), limpio)
    return re.sub(r"\s+", " ", limpio).strip()


def wer(referencia, hipotesis):
    if not referencia:
        return None
    try:
        import jiwer
    except ImportError:
        return None
    return jiwer.wer(referencia, hipotesis)


def intencion_del_sistema(intencion_base, monto):
    """Reproduce la intencion que devuelve el backend para una transcripcion.

    ``nlp.detect_intent`` solo distingue tres casos. El backend agrega un
    cuarto: una peticion de registro sin monto recuperable queda pendiente de
    aclaracion porque nunca se inventa un valor.
    """
    if intencion_base == "registrar" and monto is None:
        return "requiere_aclaracion"
    return intencion_base


def main():
    args = parse_args()
    if not MANIFEST.exists():
        print("No existe el manifiesto:", MANIFEST)
        return 1
    if not ai.esta_configurado():
        print("Falta GEMINI_API_KEY en backend/.env")
        return 1

    with MANIFEST.open(encoding="utf-8-sig", newline="") as fh:
        filas = list(csv.DictReader(fh))

    base_audio = Path(args.audio_dir) if args.audio_dir else DATASET

    resultados = []
    for fila in filas:
        ruta = base_audio / Path(fila["archivo"]).name
        if not ruta.exists():
            ruta = base_audio / fila["archivo"]
        if not ruta.exists():
            print(f"[{fila['id']}] sin audio, se omite")
            continue

        audio_bytes = ruta.read_bytes()
        inicio = time.time()
        salida = None
        for intento in range(1, 5):
            try:
                salida = ai.transcribe_audio(audio_bytes, model=args.modelo)
                break
            except ai.STTCuota:
                espera = 25 * intento
                print(
                    f"[{fila['id']}] cuota agotada, esperando {espera}s "
                    f"(intento {intento}/4)"
                )
                time.sleep(espera)
            except ai.ErrorSTT as exc:
                print(f"[{fila['id']}] ERROR {exc.codigo}: {exc.mensaje}")
                break
        if salida is None:
            resultados.append(
                {
                    "id": fila["id"],
                    "error": "sin resultado",
                    "esperado": fila["transcripcion"],
                    "obtenido": "",
                }
            )
            continue
        latencia = round(time.time() - inicio, 2)

        transcrito = salida["texto"]
        esperado = fila["transcripcion"]
        monto_esperado = fila["monto_esperado"].strip()
        monto_obtenido = nlp.parse_amount(normalizar(transcrito))
        intencion_esperada = fila["intent"]
        intencion_obtenida = intencion_del_sistema(
            nlp.detect_intent(normalizar(transcrito)), monto_obtenido
        )

        monto_ok = None
        if monto_esperado:
            monto_ok = str(monto_obtenido) == str(monto_esperado)
        intencion_ok = intencion_esperada == intencion_obtenida

        resultados.append(
            {
                "id": fila["id"],
                "esperado": esperado,
                "obtenido": transcrito,
                "wer": wer(
                    normalizar_para_wer(esperado), normalizar_para_wer(transcrito)
                ),
                "monto_esperado": monto_esperado or None,
                "monto_obtenido": monto_obtenido,
                "monto_ok": monto_ok,
                "intencion_esperada": intencion_esperada,
                "intencion_obtenida": intencion_obtenida,
                "intencion_ok": intencion_ok,
                "latencia_api_s": round((salida.get("latencia_ms") or 0) / 1000, 2),
                "latencia_total_s": latencia,
                "tokens_entrada": salida.get("tokens_entrada"),
                "tokens_salida": salida.get("tokens_salida"),
            }
        )
        marca = "OK " if (monto_ok in (None, True) and intencion_ok) else "!! "
        print(
            f"{marca}[{fila['id']}] api {round((salida.get('latencia_ms') or 0) / 1000, 2)}s "
            f"| \"{transcrito}\" | monto={monto_obtenido} "
            f"(esperado {monto_esperado or '-'})"
        )
        if args.pausa:
            time.sleep(args.pausa)

    def promedio(clave):
        valores = [r[clave] for r in resultados if r.get(clave) is not None]
        return round(statistics.mean(valores), 4) if valores else None

    def exactitud(clave):
        valores = [r[clave] for r in resultados if r.get(clave) is not None]
        if not valores:
            return None
        return round(sum(1 for v in valores if v) / len(valores), 4)

    latencias = [r["latencia_api_s"] for r in resultados if r.get("latencia_api_s")]
    totales = [r["latencia_total_s"] for r in resultados if r.get("latencia_total_s")]
    resumen = {
        "clips": len(resultados),
        "modelo": args.modelo or ai.modelo(),
        "wer_promedio": promedio("wer"),
        "wer_objetivo": UMBRAL_WER,
        "exactitud_montos": exactitud("monto_ok"),
        "montos_objetivo": UMBRAL_MONTOS,
        "exactitud_intencion": exactitud("intencion_ok"),
        "intencion_objetivo": UMBRAL_INTENCION,
        "latencia_api_promedio_s": round(statistics.mean(latencias), 2) if latencias else None,
        "latencia_api_maxima_s": round(max(latencias), 2) if latencias else None,
        "latencia_total_promedio_s": round(statistics.mean(totales), 2) if totales else None,
        "tokens_totales": sum(
            (r.get("tokens_entrada") or 0) + (r.get("tokens_salida") or 0)
            for r in resultados
        ),
    }
    REPORTE.write_text(
        json.dumps({"resumen": resumen, "resultados": resultados},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n=== Resumen ===")
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    print(f"\nReporte completo en {REPORTE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
