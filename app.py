import os
import io
import time
from collections import deque
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory, send_file
import requests
from PIL import Image

from src.pipeline import run_hybrid_pipeline
from src.sam_client import RemoteSAMClient
from src.coral_classifier import CLASS_COLORS
from src.preprocessing import enhance_underwater_image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
MODELS_DIR = os.path.join(BASE_DIR, "models")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOGS_DIR, "pipeline.log")
log_buffer = deque(maxlen=200)


def log_event(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_short = datetime.now().strftime("%H:%M:%S")
    entry = {
        "time": time_short,
        "timestamp": timestamp,
        "level": level,
        "message": message
    }
    log_buffer.append(entry)
    formatted = f"[{timestamp}] [{level}] {message}"
    print(formatted)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024  # 64 MB max upload

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/images")
def list_images():
    """Lists available test photos in the images/ directory."""
    files = []
    for f in sorted(os.listdir(IMAGES_DIR)):
        ext = os.path.splitext(f)[1].lower()
        if ext in VALID_EXTENSIONS:
            filepath = os.path.join(IMAGES_DIR, f)
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            files.append({
                "filename": f,
                "url": f"/images/{f}",
                "size_mb": round(size_mb, 2)
            })
    return jsonify({"images": files, "count": len(files)})


@app.route("/api/test-colab", methods=["POST"])
def test_colab():
    """Tests connection to the user-provided Google Colab ngrok URL."""
    data = request.get_json() or {}
    url = (data.get("colab_url") or "").strip().rstrip("/")
    if not url:
        log_event("Teste de conexão rejeitado: Nenhuma URL do Colab informada.", level="WARNING")
        return jsonify({"connected": False, "error": "Nenhuma URL informada."})

    log_event(f"Testando conexão com Colab: {url}/health ...")
    client = RemoteSAMClient(colab_url=url)
    try:
        t0 = time.time()
        headers = {
            "ngrok-skip-browser-warning": "true",
            "Bypass-Tunnel-Reminder": "true",
            "User-Agent": "CoralNet-SAM-Client/1.0"
        }
        resp = requests.get(f"{url}/health", headers=headers, timeout=8)
        latency_ms = int((time.time() - t0) * 1000)
        if resp.status_code == 200:
            info = resp.json()
            gpu_name = info.get("gpu_name", "NVIDIA GPU")
            model_name = info.get("model", "CoralSCOP ViT-B")
            is_coralscop = "coralscop" in model_name.lower() or info.get("engine") == "coralscop"
            log_event(f"Colab online! Latência: {latency_ms}ms | GPU: {gpu_name} | Modelo: {model_name}", level="SUCCESS")
            return jsonify({
                "connected": True,
                "latency_ms": latency_ms,
                "model": model_name,
                "is_coralscop": is_coralscop,
                "device": info.get("device", "cuda"),
                "gpu_name": gpu_name
            })
        else:
            err_msg = f"Servidor Colab retornou status HTTP {resp.status_code}: {resp.text[:200]}"
            log_event(err_msg, level="ERROR")
            return jsonify({"connected": False, "error": err_msg})
    except Exception as e:
        err_msg = f"Não foi possível conectar ao Colab: {str(e)}"
        log_event(err_msg, level="ERROR")
        return jsonify({"connected": False, "error": err_msg})


@app.route("/api/logs")
def get_logs():
    """Returns recent log entries for the in-browser log console."""
    return jsonify({
        "success": True,
        "logs": list(log_buffer),
        "log_file": LOG_FILE
    })


@app.route("/api/logs/clear", methods=["POST"])
def clear_logs():
    """Clears the in-memory log buffer."""
    log_buffer.clear()
    return jsonify({"success": True})


@app.route("/api/upload", methods=["POST"])
def upload_image():
    """Uploads a new survey image to the images/ folder."""
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Nome de arquivo vazio."}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in VALID_EXTENSIONS:
        return jsonify({"error": f"Formato inválido ({ext}). Formatos suportados: JPG, PNG, TIFF."}), 400

    filename = os.path.basename(file.filename)
    dest_path = os.path.join(IMAGES_DIR, filename)
    file.save(dest_path)
    log_event(f"Nova foto enviada pelo usuário: {filename} ({round(os.path.getsize(dest_path)/(1024*1024), 2)} MB)")

    return jsonify({
        "success": True,
        "filename": filename,
        "url": f"/images/{filename}"
    })


@app.route("/api/preview-filter", methods=["POST"])
def preview_filter():
    """Generates a local underwater-enhanced preview image (White Balance / CLAHE / Combined) without calling Colab."""
    data = request.get_json() or {}
    image_name = data.get("image_name")
    filter_mode = (data.get("filter_mode") or "combined").lower().strip()
    quadrat_corners = data.get("quadrat_corners")

    if not image_name:
        return jsonify({"error": "Nenhuma imagem selecionada."}), 400

    image_path = os.path.join(IMAGES_DIR, os.path.basename(image_name))
    if not os.path.exists(image_path):
        return jsonify({"error": f"Imagem '{image_name}' não encontrada."}), 404

    if filter_mode == "none":
        with Image.open(image_path) as im:
            w, h = im.size
        return jsonify({
            "success": True,
            "preview_url": f"/images/{os.path.basename(image_name)}",
            "width": w,
            "height": h
        })

    try:
        t0 = time.time()
        with Image.open(image_path) as orig_img:
            orig_rgb = orig_img.convert("RGB")
            w, h = orig_rgb.size
            enhanced = enhance_underwater_image(
                orig_rgb,
                filter_mode=filter_mode,
                quadrat_corners=quadrat_corners if (quadrat_corners and len(quadrat_corners) == 4) else None
            )

        base_name = os.path.splitext(os.path.basename(image_name))[0]
        roi_tag = "roi" if (quadrat_corners and len(quadrat_corners) == 4) else "full"
        preview_filename = f"{base_name}_enhanced_{filter_mode}_{roi_tag}.jpg"
        preview_path = os.path.join(OUTPUT_DIR, preview_filename)
        enhanced.save(preview_path, format="JPEG", quality=92)
        elapsed_ms = int((time.time() - t0) * 1000)
        log_event(f"Filtro '{filter_mode}' gerado localmente para {image_name} em {elapsed_ms}ms.")

        return jsonify({
            "success": True,
            "preview_url": f"/output/{preview_filename}?t={int(time.time() * 1000)}",
            "width": w,
            "height": h
        })
    except Exception as e:
        log_event(f"Falha ao gerar prévia de filtro: {e}", level="ERROR")
        return jsonify({"error": str(e)}), 500


@app.route("/api/process", methods=["POST"])
def process_pipeline():
    """Executes the CoralSCOP + CoralNet benthic segmentation pipeline."""
    data = request.get_json() or {}
    image_name = data.get("image_name")
    if not image_name:
        log_event("Execução rejeitada: Nenhuma imagem selecionada.", level="ERROR")
        return jsonify({"error": "Nenhuma imagem selecionada."}), 400

    image_path = os.path.join(IMAGES_DIR, os.path.basename(image_name))
    if not os.path.exists(image_path):
        log_event(f"Imagem não encontrada: {image_path}", level="ERROR")
        return jsonify({"error": f"Imagem '{image_name}' não encontrada no servidor."}), 404

    colab_url = (data.get("colab_url") or "").strip() or None
    min_area = int(data.get("min_area", 1500))
    iou_thresh = float(data.get("iou_thresh", 0.60))
    n_points = int(data.get("n_points", 5))
    quadrat_w = float(data.get("quadrat_width_cm", 50.0))
    quadrat_h = float(data.get("quadrat_height_cm", 50.0))
    filter_mode = (data.get("filter_mode") or "combined").lower().strip()
    quadrat_corners = data.get("quadrat_corners")
    if not (isinstance(quadrat_corners, list) and len(quadrat_corners) == 4):
        quadrat_corners = None
    render_on_enhanced = bool(data.get("render_on_enhanced", False))

    # Hiperparâmetros do CoralSCOP / SAM
    points_per_side = int(data.get("points_per_side", 32))
    pred_iou_thresh = float(data.get("pred_iou_thresh", 0.72))
    stability_score_thresh = float(data.get("stability_score_thresh", 0.62))
    crop_n_layers = int(data.get("crop_n_layers", 1))
    crop_n_points_downscale_factor = int(data.get("crop_n_points_downscale_factor", 2))

    log_event(
        f"Iniciando pipeline: {image_name} | Destino: {colab_url or 'Modo Simulado Local'} | "
        f"Filtro: {filter_mode} | ROI 4-Cantos: {'Sim' if quadrat_corners else 'Não'} | "
        f"Grid: {points_per_side}x{points_per_side} | Área mín: {min_area}px | "
        f"pred_iou: {pred_iou_thresh} | stability: {stability_score_thresh}"
    )

    try:
        t_start = time.time()
        result = run_hybrid_pipeline(
            image_path=image_path,
            colab_url=colab_url,
            output_dir=OUTPUT_DIR,
            min_area=min_area,
            iou_thresh=iou_thresh,
            n_points_multi=n_points,
            quadrat_width_cm=quadrat_w,
            quadrat_height_cm=quadrat_h,
            points_per_side=points_per_side,
            pred_iou_thresh=pred_iou_thresh,
            stability_score_thresh=stability_score_thresh,
            crop_n_layers=crop_n_layers,
            crop_n_points_downscale_factor=crop_n_points_downscale_factor,
            filter_mode=filter_mode,
            quadrat_corners=quadrat_corners,
            render_on_enhanced=render_on_enhanced
        )
        total_sec = round(time.time() - t_start, 1)
        log_event(
            f"Pipeline concluído em {total_sec}s ({result.get('remote_model')})! "
            f"{result.get('total_colonies')} colônias ({result.get('total_coral_cm2')} cm² / {result.get('total_coral_cover_pct')}% do quadrante).",
            level="SUCCESS"
        )

        return jsonify({
            "success": True,
            "data": result,
            "class_colors": CLASS_COLORS
        })
    except Exception as e:
        import traceback
        err_text = str(e)
        if "10054" in err_text or "Connection aborted" in err_text:
            log_event(f"[QUEDA DE CONEXÃO DO TÚNEL] {err_text}", level="ERROR")
        elif "500" in err_text:
            log_event(f"[ERRO NO SERVIDOR COLAB (500)] {err_text}", level="ERROR")
        else:
            log_event(f"[ERRO NO PIPELINE] {err_text}", level="ERROR")

        traceback.print_exc()
        return jsonify({
            "error": err_text,
            "is_connection_error": "10054" in err_text or "Connection aborted" in err_text
        }), 500


@app.route("/api/download/csv/<filename>")
def download_csv(filename):
    """Downloads the ecological report CSV."""
    safe_name = os.path.basename(filename)
    csv_path = os.path.join(OUTPUT_DIR, safe_name)
    if os.path.exists(csv_path):
        return send_file(csv_path, as_attachment=True, download_name=safe_name)
    return jsonify({"error": "Relatório CSV não encontrado."}), 404


@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)


@app.route("/output/<path:filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("[*] CoralNet-SAM Web App (Fase 3: Interface Unificada)")
    print("[*] Acesse em seu navegador: http://127.0.0.1:5000")
    print("=" * 65 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
