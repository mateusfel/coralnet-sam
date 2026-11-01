import os
import io
import time
from flask import Flask, render_template, jsonify, request, send_from_directory, send_file
import requests
from PIL import Image

from src.pipeline import run_hybrid_pipeline
from src.sam_client import RemoteSAMClient
from src.coral_classifier import CLASS_COLORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
MODELS_DIR = os.path.join(BASE_DIR, "models")

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

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
        return jsonify({"connected": False, "error": "Nenhuma URL informada."})

    client = RemoteSAMClient(colab_url=url)
    try:
        t0 = time.time()
        headers = {"Bypass-Tunnel-Reminder": "true", "User-Agent": "CoralNet-SAM-Client/1.0"}
        resp = requests.get(f"{url}/health", headers=headers, timeout=8)
        latency_ms = int((time.time() - t0) * 1000)
        if resp.status_code == 200:
            info = resp.json()
            return jsonify({
                "connected": True,
                "latency_ms": latency_ms,
                "model": info.get("model", "SAM ViT-H"),
                "device": info.get("device", "cuda"),
                "gpu_name": info.get("gpu_name", "NVIDIA GPU")
            })
        else:
            return jsonify({"connected": False, "error": f"Servidor retornou status {resp.status_code}"})
    except Exception as e:
        return jsonify({"connected": False, "error": f"Não foi possível conectar: {str(e)}"})


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

    return jsonify({
        "success": True,
        "filename": filename,
        "url": f"/images/{filename}"
    })


@app.route("/api/process", methods=["POST"])
def process_pipeline():
    """Executes the Phase 3 SAM + CoralNet pipeline."""
    data = request.get_json() or {}
    image_name = data.get("image_name")
    if not image_name:
        return jsonify({"error": "Nenhuma imagem selecionada."}), 400

    image_path = os.path.join(IMAGES_DIR, image_name)
    if not os.path.exists(image_path):
        return jsonify({"error": f"Imagem '{image_name}' não encontrada no servidor."}), 404

    colab_url = (data.get("colab_url") or "").strip() or None
    min_area = int(data.get("min_area", 300))
    iou_thresh = float(data.get("iou_thresh", 0.60))
    n_points = int(data.get("n_points", 5))
    quadrat_w = float(data.get("quadrat_width_cm", 50.0))
    quadrat_h = float(data.get("quadrat_height_cm", 50.0))

    try:
        result = run_hybrid_pipeline(
            image_path=image_path,
            colab_url=colab_url,
            output_dir=OUTPUT_DIR,
            min_area=min_area,
            iou_thresh=iou_thresh,
            n_points_multi=n_points,
            quadrat_width_cm=quadrat_w,
            quadrat_height_cm=quadrat_h
        )

        return jsonify({
            "success": True,
            "data": result,
            "class_colors": CLASS_COLORS
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


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
