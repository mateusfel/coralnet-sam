import os
import time
from collections import deque
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory, send_file
import requests
from PIL import Image

from src.pipeline import (
    run_hybrid_pipeline,
    inspect_image_polygon_status,
    load_pipeline_session,
    render_and_export_session,
    session_to_public_payload,
    export_project_consolidated_csv,
    group_colonies_in_session,
    modify_colony_part_in_session,
    add_manual_colony_in_session,
    update_colony_polygon_vertices_in_session,
)
from src.few_shot_memory import (
    CORAL_GENERA,
    NON_CORAL_LABEL,
    NON_CORAL_DISPLAY,
    CLASS_COLORS,
    get_default_memory_path,
    get_fewshot_summary,
    set_fewshot_enabled,
    clear_fewshot_memory,
    add_fewshot_prototype,
)
from src.preprocessing import enhance_underwater_image
from src.project_manager import (
    PROJECT_MARKER_FILENAME,
    VALID_IMAGE_EXTENSIONS,
    compute_file_sha256,
    get_sample_images_info,
    get_default_projects_parent_dir,
    create_project,
    open_existing_project,
    activate_demo_workspace,
    remove_recent_project,
    copy_sample_images_to_dir,
    resolve_active_workspace,
    list_recent_projects_with_status,
    browse_local_directories,
    pick_folder_native_dialog,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
MODELS_DIR = os.path.join(BASE_DIR, "models")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
PROJECTS_REGISTRY_FILE = os.path.join(LOGS_DIR, "projects_registry.json")

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOGS_DIR, "pipeline.log")
log_buffer = deque(maxlen=250)


def log_event(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_short = datetime.now().strftime("%H:%M:%S")
    entry = {
        "time": time_short,
        "timestamp": timestamp,
        "level": level,
        "message": message,
    }
    log_buffer.append(entry)
    formatted = f"[{timestamp}] [{level}] {message}"
    try:
        print(formatted)
    except UnicodeEncodeError:
        try:
            print(formatted.encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 128 * 1024 * 1024  # 128 MB max upload (supports multi-photo upload)

VALID_EXTENSIONS = VALID_IMAGE_EXTENSIONS


def _get_ws():
    """Resolves the active workspace (external User Project or built-in Demo/Test Suggestion Set)."""
    return resolve_active_workspace(
        repo_base_dir=BASE_DIR,
        repo_images_dir=IMAGES_DIR,
        repo_output_dir=OUTPUT_DIR,
        default_memory_path=get_default_memory_path(),
        registry_path=PROJECTS_REGISTRY_FILE,
    )


def _public_ws_info(ws):
    return {
        "mode": ws["mode"],
        "is_demo": ws["is_demo"],
        "name": ws["name"],
        "root_path": ws["root_path"],
        "marker_file": ws["marker_file"],
        "marker_filename": PROJECT_MARKER_FILENAME,
        "directories": {
            "raw_images": ws["raw_images_dir"],
            "filtered_images": ws["filtered_dir"],
            "polygons": ws["polygons_dir"],
            "exports": ws["exports_dir"],
        },
    }


def _scan_workspace_images(ws):
    """
    Lists all raw images in the active workspace along with their live SHA-256 hash verification
    status: 'processed', 'unprocessed', or 'hash_mismatch' (when replaced by a file of the same name).
    """
    raw_dir = ws["raw_images_dir"]
    poly_dir = ws["polygons_dir"]
    legacy_dir = ws["legacy_output_dir"]

    files = []
    counts = {"total": 0, "processed": 0, "unprocessed": 0, "hash_mismatch": 0}

    if os.path.isdir(raw_dir):
        for f in sorted(os.listdir(raw_dir)):
            ext = os.path.splitext(f)[1].lower()
            if ext not in VALID_EXTENSIONS:
                continue
            filepath = os.path.join(raw_dir, f)
            if not os.path.isfile(filepath):
                continue

            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            st = inspect_image_polygon_status(
                image_filename=f,
                raw_images_dir=raw_dir,
                polygons_dir=poly_dir,
                legacy_output_dir=legacy_dir,
            )
            sha_short = (st["image_sha256"] or "")[:12]
            status_code = st["status"]
            counts["total"] += 1
            if status_code == "processed":
                counts["processed"] += 1
            elif status_code == "hash_mismatch":
                counts["hash_mismatch"] += 1
            else:
                counts["unprocessed"] += 1

            sess = st["session"] or {}
            files.append({
                "filename": f,
                "url": f"/images/{f}?v={sha_short}",
                "size_mb": round(size_mb, 2),
                "image_sha256_short": sha_short,
                "status": status_code,
                "processed": status_code == "processed",
                "hash_mismatch": status_code == "hash_mismatch",
                "previous_sha256_short": (st["previous_sha256"] or "")[:12] if st["hash_mismatch"] else "",
                "total_colonies": int(sess.get("total_colonies", 0)) if status_code == "processed" else 0,
                "total_coral_cm2": float(sess.get("total_coral_cm2", 0.0)) if status_code == "processed" else 0.0,
                "total_coral_cover_pct": float(sess.get("total_coral_cover_pct", 0.0)) if status_code == "processed" else 0.0,
                "has_quadrat_roi": bool(sess.get("has_quadrat_roi", False)) if status_code == "processed" else False,
            })

    return files, counts


def _load_verified_session_or_error(image_name: str, ws):
    """
    Loads a polygon session strictly verified by SHA-256 against the raw image on disk.
    Returns `(session_dict, None, 200)` on success, or `(None, error_msg, http_status)` on failure.
    """
    st = inspect_image_polygon_status(
        image_filename=image_name,
        raw_images_dir=ws["raw_images_dir"],
        polygons_dir=ws["polygons_dir"],
        legacy_output_dir=ws["legacy_output_dir"],
    )
    if st["status"] == "processed" and st["session"]:
        return st["session"], None, 200
    if st["status"] == "hash_mismatch":
        msg = (
            f"O arquivo de imagem '{image_name}' foi modificado ou substituído por outro de mesmo nome "
            f"(hash SHA-256 diferente: {(st['previous_sha256'] or '')[:10]} != {(st['image_sha256'] or '')[:10]}). "
            f"Os polígonos antigos foram desconsiderados — reexecute o pipeline nesta foto."
        )
        log_event(msg, level="WARNING")
        return None, msg, 409
    if st["status"] == "missing":
        return None, f"Imagem '{image_name}' não encontrada na pasta raw_images.", 404
    return None, "Sessão desta imagem não encontrada. Execute o pipeline primeiro.", 404


def _render_ws_session(session_data, ws, recompute_unlocked: bool = False):
    updated = render_and_export_session(
        session_data,
        output_dir=ws["exports_dir"],
        recompute_unlocked=recompute_unlocked,
        polygons_dir=ws["polygons_dir"],
        filtered_dir=ws["filtered_dir"],
        fewshot_memory_path=ws["fewshot_memory_path"],
    )
    if not ws["is_demo"]:
        try:
            export_project_consolidated_csv(
                raw_images_dir=ws["raw_images_dir"],
                polygons_dir=ws["polygons_dir"],
                exports_dir=ws["exports_dir"],
            )
        except Exception:
            pass
    return updated


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/taxonomy")
def get_taxonomy():
    """Returns strictly the 11 South Atlantic Coral Genera, Non-Coral filter label, colors, Few-Shot & workspace."""
    ws = _get_ws()
    return jsonify({
        "success": True,
        "genera": CORAL_GENERA,
        "non_coral_label": NON_CORAL_LABEL,
        "non_coral_display": NON_CORAL_DISPLAY,
        "class_colors": CLASS_COLORS,
        "fewshot": get_fewshot_summary(ws["fewshot_memory_path"]),
        "workspace": _public_ws_info(ws),
    })


# =========================================================================
# PROJECT WORKSPACE MANAGEMENT ROUTES
# =========================================================================
@app.route("/api/projects", methods=["GET"])
def get_projects_info():
    """Returns active project/demo workspace, image status counts, recent projects, and default sample set info."""
    ws = _get_ws()
    files, counts = _scan_workspace_images(ws)
    return jsonify({
        "success": True,
        "workspace": _public_ws_info(ws),
        "summary": counts,
        "images": files,
        "recent_projects": list_recent_projects_with_status(PROJECTS_REGISTRY_FILE, BASE_DIR),
        "sample_set": get_sample_images_info(IMAGES_DIR),
        "default_parent_dir": get_default_projects_parent_dir(BASE_DIR),
        "fewshot": get_fewshot_summary(ws["fewshot_memory_path"]),
    })


@app.route("/api/projects/create", methods=["POST"])
def api_create_project():
    """Creates a new project folder outside the repository with `coralscop_project.json` and 4 subdirectories."""
    data = request.get_json() or {}
    root_path = (data.get("root_path") or "").strip()
    name = (data.get("name") or "").strip()
    copy_samples = bool(data.get("copy_sample_images", False))

    try:
        created = create_project(
            root_path=root_path,
            name=name,
            repo_base_dir=BASE_DIR,
            repo_images_dir=IMAGES_DIR,
            registry_path=PROJECTS_REGISTRY_FILE,
            copy_sample_images=copy_samples,
        )
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Falha ao criar projeto: {e}"}), 500

    ws = _get_ws()
    files, counts = _scan_workspace_images(ws)
    sample_note = f" ({created['copied_sample_count']} fotos padrão copiadas)" if copy_samples else ""
    log_event(
        f"Novo projeto criado e ativado: '{created['name']}' em {created['root_path']}{sample_note}.",
        level="SUCCESS",
    )
    return jsonify({
        "success": True,
        "created": created,
        "workspace": _public_ws_info(ws),
        "summary": counts,
        "images": files,
        "recent_projects": list_recent_projects_with_status(PROJECTS_REGISTRY_FILE, BASE_DIR),
        "fewshot": get_fewshot_summary(ws["fewshot_memory_path"]),
    })


@app.route("/api/projects/open", methods=["POST"])
def api_open_project():
    """Validates `coralscop_project.json` in an existing folder and switches the active workspace to it."""
    data = request.get_json() or {}
    root_path = (data.get("root_path") or "").strip()

    try:
        opened = open_existing_project(
            root_path=root_path,
            repo_base_dir=BASE_DIR,
            registry_path=PROJECTS_REGISTRY_FILE,
        )
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Falha ao abrir projeto: {e}"}), 500

    ws = _get_ws()
    files, counts = _scan_workspace_images(ws)
    mismatch_note = f" | ⚠️ {counts['hash_mismatch']} com hash alterado" if counts["hash_mismatch"] else ""
    log_event(
        f"Projeto aberto: '{opened['name']}' ({opened['root_path']}) — "
        f"{counts['total']} fotos ({counts['processed']} processadas, {counts['unprocessed']} pendentes{mismatch_note}).",
        level="SUCCESS",
    )
    return jsonify({
        "success": True,
        "opened": opened,
        "workspace": _public_ws_info(ws),
        "summary": counts,
        "images": files,
        "recent_projects": list_recent_projects_with_status(PROJECTS_REGISTRY_FILE, BASE_DIR),
        "fewshot": get_fewshot_summary(ws["fewshot_memory_path"]),
    })


@app.route("/api/projects/demo", methods=["POST"])
def api_activate_demo():
    """Switches back to the built-in Demo/Test Suggestion Set shipped in the repository."""
    activate_demo_workspace(PROJECTS_REGISTRY_FILE)
    ws = _get_ws()
    files, counts = _scan_workspace_images(ws)
    log_event("Modo alternado para o Conjunto Padrão de Teste (Demonstração do repositório).")
    return jsonify({
        "success": True,
        "workspace": _public_ws_info(ws),
        "summary": counts,
        "images": files,
        "recent_projects": list_recent_projects_with_status(PROJECTS_REGISTRY_FILE, BASE_DIR),
        "fewshot": get_fewshot_summary(ws["fewshot_memory_path"]),
    })


@app.route("/api/projects/copy-samples", methods=["POST"])
def api_copy_samples_into_project():
    """Copies the repository's default test suggestion images into the currently open project's `raw_images/`."""
    ws = _get_ws()
    if ws["is_demo"]:
        return jsonify({"error": "Você já está no Conjunto Padrão de Teste. Crie ou abra um projeto primeiro."}), 400

    copied = copy_sample_images_to_dir(IMAGES_DIR, ws["raw_images_dir"])
    files, counts = _scan_workspace_images(ws)
    log_event(f"{len(copied)} foto(s) padrão de teste copiadas para o projeto '{ws['name']}'.", level="SUCCESS")
    return jsonify({
        "success": True,
        "copied_count": len(copied),
        "copied_files": copied,
        "summary": counts,
        "images": files,
    })


@app.route("/api/projects/remove-recent", methods=["POST"])
def api_remove_recent_project():
    """Removes a project from the recent history list without deleting any files on disk."""
    data = request.get_json() or {}
    root_path = (data.get("root_path") or "").strip()
    remove_recent_project(root_path, PROJECTS_REGISTRY_FILE)
    ws = _get_ws()
    files, counts = _scan_workspace_images(ws)
    return jsonify({
        "success": True,
        "workspace": _public_ws_info(ws),
        "summary": counts,
        "images": files,
        "recent_projects": list_recent_projects_with_status(PROJECTS_REGISTRY_FILE, BASE_DIR),
        "fewshot": get_fewshot_summary(ws["fewshot_memory_path"]),
    })


@app.route("/api/projects/pick-folder", methods=["POST"])
def api_pick_folder_native():
    """Opens a native Windows OS folder selection dialog in foreground and returns the chosen path."""
    data = request.get_json() or {}
    initial_dir = (data.get("initial_dir") or "").strip() or get_default_projects_parent_dir(BASE_DIR)
    title = (data.get("title") or "").strip() or "Selecione a pasta raiz do projeto CoralSCOP"
    chosen = pick_folder_native_dialog(initial_dir=initial_dir, title=title)
    return jsonify({
        "success": True,
        "cancelled": chosen is None,
        "path": chosen,
    })


@app.route("/api/projects/browse-dirs", methods=["POST"])
def api_browse_dirs():
    """Lists local drives and folders for the in-browser folder navigator (and optionally creates a subfolder)."""
    data = request.get_json() or {}
    target_path = data.get("path")
    create_sub = (data.get("create_subfolder") or "").strip() or None
    try:
        listing = browse_local_directories(
            target_path=target_path,
            repo_base_dir=BASE_DIR,
            create_subfolder=create_sub,
        )
        return jsonify({"success": True, **listing})
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/download-summary")
def download_project_summary_csv():
    """Generates and downloads `project_ecological_summary.csv` across all hash-verified processed images."""
    ws = _get_ws()
    info = export_project_consolidated_csv(
        raw_images_dir=ws["raw_images_dir"],
        polygons_dir=ws["polygons_dir"],
        exports_dir=ws["exports_dir"],
        legacy_output_dir=ws["legacy_output_dir"],
    )
    safe_prefix = "demo" if ws["is_demo"] else "".join(
        ch if (ch.isalnum() or ch in ("-", "_")) else "_" for ch in ws["name"]
    ).strip("_") or "projeto"
    dl_name = f"{safe_prefix}_ecological_summary.csv"
    return send_file(info["csv_path"], as_attachment=True, download_name=dl_name)


# =========================================================================
# IMAGES, HASH-VERIFIED SESSION RELOAD & UPLOAD ROUTES
# =========================================================================
@app.route("/api/images")
def list_images():
    """Lists available photos in the active project's `raw_images/` (or Demo `images/`) with processed/hash status."""
    ws = _get_ws()
    files, counts = _scan_workspace_images(ws)
    return jsonify({
        "images": files,
        "count": len(files),
        "summary": counts,
        "workspace": _public_ws_info(ws),
    })


@app.route("/api/image-session/<path:image_name>")
def get_image_session(image_name):
    """
    Checks if `image_name` has a saved polygon/classification file in `polygons/` AND verifies its
    SHA-256 hash against the raw image file on disk. If replaced by another file of the same name,
    detects the hash difference and disregards the old polygons (`status='hash_mismatch'`).
    """
    ws = _get_ws()
    fname = os.path.basename(image_name)
    st = inspect_image_polygon_status(
        image_filename=fname,
        raw_images_dir=ws["raw_images_dir"],
        polygons_dir=ws["polygons_dir"],
        legacy_output_dir=ws["legacy_output_dir"],
    )

    if st["status"] == "missing":
        return jsonify({"error": f"Imagem '{fname}' não encontrada."}), 404

    sha_short = (st["image_sha256"] or "")[:12]

    if st["status"] == "processed" and st["session"]:
        sess = st["session"]
        out_img = os.path.join(ws["exports_dir"], sess.get("output_image_filename", ""))
        out_csv = os.path.join(ws["exports_dir"], sess.get("output_csv_filename", ""))
        if not (os.path.isfile(out_img) and os.path.isfile(out_csv)):
            payload = _render_ws_session(sess, ws, recompute_unlocked=False)
        else:
            payload = session_to_public_payload(sess, fewshot_memory_path=ws["fewshot_memory_path"])

        return jsonify({
            "success": True,
            "has_session": True,
            "status": "processed",
            "image_sha256_short": sha_short,
            "data": payload,
        })

    if st["status"] == "hash_mismatch":
        prev_short = (st["previous_sha256"] or "")[:12]
        msg = (
            f"O arquivo '{fname}' foi substituído por uma imagem diferente com o mesmo nome "
            f"(hash anterior: {prev_short} != hash atual: {sha_short}). "
            f"Os polígonos e classificações antigos foram desconsiderados."
        )
        log_event(msg, level="WARNING")
        return jsonify({
            "success": True,
            "has_session": False,
            "status": "hash_mismatch",
            "image_sha256_short": sha_short,
            "previous_sha256_short": prev_short,
            "message": msg,
        })

    return jsonify({
        "success": True,
        "has_session": False,
        "status": "unprocessed",
        "image_sha256_short": sha_short,
    })


@app.route("/api/test-colab", methods=["POST"])
def test_colab():
    """Tests connection to the user-provided Google Colab ngrok/Localtunnel URL."""
    data = request.get_json() or {}
    url = (data.get("colab_url") or "").strip().rstrip("/")
    if not url:
        log_event("Teste de conexão rejeitado: Nenhuma URL do Colab informada.", level="WARNING")
        return jsonify({"connected": False, "error": "Nenhuma URL informada."})

    log_event(f"Testando conexão com Colab: {url}/health ...")
    try:
        t0 = time.time()
        headers = {
            "ngrok-skip-browser-warning": "true",
            "Bypass-Tunnel-Reminder": "true",
            "User-Agent": "CoralSCOP-BioCLIP25-Client/3.0",
        }
        resp = requests.get(f"{url}/health", headers=headers, timeout=8)
        latency_ms = int((time.time() - t0) * 1000)
        if resp.status_code == 200:
            info = resp.json()
            gpu_name = info.get("gpu_name", "NVIDIA GPU")
            model_name = info.get("model", "CoralSCOP ViT-B")
            classifier_model = info.get("classifier_model", "")
            is_coralscop = "coralscop" in model_name.lower() or info.get("engine") == "coralscop"
            has_bioclip = bool(info.get("has_bioclip")) or ("bioclip" in classifier_model.lower())
            log_event(
                f"Colab online ({latency_ms}ms) | GPU: {gpu_name} | Segm: {model_name} | "
                f"Classificador: {classifier_model or 'Não carregado (atualize o Colab)'}",
                level="SUCCESS",
            )
            return jsonify({
                "connected": True,
                "latency_ms": latency_ms,
                "model": model_name,
                "classifier_model": classifier_model,
                "is_coralscop": is_coralscop,
                "has_bioclip": has_bioclip,
                "device": info.get("device", "cuda"),
                "gpu_name": gpu_name,
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
        "log_file": LOG_FILE,
    })


@app.route("/api/logs/clear", methods=["POST"])
def clear_logs():
    """Clears the in-memory log buffer."""
    log_buffer.clear()
    return jsonify({"success": True})


@app.route("/api/upload", methods=["POST"])
def upload_image():
    """Uploads one or multiple survey images into the active project's `raw_images/` folder."""
    ws = _get_ws()
    incoming = request.files.getlist("files")
    if not incoming and "file" in request.files:
        incoming = [request.files["file"]]

    if not incoming:
        return jsonify({"error": "Nenhum arquivo enviado."}), 400

    saved_names = []
    skipped_errors = []
    os.makedirs(ws["raw_images_dir"], exist_ok=True)

    for f_obj in incoming:
        if not f_obj or not f_obj.filename:
            continue
        ext = os.path.splitext(f_obj.filename)[1].lower()
        if ext not in VALID_EXTENSIONS:
            skipped_errors.append(f"{f_obj.filename} ({ext} inválido)")
            continue
        filename = os.path.basename(f_obj.filename)
        dest_path = os.path.join(ws["raw_images_dir"], filename)
        f_obj.save(dest_path)
        saved_names.append(filename)

    if not saved_names:
        err_detail = "; ".join(skipped_errors) if skipped_errors else "Nome de arquivo vazio."
        return jsonify({"error": f"Nenhuma imagem válida enviada ({err_detail})."}), 400

    last_file = saved_names[-1]
    last_sha = compute_file_sha256(os.path.join(ws["raw_images_dir"], last_file))[:12]
    log_event(
        f"{len(saved_names)} foto(s) adicionada(s) em '{ws['name']}': {', '.join(saved_names[:5])}"
        + ("..." if len(saved_names) > 5 else ""),
        level="SUCCESS",
    )

    return jsonify({
        "success": True,
        "filename": last_file,
        "uploaded_files": saved_names,
        "uploaded_count": len(saved_names),
        "url": f"/images/{last_file}?v={last_sha}",
    })


@app.route("/api/preview-filter", methods=["POST"])
def preview_filter():
    """Generates a local underwater-enhanced preview image inside `filtered_images/` without calling Colab."""
    ws = _get_ws()
    data = request.get_json() or {}
    image_name = data.get("image_name")
    filter_mode = (data.get("filter_mode") or "combined").lower().strip()
    quadrat_corners = data.get("quadrat_corners")

    if not image_name:
        return jsonify({"error": "Nenhuma imagem selecionada."}), 400

    fname = os.path.basename(image_name)
    image_path = os.path.join(ws["raw_images_dir"], fname)
    if not os.path.exists(image_path):
        return jsonify({"error": f"Imagem '{fname}' não encontrada."}), 404

    sha_short = compute_file_sha256(image_path)[:10]

    if filter_mode == "none":
        with Image.open(image_path) as im:
            w, h = im.size
        return jsonify({
            "success": True,
            "preview_url": f"/images/{fname}?v={sha_short}",
            "width": w,
            "height": h,
        })

    try:
        t0 = time.time()
        with Image.open(image_path) as orig_img:
            orig_rgb = orig_img.convert("RGB")
            w, h = orig_rgb.size
            enhanced = enhance_underwater_image(
                orig_rgb,
                filter_mode=filter_mode,
                quadrat_corners=quadrat_corners if (quadrat_corners and len(quadrat_corners) == 4) else None,
            )

        os.makedirs(ws["filtered_dir"], exist_ok=True)
        base_name = os.path.splitext(fname)[0]
        roi_tag = "roi" if (quadrat_corners and len(quadrat_corners) == 4) else "full"
        preview_filename = f"{base_name}_enhanced_{filter_mode}_{roi_tag}_{sha_short}.jpg"
        preview_path = os.path.join(ws["filtered_dir"], preview_filename)
        enhanced.save(preview_path, format="JPEG", quality=92)
        elapsed_ms = int((time.time() - t0) * 1000)
        log_event(f"Filtro '{filter_mode}' salvo em filtered_images para {fname} em {elapsed_ms}ms.")

        return jsonify({
            "success": True,
            "preview_url": f"/filtered/{preview_filename}?t={int(time.time() * 1000)}",
            "width": w,
            "height": h,
        })
    except Exception as e:
        log_event(f"Falha ao gerar prévia de filtro: {e}", level="ERROR")
        return jsonify({"error": str(e)}), 500


# =========================================================================
# SINGLE-IMAGE & BATCH PIPELINE EXECUTION ROUTES
# =========================================================================
def _extract_pipeline_params(data: dict):
    colab_url = (data.get("colab_url") or "").strip() or None
    quadrat_corners = data.get("quadrat_corners")
    if not (isinstance(quadrat_corners, list) and len(quadrat_corners) == 4):
        quadrat_corners = None

    return {
        "colab_url": colab_url,
        "min_area": int(data.get("min_area", 1500)),
        "iou_thresh": float(data.get("iou_thresh", 0.60)),
        "n_points_multi": int(data.get("n_points", 5)),
        "quadrat_width_cm": float(data.get("quadrat_width_cm", 50.0)),
        "quadrat_height_cm": float(data.get("quadrat_height_cm", 50.0)),
        "filter_mode": (data.get("filter_mode") or "combined").lower().strip(),
        "quadrat_corners": quadrat_corners,
        "render_on_enhanced": bool(data.get("render_on_enhanced", False)),
        "points_per_side": int(data.get("points_per_side", 32)),
        "pred_iou_thresh": float(data.get("pred_iou_thresh", 0.72)),
        "stability_score_thresh": float(data.get("stability_score_thresh", 0.62)),
        "crop_n_layers": int(data.get("crop_n_layers", 1)),
        "crop_n_points_downscale_factor": int(data.get("crop_n_points_downscale_factor", 2)),
    }


@app.route("/api/process", methods=["POST"])
def process_pipeline():
    """Executes CoralSCOP + BioCLIP 2.5 ReefNet on a single selected image in the active project."""
    ws = _get_ws()
    data = request.get_json() or {}
    image_name = data.get("image_name")
    if not image_name:
        log_event("Execução rejeitada: Nenhuma imagem selecionada.", level="ERROR")
        return jsonify({"error": "Nenhuma imagem selecionada."}), 400

    fname = os.path.basename(image_name)
    image_path = os.path.join(ws["raw_images_dir"], fname)
    if not os.path.exists(image_path):
        log_event(f"Imagem não encontrada: {image_path}", level="ERROR")
        return jsonify({"error": f"Imagem '{fname}' não encontrada na pasta do projeto."}), 404

    params = _extract_pipeline_params(data)
    fs_info = get_fewshot_summary(ws["fewshot_memory_path"])
    fs_status = f"ON ({fs_info['total_samples']} ref)" if fs_info["enabled"] else "OFF (Zero-Shot)"

    log_event(
        f"[{ws['name']}] Processando: {fname} | Destino: {params['colab_url'] or 'Simulado Local'} | "
        f"Filtro: {params['filter_mode']} | ROI 4-Cantos: {'Sim' if params['quadrat_corners'] else 'Não'} | "
        f"Few-Shot: {fs_status}"
    )

    try:
        t_start = time.time()
        result = run_hybrid_pipeline(
            image_path=image_path,
            output_dir=ws["exports_dir"],
            filtered_dir=ws["filtered_dir"],
            polygons_dir=ws["polygons_dir"],
            fewshot_memory_path=ws["fewshot_memory_path"],
            **params,
        )
        if not ws["is_demo"]:
            try:
                export_project_consolidated_csv(
                    raw_images_dir=ws["raw_images_dir"],
                    polygons_dir=ws["polygons_dir"],
                    exports_dir=ws["exports_dir"],
                )
            except Exception:
                pass

        total_sec = round(time.time() - t_start, 1)
        log_event(
            f"Concluído em {total_sec}s ({fname}): {result.get('total_colonies')} colônias "
            f"({result.get('total_coral_cm2')} cm² / {result.get('total_coral_cover_pct')}%).",
            level="SUCCESS",
        )

        return jsonify({
            "success": True,
            "data": result,
            "genera": CORAL_GENERA,
            "class_colors": CLASS_COLORS,
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
            "is_connection_error": "10054" in err_text or "Connection aborted" in err_text,
        }), 500


@app.route("/api/process/batch", methods=["POST"])
def process_batch_pipeline():
    """
    Executes CoralSCOP + BioCLIP 2.5 ReefNet in batch mode over:
      - batch_mode='all': all raw images in the active project (or only pending if `skip_processed=True`)
      - batch_mode='pending': only unprocessed and hash-mismatched images
      - batch_mode='selected': explicit `image_names` subset selected by the user
    Generates/updates `project_ecological_summary.csv` at completion.
    """
    ws = _get_ws()
    data = request.get_json() or {}
    batch_mode = (data.get("batch_mode") or "all").lower().strip()
    skip_processed = bool(data.get("skip_processed", False)) or (batch_mode == "pending")
    selected_names = data.get("image_names") or []
    corners_by_img = data.get("quadrat_corners_by_image") or {}

    files, _ = _scan_workspace_images(ws)
    by_name = {item["filename"]: item for item in files}

    if batch_mode == "selected":
        if not isinstance(selected_names, list) or not selected_names:
            return jsonify({"error": "Selecione pelo menos 1 foto para o processamento em lote."}), 400
        candidates = [by_name[os.path.basename(n)] for n in selected_names if os.path.basename(n) in by_name]
    else:
        candidates = list(files)

    targets = []
    skipped = []
    for item in candidates:
        if skip_processed and item["status"] == "processed":
            skipped.append(item["filename"])
        else:
            targets.append(item["filename"])

    if not targets:
        return jsonify({
            "success": True,
            "processed_count": 0,
            "skipped_count": len(skipped),
            "failed_count": 0,
            "results": [],
            "errors": [],
            "message": "Todas as fotos selecionadas já estão processadas e com hash SHA-256 íntegro.",
        })

    base_params = _extract_pipeline_params(data)
    log_event(
        f"[{ws['name']}] Iniciando processamento em LOTE ({batch_mode}): {len(targets)} foto(s) "
        f"({len(skipped)} já processadas puladas)..."
    )

    batch_results = []
    batch_errors = []
    last_full_result = None

    for idx, fname in enumerate(targets, 1):
        img_path = os.path.join(ws["raw_images_dir"], fname)
        img_params = dict(base_params)
        per_img_corners = corners_by_img.get(fname)
        if isinstance(per_img_corners, list) and len(per_img_corners) == 4:
            img_params["quadrat_corners"] = per_img_corners
        elif batch_mode != "selected" or len(targets) > 1:
            # Don't accidentally apply one photo's quadrat corners to other photos unless mapped
            if fname not in corners_by_img:
                img_params["quadrat_corners"] = None

        try:
            t0 = time.time()
            res = run_hybrid_pipeline(
                image_path=img_path,
                output_dir=ws["exports_dir"],
                filtered_dir=ws["filtered_dir"],
                polygons_dir=ws["polygons_dir"],
                fewshot_memory_path=ws["fewshot_memory_path"],
                **img_params,
            )
            dt = round(time.time() - t0, 1)
            last_full_result = res
            batch_results.append({
                "success": True,
                "filename": fname,
                "image_name": fname,
                "elapsed_sec": dt,
                "colonies_count": res.get("total_colonies", 0),
                "total_colonies": res.get("total_colonies", 0),
                "total_coral_cm2": res.get("total_coral_cm2", 0.0),
                "coral_cover_pct": res.get("total_coral_cover_pct", 0.0),
                "total_coral_cover_pct": res.get("total_coral_cover_pct", 0.0),
                "image_sha256_short": (res.get("image_sha256") or "")[:12],
            })
            log_event(
                f"[Lote {idx}/{len(targets)}] {fname} concluída em {dt}s "
                f"({res.get('total_colonies')} colônias | {res.get('total_coral_cover_pct')}%).",
                level="SUCCESS",
            )
        except Exception as e:
            err_str = str(e)
            batch_errors.append({"success": False, "filename": fname, "image_name": fname, "error": err_str})
            log_event(f"[Lote {idx}/{len(targets)}] Erro em {fname}: {err_str}", level="ERROR")
            if "10054" in err_str or "Connection aborted" in err_str:
                break

    summary_info = export_project_consolidated_csv(
        raw_images_dir=ws["raw_images_dir"],
        polygons_dir=ws["polygons_dir"],
        exports_dir=ws["exports_dir"],
        legacy_output_dir=ws["legacy_output_dir"],
    )
    updated_files, updated_counts = _scan_workspace_images(ws)

    return jsonify({
        "success": len(batch_errors) == 0 or len(batch_results) > 0,
        "successful": len(batch_results),
        "failed": len(batch_errors),
        "total": len(targets) + len(skipped),
        "processed_count": len(batch_results),
        "skipped_count": len(skipped),
        "failed_count": len(batch_errors),
        "results": batch_results,
        "errors": batch_errors,
        "last_result": last_full_result,
        "summary_csv_filename": summary_info["csv_filename"],
        "images": updated_files,
        "summary": updated_counts,
    })


# =========================================================================
# POST-PROCESSING COLONY, GROUPING, MANUAL POLYGON & FEW-SHOT ROUTES
# =========================================================================
@app.route("/api/colony/update", methods=["POST"])
def update_colony():
    """Manual 1-click colony edit (genus change, Non-Coral discard, or restore) on a hash-verified session."""
    ws = _get_ws()
    data = request.get_json() or {}
    image_name = data.get("image_name")
    colony_id = data.get("colony_id")
    action = data.get("action", "set_genus")
    new_genus = data.get("genus")

    if not image_name or colony_id is None:
        return jsonify({"error": "Parâmetros image_name e colony_id são obrigatórios."}), 400

    session, err_msg, code = _load_verified_session_or_error(image_name, ws)
    if not session:
        return jsonify({"error": err_msg}), code

    cid = int(colony_id)
    target = next((c for c in session.get("colonies", []) if int(c["id"]) == cid), None)
    if not target:
        return jsonify({"error": f"Colônia/Polígono #{cid} não encontrado."}), 404

    if action == "delete" or (action == "set_genus" and new_genus == NON_CORAL_LABEL):
        target["discarded"] = True
        target["discard_reason"] = "manual"
        target["manual_locked"] = True
        target["used_fewshot"] = False
        log_event(f"Polígono #{cid} ({image_name}) marcado como 'Não é Coral' (descartado do cálculo coralíneo).")
    elif action == "restore":
        if new_genus and new_genus in CORAL_GENERA:
            target["genus"] = new_genus
            target["color"] = CLASS_COLORS.get(new_genus, "#38bdf8")
        target["discarded"] = False
        target["discard_reason"] = ""
        target["manual_locked"] = True
        log_event(f"Polígono #{cid} ({image_name}) restaurado como coral ativo ({target['genus']}).")
    else:
        if new_genus not in CORAL_GENERA:
            return jsonify({"error": f"Gênero inválido '{new_genus}'. Permitidos apenas gêneros de corais ou 'Não é Coral'."}), 400

        old_genus = target["genus"]
        target["genus"] = new_genus
        target["color"] = CLASS_COLORS.get(new_genus, "#38bdf8")
        target["confidence"] = 1.0
        target["manual_locked"] = True
        target["used_fewshot"] = False
        target["discarded"] = False
        target["discard_reason"] = ""
        log_event(f"Rótulo da Colônia #{cid} ({image_name}) editado manualmente: {old_genus} -> {new_genus}.")

    updated_result = _render_ws_session(session, ws, recompute_unlocked=False)
    return jsonify({
        "success": True,
        "data": updated_result,
        "fewshot": get_fewshot_summary(ws["fewshot_memory_path"]),
    })


@app.route("/api/colony/teach", methods=["POST"])
def teach_colony_fewshot():
    """Saves 1024-D BioCLIP 2.5 visual signature into the active project's Few-Shot memory and re-evaluates."""
    ws = _get_ws()
    data = request.get_json() or {}
    image_name = data.get("image_name")
    colony_id = data.get("colony_id")
    new_genus = data.get("genus")

    if not image_name or colony_id is None or not new_genus:
        return jsonify({"error": "Parâmetros image_name, colony_id e genus são obrigatórios."}), 400
    if new_genus not in CORAL_GENERA and new_genus != NON_CORAL_LABEL:
        return jsonify({"error": f"Rótulo inválido '{new_genus}'. Permitidos apenas gêneros de corais ou 'Não é Coral'."}), 400

    session, err_msg, code = _load_verified_session_or_error(image_name, ws)
    if not session:
        return jsonify({"error": err_msg}), code

    cid = int(colony_id)
    target = next((c for c in session.get("colonies", []) if int(c["id"]) == cid), None)
    if not target:
        return jsonify({"error": f"Colônia/Polígono #{cid} não encontrado."}), 404

    emb = target.get("embedding")
    if not emb:
        return jsonify({"error": "Este polígono não possui vetor de assinatura visual BioCLIP salvo."}), 400

    old_state_map = {
        int(c["id"]): (c["genus"], bool(c.get("discarded", False)))
        for c in session.get("colonies", [])
    }

    fs_summary = add_fewshot_prototype(
        genus=new_genus,
        embedding=emb,
        source_image=os.path.basename(image_name),
        colony_id=cid,
        area_cm2=float(target.get("area_cm2", 0.0)),
        memory_path=ws["fewshot_memory_path"],
    )

    is_non_coral = new_genus == NON_CORAL_LABEL
    if is_non_coral:
        target["discarded"] = True
        target["discard_reason"] = "manual"
        target["manual_locked"] = True
        target["used_fewshot"] = True
    else:
        target["genus"] = new_genus
        target["color"] = CLASS_COLORS.get(new_genus, "#38bdf8")
        target["confidence"] = 1.0
        target["manual_locked"] = True
        target["used_fewshot"] = True
        target["discarded"] = False
        target["discard_reason"] = ""

    updated_result = _render_ws_session(session, ws, recompute_unlocked=True)

    changed_others = 0
    auto_discarded_others = 0
    auto_restored_others = 0
    for c in updated_result["colonies"]:
        other_id = int(c["id"])
        if other_id == cid:
            continue
        prev_genus, prev_disc = old_state_map.get(other_id, (c["genus"], False))
        now_disc = bool(c.get("discarded", False))
        if not prev_disc and now_disc:
            auto_discarded_others += 1
        elif prev_disc and not now_disc:
            auto_restored_others += 1
        elif not now_disc and prev_genus != c["genus"]:
            changed_others += 1

    label_display = NON_CORAL_DISPLAY if is_non_coral else new_genus
    log_event(
        f"Assinatura BioCLIP 2.5 ensinada em '{ws['name']}': Polígono #{cid} -> {label_display} "
        f"({fs_summary['total_samples']} ref | {changed_others} reclassificados | "
        f"{auto_discarded_others} não-corais filtrados automaticamente!).",
        level="SUCCESS",
    )

    return jsonify({
        "success": True,
        "data": updated_result,
        "fewshot": fs_summary,
        "taught_non_coral": is_non_coral,
        "changed_similar_colonies": changed_others,
        "auto_discarded_similar": auto_discarded_others,
        "auto_restored_similar": auto_restored_others,
    })


@app.route("/api/colony/group", methods=["POST"])
def group_colonies():
    """Groups 2+ selected polygons/colonies of the same Coral Genus into 1 Colony Group."""
    ws = _get_ws()
    data = request.get_json() or {}
    image_name = data.get("image_name")
    colony_ids = data.get("colony_ids")

    if not image_name or not isinstance(colony_ids, list):
        return jsonify({"error": "Parâmetros image_name e colony_ids (lista) são obrigatórios."}), 400

    session, err_msg, code = _load_verified_session_or_error(image_name, ws)
    if not session:
        return jsonify({"error": err_msg}), code

    try:
        group_info = group_colonies_in_session(session, colony_ids)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    updated_result = _render_ws_session(session, ws, recompute_unlocked=False)
    log_event(
        f"Polígonos agrupados em {image_name}: {group_info['merged_count']} itens unidos no "
        f"Grupo #{group_info['merged_into_id']} ({group_info['genus']}, {group_info['parts_count']} partes, "
        f"{group_info['area_cm2']} cm² / {group_info['area_pct']}%).",
        level="SUCCESS",
    )
    return jsonify({
        "success": True,
        "data": updated_result,
        "group_info": group_info,
        "fewshot": get_fewshot_summary(ws["fewshot_memory_path"]),
    })


@app.route("/api/colony/part", methods=["POST"])
def modify_colony_part():
    """Separates, discards, or ungroups sub-polygons of a multi-part Colony Group."""
    ws = _get_ws()
    data = request.get_json() or {}
    image_name = data.get("image_name")
    colony_id = data.get("colony_id")
    part_index = int(data.get("part_index", 0))
    action = data.get("action", "split")

    if not image_name or colony_id is None:
        return jsonify({"error": "Parâmetros image_name e colony_id são obrigatórios."}), 400

    session, err_msg, code = _load_verified_session_or_error(image_name, ws)
    if not session:
        return jsonify({"error": err_msg}), code

    try:
        part_info = modify_colony_part_in_session(
            session,
            colony_id=int(colony_id),
            part_index=part_index,
            action=action,
        )
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    updated_result = _render_ws_session(session, ws, recompute_unlocked=False)
    log_event(
        f"Edição de sub-polígono ({action}) no Grupo #{colony_id} ({image_name}): "
        f"{part_info.get('remaining_parts')} parte(s) restante(s).",
        level="INFO",
    )
    return jsonify({
        "success": True,
        "data": updated_result,
        "part_info": part_info,
        "fewshot": get_fewshot_summary(ws["fewshot_memory_path"]),
    })


@app.route("/api/colony/add", methods=["POST"])
def add_manual_colony():
    """Post-processing manual polygon demarcation for corals missed by CoralSCOP."""
    ws = _get_ws()
    data = request.get_json() or {}
    image_name = data.get("image_name")
    polygon_pts = data.get("polygon")
    genus = data.get("genus")
    colab_url = (data.get("colab_url") or "").strip() or None

    if not image_name or not isinstance(polygon_pts, list):
        return jsonify({"error": "Parâmetros image_name e polygon (vértices) são obrigatórios."}), 400

    session, err_msg, code = _load_verified_session_or_error(image_name, ws)
    if not session:
        return jsonify({"error": err_msg}), code

    try:
        add_info = add_manual_colony_in_session(
            session_data=session,
            polygon_points=polygon_pts,
            output_dir=ws["exports_dir"],
            genus=genus,
            colab_url=colab_url,
            filtered_dir=ws["filtered_dir"],
            fewshot_memory_path=ws["fewshot_memory_path"],
        )
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    updated_result = _render_ws_session(session, ws, recompute_unlocked=False)
    vec_note = "vetor BioCLIP 2.5 extraído na GPU!" if add_info["extracted_bioclip"] else (
        "assinatura local" if add_info["has_embedding"] else "sem vetor GPU (Colab offline)"
    )
    log_event(
        f"Novo polígono manual #{add_info['new_colony_id']} adicionado em {image_name}: "
        f"{add_info['genus']} ({add_info['area_cm2']} cm², {add_info['area_pct']}% | {vec_note}).",
        level="SUCCESS",
    )
    return jsonify({
        "success": True,
        "data": updated_result,
        "add_info": add_info,
        "fewshot": get_fewshot_summary(ws["fewshot_memory_path"]),
    })


@app.route("/api/colony/edit-polygon", methods=["POST"])
def edit_colony_polygon():
    """Post-processing vertex editing for an existing colony polygon (or sub-polygon of a group)."""
    ws = _get_ws()
    data = request.get_json() or {}
    image_name = data.get("image_name")
    colony_id = data.get("colony_id")
    part_index = int(data.get("part_index", 0))
    polygon_pts = data.get("polygon")
    colab_url = (data.get("colab_url") or "").strip() or None
    refresh_bioclip = bool(data.get("refresh_bioclip", True))

    if not image_name or colony_id is None or not isinstance(polygon_pts, list):
        return jsonify({"error": "Parâmetros image_name, colony_id e polygon são obrigatórios."}), 400

    session, err_msg, code = _load_verified_session_or_error(image_name, ws)
    if not session:
        return jsonify({"error": err_msg}), code

    try:
        edit_info = update_colony_polygon_vertices_in_session(
            session_data=session,
            colony_id=int(colony_id),
            part_index=part_index,
            polygon_points=polygon_pts,
            output_dir=ws["exports_dir"],
            colab_url=colab_url,
            refresh_bioclip=refresh_bioclip,
            filtered_dir=ws["filtered_dir"],
            fewshot_memory_path=ws["fewshot_memory_path"],
        )
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    updated_result = _render_ws_session(session, ws, recompute_unlocked=False)
    vec_note = " + vetor BioCLIP 2.5 atualizado" if edit_info["refreshed_bioclip"] else ""
    log_event(
        f"Borda do polígono #{colony_id} (parte #{part_index + 1}) editada em {image_name}: "
        f"nova área = {edit_info['area_cm2']} cm² ({edit_info['area_pct']}%){vec_note}.",
        level="SUCCESS",
    )
    return jsonify({
        "success": True,
        "data": updated_result,
        "edit_info": edit_info,
        "fewshot": get_fewshot_summary(ws["fewshot_memory_path"]),
    })


@app.route("/api/fewshot", methods=["GET"])
def fewshot_status():
    ws = _get_ws()
    return jsonify({"success": True, "fewshot": get_fewshot_summary(ws["fewshot_memory_path"])})


@app.route("/api/fewshot/toggle", methods=["POST"])
def fewshot_toggle():
    """Enables or disables Few-Shot memory for the active project and optionally re-evaluates the open image."""
    ws = _get_ws()
    data = request.get_json() or {}
    enabled = bool(data.get("enabled", True))
    image_name = data.get("image_name")

    fs_summary = set_fewshot_enabled(enabled, memory_path=ws["fewshot_memory_path"])
    log_event(f"Memória Few-Shot ({ws['name']}) {'ATIVADA' if enabled else 'DESATIVADA (Zero-Shot Puro)'}.")

    updated_result = None
    if image_name:
        session = load_pipeline_session(
            image_name,
            ws["exports_dir"],
            polygons_dir=ws["polygons_dir"],
            raw_images_dir=ws["raw_images_dir"],
        )
        if session:
            updated_result = _render_ws_session(session, ws, recompute_unlocked=True)

    return jsonify({
        "success": True,
        "fewshot": fs_summary,
        "data": updated_result,
    })


@app.route("/api/fewshot/clear", methods=["POST"])
def fewshot_clear():
    """Clears saved Few-Shot prototypes in the active project and resets Few-Shot locks on the open image."""
    ws = _get_ws()
    data = request.get_json() or {}
    image_name = data.get("image_name")

    fs_summary = clear_fewshot_memory(memory_path=ws["fewshot_memory_path"])
    log_event(f"Memória Few-Shot de '{ws['name']}' limpa pelo usuário (0 referências).", level="WARNING")

    updated_result = None
    if image_name:
        session = load_pipeline_session(
            image_name,
            ws["exports_dir"],
            polygons_dir=ws["polygons_dir"],
            raw_images_dir=ws["raw_images_dir"],
        )
        if session:
            for c in session.get("colonies", []):
                if c.get("discard_reason") == "fewshot_non_coral" or (c.get("used_fewshot") and c.get("discarded")):
                    c["discarded"] = False
                    c["discard_reason"] = ""
                    c["manual_locked"] = False
                elif not c.get("is_grouped") and c.get("discard_reason") != "manual":
                    c["manual_locked"] = False
            updated_result = _render_ws_session(session, ws, recompute_unlocked=True)

    return jsonify({
        "success": True,
        "fewshot": fs_summary,
        "data": updated_result,
    })


@app.route("/api/reclassify", methods=["POST"])
def reclassify_open_image():
    """Re-applies current Few-Shot / Zero-Shot state to the open hash-verified photo in milliseconds."""
    ws = _get_ws()
    data = request.get_json() or {}
    image_name = data.get("image_name")
    unlock_manual = bool(data.get("unlock_manual", False))

    if not image_name:
        return jsonify({"error": "Nenhuma imagem selecionada."}), 400

    session, err_msg, code = _load_verified_session_or_error(image_name, ws)
    if not session:
        return jsonify({"error": err_msg}), code

    if unlock_manual:
        for c in session.get("colonies", []):
            if not c.get("is_grouped") and c.get("discard_reason") != "manual":
                c["manual_locked"] = False

    updated_result = _render_ws_session(session, ws, recompute_unlocked=True)
    log_event(f"Reclassificação local instantânea aplicada em {image_name}.")
    return jsonify({
        "success": True,
        "data": updated_result,
        "fewshot": get_fewshot_summary(ws["fewshot_memory_path"]),
    })


@app.route("/api/download/csv/<filename>")
def download_csv(filename):
    """Downloads an ecological report CSV from the active project's `exports/` folder."""
    ws = _get_ws()
    safe_name = os.path.basename(filename)
    csv_path = os.path.join(ws["exports_dir"], safe_name)
    if os.path.exists(csv_path):
        return send_file(csv_path, as_attachment=True, download_name=safe_name)
    return jsonify({"error": "Relatório CSV não encontrado."}), 404


@app.route("/images/<path:filename>")
def serve_image(filename):
    ws = _get_ws()
    resp = send_from_directory(ws["raw_images_dir"], filename, max_age=0)
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return resp


@app.route("/filtered/<path:filename>")
def serve_filtered_image(filename):
    ws = _get_ws()
    safe_path = os.path.join(ws["filtered_dir"], os.path.basename(filename))
    if os.path.exists(safe_path):
        return send_from_directory(ws["filtered_dir"], os.path.basename(filename), max_age=0)
    return send_from_directory(ws["exports_dir"], os.path.basename(filename), max_age=0)


@app.route("/output/<path:filename>")
def serve_output(filename):
    ws = _get_ws()
    safe_base = os.path.basename(filename)
    exp_path = os.path.join(ws["exports_dir"], safe_base)
    if os.path.exists(exp_path):
        return send_from_directory(ws["exports_dir"], safe_base, max_age=0)
    return send_from_directory(ws["filtered_dir"], safe_base, max_age=0)


if __name__ == "__main__":
    print("\n" + "=" * 68)
    print("[*] CoralSCOP + BioCLIP 2.5 ReefNet Web App (Modo Projetos + Hash SHA-256)")
    print("[*] Acesse em seu navegador: http://127.0.0.1:5000")
    print("=" * 68 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
