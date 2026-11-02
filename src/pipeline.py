import os
import csv
import json
import copy
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
import cv2
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from src.sam_client import RemoteSAMClient
from src.coral_classifier import get_coral_classifier
from src.few_shot_memory import (
    CORAL_GENERA,
    CLASS_COLORS,
    load_fewshot_memory,
    get_fewshot_summary,
    fuse_zeroshot_and_fewshot
)
from src.geometry import (
    apply_hierarchical_nms,
    sample_interior_points,
    generate_approx_polygon
)
from src.preprocessing import (
    order_quad_corners,
    build_quadrat_mask,
    enhance_underwater_image,
    prepare_quadrat_roi_crop,
    clip_polygons_to_quadrat,
    build_quadrat_homography,
    compute_polygons_area_cm2
)
from src.project_manager import compute_file_sha256, VALID_IMAGE_EXTENSIONS


FILTER_LABELS = {
    "combined": "Combinado (Balanço de Branco + CLAHE)",
    "wb": "Balanço de Branco Subaquático",
    "clahe": "CLAHE (Realce de Textura LAB)",
    "none": "Original (Sem Filtro)"
}


def get_session_cache_path(image_filename: str, output_dir: str) -> str:
    base_name = os.path.splitext(os.path.basename(image_filename))[0]
    return os.path.join(output_dir, f"{base_name}_session.json")


def get_polygon_file_path(image_filename: str, polygons_dir: str, image_sha256: str) -> str:
    base_name = os.path.splitext(os.path.basename(image_filename))[0]
    h12 = (image_sha256 or "nohash")[:12]
    return os.path.join(polygons_dir, f"{base_name}_{h12}_polygons.json")


def inspect_image_polygon_status(
    image_filename: str,
    raw_images_dir: str,
    polygons_dir: str,
    legacy_output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Computes the raw image's live SHA-256 hash on disk and checks `polygons_dir` for a
    matching polygon/classification record.
    Returns status in {'processed', 'hash_mismatch', 'unprocessed', 'missing'}:
      - 'processed': polygon JSON exists AND full 64-char SHA-256 matches the raw image bytes.
      - 'hash_mismatch': a polygon JSON exists for this filename, but the raw image file was
        replaced/modified (SHA-256 differs) -> stale polygons are strictly disregarded (`session=None`).
      - 'unprocessed': no polygon JSON exists for this filename yet.
    """
    fname = os.path.basename(image_filename)
    raw_path = os.path.join(raw_images_dir, fname)
    if not os.path.isfile(raw_path):
        return {
            "status": "missing",
            "processed": False,
            "hash_mismatch": False,
            "image_sha256": None,
            "previous_sha256": None,
            "polygon_file": None,
            "session": None,
        }

    actual_sha256 = compute_file_sha256(raw_path)
    base_name = os.path.splitext(fname)[0]

    # 1. Primary lookup: hash-linked polygon file `<stem>_<sha12>_polygons.json` in polygons_dir
    if polygons_dir and os.path.isdir(polygons_dir):
        exact_path = get_polygon_file_path(fname, polygons_dir, actual_sha256)
        if os.path.isfile(exact_path):
            try:
                with open(exact_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if (
                    isinstance(data, dict)
                    and data.get("image_sha256") == actual_sha256
                    and os.path.basename(data.get("image_filename", "")) == fname
                ):
                    data["image"] = raw_path
                    data["polygon_filename"] = os.path.basename(exact_path)
                    return {
                        "status": "processed",
                        "processed": True,
                        "hash_mismatch": False,
                        "image_sha256": actual_sha256,
                        "previous_sha256": None,
                        "polygon_file": exact_path,
                        "session": data,
                    }
            except Exception:
                pass

    # 2. Optional legacy fallback (`<stem>_session.json` in Demo / legacy output_dir)
    mismatched_sha: Optional[str] = None
    mismatched_file: Optional[str] = None
    if legacy_output_dir and os.path.isdir(legacy_output_dir):
        legacy_path = get_session_cache_path(fname, legacy_output_dir)
        if os.path.isfile(legacy_path):
            try:
                with open(legacy_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and os.path.basename(data.get("image_filename", fname)) == fname:
                    saved_sha = data.get("image_sha256")
                    if saved_sha == actual_sha256 or not saved_sha:
                        data["image"] = raw_path
                        data["image_sha256"] = actual_sha256
                        data["polygon_filename"] = os.path.basename(legacy_path)
                        return {
                            "status": "processed",
                            "processed": True,
                            "hash_mismatch": False,
                            "image_sha256": actual_sha256,
                            "previous_sha256": None,
                            "polygon_file": legacy_path,
                            "session": data,
                        }
                    else:
                        mismatched_sha = saved_sha
                        mismatched_file = legacy_path
            except Exception:
                pass

    # 3. Scan polygons_dir for any stale polygon file belonging to `fname` with an older SHA-256
    prefix = f"{base_name}_"
    if polygons_dir and os.path.isdir(polygons_dir):
        for entry in sorted(os.listdir(polygons_dir)):
            if not (entry.startswith(prefix) and entry.endswith("_polygons.json")):
                continue
            cand_path = os.path.join(polygons_dir, entry)
            try:
                with open(cand_path, "r", encoding="utf-8") as f:
                    cand = json.load(f)
                if isinstance(cand, dict) and os.path.basename(cand.get("image_filename", "")) == fname:
                    old_sha = cand.get("image_sha256")
                    if old_sha and old_sha != actual_sha256:
                        mismatched_sha = old_sha
                        mismatched_file = cand_path
                        break
            except Exception:
                continue

    if mismatched_sha:
        return {
            "status": "hash_mismatch",
            "processed": False,
            "hash_mismatch": True,
            "image_sha256": actual_sha256,
            "previous_sha256": mismatched_sha,
            "polygon_file": mismatched_file,
            "session": None,
        }

    return {
        "status": "unprocessed",
        "processed": False,
        "hash_mismatch": False,
        "image_sha256": actual_sha256,
        "previous_sha256": None,
        "polygon_file": None,
        "session": None,
    }


def load_pipeline_session(
    image_filename: str,
    output_dir: str,
    polygons_dir: Optional[str] = None,
    raw_images_dir: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Loads a saved polygon/classification session ONLY IF its recorded `image_sha256` matches
    the current raw image file on disk. If the image was replaced by a different file with the
    same filename, returns None so stale polygons are automatically disregarded.
    """
    fname = os.path.basename(image_filename)
    p_dir = polygons_dir or output_dir

    if raw_images_dir:
        legacy_dir = output_dir if (polygons_dir is None or polygons_dir == output_dir) else None
        status_info = inspect_image_polygon_status(
            image_filename=fname,
            raw_images_dir=raw_images_dir,
            polygons_dir=p_dir,
            legacy_output_dir=legacy_dir,
        )
        return status_info["session"] if status_info["status"] == "processed" else None

    # Direct fallback (when raw_images_dir is not passed explicitly): check polygons_dir & output_dir
    base_name = os.path.splitext(fname)[0]
    candidates: List[str] = []
    if os.path.isdir(p_dir):
        for entry in sorted(os.listdir(p_dir), reverse=True):
            if entry.startswith(f"{base_name}_") and entry.endswith("_polygons.json"):
                candidates.append(os.path.join(p_dir, entry))
    legacy_path = get_session_cache_path(fname, output_dir)
    if os.path.isfile(legacy_path):
        candidates.append(legacy_path)

    for cpath in candidates:
        try:
            with open(cpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                continue
            if os.path.basename(data.get("image_filename", fname)) != fname:
                continue
            img_disk = data.get("image")
            saved_sha = data.get("image_sha256")
            if img_disk and os.path.isfile(img_disk) and saved_sha:
                if compute_file_sha256(img_disk) != saved_sha:
                    continue
            return data
        except Exception:
            continue
    return None


def save_pipeline_session(
    session_data: Dict[str, Any],
    output_dir: str,
    polygons_dir: Optional[str] = None,
) -> str:
    """
    Persists polygons, classifications, 4-corner homography calibration, and 1024-D BioCLIP 2.5
    embeddings into `polygons_dir` (bound by the raw image's full SHA-256 hash).
    Automatically removes obsolete polygon files of the same `image_filename` with older hashes.
    """
    p_dir = polygons_dir or output_dir
    os.makedirs(p_dir, exist_ok=True)

    fname = os.path.basename(session_data["image_filename"])
    img_path = session_data.get("image")
    if img_path and os.path.isfile(img_path):
        # Always synchronize with the exact SHA-256 of the image being saved
        if not session_data.get("image_sha256"):
            session_data["image_sha256"] = compute_file_sha256(img_path)

    sha256 = session_data.get("image_sha256") or ""
    session_data["schema"] = "coralscop-polygons-v1"
    session_data["image_hash_short"] = sha256[:12] if sha256 else ""
    session_data["saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if sha256:
        poly_path = get_polygon_file_path(fname, p_dir, sha256)
    else:
        poly_path = get_session_cache_path(fname, p_dir)

    session_data["polygon_filename"] = os.path.basename(poly_path)
    with open(poly_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False)

    # Remove stale polygon files for the exact same `fname` that had a previous SHA-256 hash
    base_name = os.path.splitext(fname)[0]
    for entry in os.listdir(p_dir):
        if entry == os.path.basename(poly_path):
            continue
        if (entry.startswith(f"{base_name}_") and entry.endswith("_polygons.json")) or entry == f"{base_name}_session.json":
            stale_candidate = os.path.join(p_dir, entry)
            try:
                with open(stale_candidate, "r", encoding="utf-8") as sf:
                    sdata = json.load(sf)
                if isinstance(sdata, dict) and os.path.basename(sdata.get("image_filename", "")) == fname:
                    os.remove(stale_candidate)
            except Exception:
                pass

    return poly_path


def session_to_public_payload(
    session_data: Dict[str, Any],
    fewshot_memory_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Converts a loaded `session_data` dict into the lightweight JSON payload expected by the
    frontend (stripping per-colony 1024-float vectors while keeping `has_embedding` and `image_sha256`).
    """
    fewshot_summary = get_fewshot_summary(fewshot_memory_path)
    public_colonies = []
    for col in session_data.get("colonies", []):
        c_copy = {k: v for k, v in col.items() if k not in ("embedding", "zero_shot_sims")}
        c_copy["has_embedding"] = bool(col.get("embedding"))
        public_colonies.append(c_copy)

    public_result = {k: v for k, v in session_data.items() if k != "colonies"}
    public_result["colonies"] = public_colonies
    public_result["fewshot_summary"] = fewshot_summary
    return public_result


def export_project_consolidated_csv(
    raw_images_dir: str,
    polygons_dir: str,
    exports_dir: str,
    legacy_output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates `<exports_dir>/project_ecological_summary.csv` aggregating all hash-verified
    processed images in the project (excluding unprocessed or hash-mismatched replaced images).
    """
    os.makedirs(exports_dir, exist_ok=True)
    summary_csv_path = os.path.join(exports_dir, "project_ecological_summary.csv")

    rows = []
    if os.path.isdir(raw_images_dir):
        for fname in sorted(os.listdir(raw_images_dir)):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in VALID_IMAGE_EXTENSIONS:
                continue
            st = inspect_image_polygon_status(
                image_filename=fname,
                raw_images_dir=raw_images_dir,
                polygons_dir=polygons_dir,
                legacy_output_dir=legacy_output_dir,
            )
            if st["status"] != "processed" or not st["session"]:
                continue
            sess = st["session"]
            g_map_cm2 = {g: 0.0 for g in CORAL_GENERA}
            g_map_pct = {g: 0.0 for g in CORAL_GENERA}
            for item in sess.get("genus_summary", []):
                g = item.get("genus")
                if g in g_map_cm2:
                    g_map_cm2[g] = float(item.get("area_cm2", 0.0))
                    g_map_pct[g] = float(item.get("coverage_pct", 0.0))

            row = [
                fname,
                (st["image_sha256"] or "")[:16],
                "Yes" if sess.get("has_quadrat_roi") else "No",
                sess.get("total_area_cm2", 2500.0),
                sess.get("total_colonies", 0),
                sess.get("discarded_count", 0),
                sess.get("total_coral_cm2", 0.0),
                sess.get("total_coral_cover_pct", 0.0),
            ]
            for g in CORAL_GENERA:
                row.append(round(g_map_cm2[g], 2))
                row.append(round(g_map_pct[g], 2))
            rows.append(row)

    header = [
        "Image_Filename",
        "Image_SHA256_16",
        "Has_4Corner_Quadrat",
        "Quadrat_Area_cm2",
        "Active_Colonies_Groups",
        "Discarded_NonCoral",
        "Total_Coral_cm2",
        "Total_Coral_Cover_Pct",
    ]
    for g in CORAL_GENERA:
        header.append(f"{g}_cm2")
        header.append(f"{g}_Pct")

    with open(summary_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    return {
        "csv_path": summary_csv_path,
        "csv_filename": os.path.basename(summary_csv_path),
        "processed_images_count": len(rows),
    }


def _get_session_calibration(
    session_data: Dict[str, Any]
) -> Tuple[int, int, float, Optional[np.ndarray], float]:
    """
    Reconstructs perspective homography H and pixel-to-cm² calibration constants from session_data.
    """
    w = max(1, int(session_data.get("image_width", 1000)))
    h = max(1, int(session_data.get("image_height", 1000)))
    quadrat_w = float(session_data.get("quadrat_width_cm", 50.0))
    quadrat_h = float(session_data.get("quadrat_height_cm", 50.0))
    total_area_cm2 = float(session_data.get("total_area_cm2", quadrat_w * quadrat_h))

    quad_corners = session_data.get("quadrat_corners")
    has_roi = bool(session_data.get("has_quadrat_roi")) and isinstance(quad_corners, list) and len(quad_corners) == 4

    if has_roi:
        ordered = order_quad_corners(quad_corners)
        homography_matrix = build_quadrat_homography(ordered, quadrat_w, quadrat_h)
        eff_px = int(session_data.get("effective_area_pixels") or max(1, int(round(cv2.contourArea(ordered)))))
    else:
        homography_matrix = None
        eff_px = int(session_data.get("effective_area_pixels") or max(1, w * h))

    fallback_cm2_per_pixel = total_area_cm2 / float(max(1, eff_px))
    return w, h, total_area_cm2, homography_matrix, fallback_cm2_per_pixel


def recompute_colony_geometry(col: Dict[str, Any], session_data: Dict[str, Any]) -> None:
    """
    Recomputes union pixel area, perspective-rectified area_cm2, coverage %, bounding box,
    interior centroid, and sample points for a colony after polygon grouping or part removal.
    """
    w, h, total_area_cm2, homography_matrix, fallback_cm2_per_pixel = _get_session_calibration(session_data)

    raw_polys = col.get("polygons") or ([col["polygon"]] if col.get("polygon") else [])
    valid_polys = [p for p in raw_polys if isinstance(p, list) and len(p) >= 3]
    valid_polys.sort(key=lambda p: float(cv2.contourArea(np.array(p, dtype=np.float32))), reverse=True)

    col["polygons"] = valid_polys
    col["polygon"] = valid_polys[0] if valid_polys else []
    col["parts_count"] = len(valid_polys)

    if not valid_polys:
        return

    all_pts = np.array([pt for p in valid_polys for pt in p], dtype=np.int32)
    x0 = max(0, int(all_pts[:, 0].min()))
    y0 = max(0, int(all_pts[:, 1].min()))
    x1 = min(w, int(all_pts[:, 0].max()) + 1)
    y1 = min(h, int(all_pts[:, 1].max()) + 1)
    bw = max(1, x1 - x0)
    bh = max(1, y1 - y0)

    local_mask = np.zeros((bh + 2, bw + 2), dtype=np.uint8)
    shifted = [
        (np.array(p, dtype=np.int32) - np.array([x0 - 1, y0 - 1], dtype=np.int32)).reshape((-1, 1, 2))
        for p in valid_polys
    ]
    cv2.fillPoly(local_mask, shifted, 1)
    union_area_px = max(1, int(np.count_nonzero(local_mask)))

    # Centroid anchored on the largest polygon part so the label stays on actual coral tissue
    largest_np = np.array(valid_polys[0], dtype=np.int32)
    M = cv2.moments(largest_np)
    if M["m00"] > 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
    else:
        cx = x0 + bw // 2
        cy = y0 + bh // 2

    if cv2.pointPolygonTest(largest_np, (float(cx), float(cy)), False) < 0:
        ys_local, xs_local = np.nonzero(local_mask)
        if len(xs_local) > 0:
            mid_idx = len(xs_local) // 2
            cx = int(xs_local[mid_idx]) + x0 - 1
            cy = int(ys_local[mid_idx]) + y0 - 1

    area_cm2 = compute_polygons_area_cm2(
        polygons=valid_polys,
        homography_matrix=homography_matrix,
        fallback_cm2_per_pixel=fallback_cm2_per_pixel,
        area_pixels=union_area_px
    )
    sum_poly_px = sum(float(cv2.contourArea(np.array(p, dtype=np.float32))) for p in valid_polys)
    if homography_matrix is not None and sum_poly_px > union_area_px * 1.03 and sum_poly_px > 0:
        area_cm2 *= (float(union_area_px) / sum_poly_px)

    cov_pct = (area_cm2 / total_area_cm2) * 100.0 if total_area_cm2 > 0 else 0.0

    col["bbox"] = [x0, y0, bw, bh]
    col["bbox_pct"] = {
        "left": (x0 / w) * 100.0,
        "top": (y0 / h) * 100.0,
        "width": (bw / w) * 100.0,
        "height": (bh / h) * 100.0
    }
    col["centroid"] = [int(cy), int(cx)]
    col["area_pixels"] = union_area_px
    col["area_cm2"] = round(area_cm2, 2)
    col["area_pct"] = round(cov_pct, 2)

    pts = sample_interior_points(
        bbox=col["bbox"],
        polygon=col["polygon"],
        polygons=valid_polys,
        centroid=col["centroid"]
    )
    col["sample_points"] = pts
    col["sample_points_count"] = len(pts)


def group_colonies_in_session(session_data: Dict[str, Any], colony_ids: List[int]) -> Dict[str, Any]:
    """
    Merges 2 or more active polygons/colonies of the EXACT SAME Coral Genus into 1 Colony Group.
    Preserves individual sub-polygons inside `polygons` so parts can be removed/split later.
    """
    clean_ids: List[int] = []
    for raw_id in (colony_ids or []):
        cid = int(raw_id)
        if cid not in clean_ids:
            clean_ids.append(cid)

    if len(clean_ids) < 2:
        raise ValueError("Selecione pelo menos 2 polígonos/colônias para formar um grupo.")

    colonies = session_data.get("colonies", [])
    by_id = {int(c["id"]): c for c in colonies}

    selected: List[Dict[str, Any]] = []
    for cid in clean_ids:
        if cid not in by_id:
            raise ValueError(f"Colônia/Polígono #{cid} não encontrado na sessão.")
        c = by_id[cid]
        if c.get("discarded", False):
            raise ValueError(
                f"O polígono #{cid} está descartado como 'Não é Coral'. Restaure-o antes de agrupar."
            )
        selected.append(c)

    distinct_genera = sorted({c["genus"] for c in selected})
    if len(distinct_genera) > 1:
        raise ValueError(
            f"Agrupamento bloqueado: os polígonos selecionados possuem classificações diferentes "
            f"({', '.join(distinct_genera)}). Corrija primeiro o polígono divergente "
            f"(com '✏️ Apenas Corrigir' ou '🧠 Ensinar BioCLIP') para unificar o gênero antes de agrupar."
        )

    primary = min(selected, key=lambda c: int(c["id"]))
    primary_id = int(primary["id"])
    secondary_ids = {int(c["id"]) for c in selected if int(c["id"]) != primary_id}

    merged_polys: List[List[List[int]]] = []
    total_weight = 0.0
    weighted_emb: Optional[np.ndarray] = None
    weighted_sims = {g: 0.0 for g in CORAL_GENERA}
    has_sims = False

    for c in selected:
        c_polys = c.get("polygons") or ([c["polygon"]] if c.get("polygon") else [])
        for p in c_polys:
            if isinstance(p, list) and len(p) >= 3:
                merged_polys.append(p)

        w_area = max(1.0, float(c.get("area_pixels", 1)))
        total_weight += w_area

        emb = c.get("embedding")
        if emb and isinstance(emb, list) and len(emb) >= 8:
            vec = np.array(emb, dtype=np.float64)
            if weighted_emb is None:
                weighted_emb = vec * w_area
            elif weighted_emb.shape == vec.shape:
                weighted_emb += vec * w_area

        zs = c.get("zero_shot_sims")
        if isinstance(zs, dict) and zs:
            has_sims = True
            for g in CORAL_GENERA:
                weighted_sims[g] += float(zs.get(g, 0.0)) * w_area

    if weighted_emb is not None and total_weight > 0:
        norm = float(np.linalg.norm(weighted_emb))
        if norm > 1e-8:
            primary["embedding"] = [round(float(x), 5) for x in (weighted_emb / norm).tolist()]

    if has_sims and total_weight > 0:
        primary["zero_shot_sims"] = {g: round(weighted_sims[g] / total_weight, 5) for g in CORAL_GENERA}

    primary["polygons"] = merged_polys
    primary["is_grouped"] = True
    primary["manual_locked"] = True
    primary["discarded"] = False
    primary["discard_reason"] = ""
    primary["confidence"] = round(
        sum(float(c.get("confidence", 1.0)) * max(1.0, float(c.get("area_pixels", 1))) for c in selected) / max(1.0, total_weight),
        4
    )

    recompute_colony_geometry(primary, session_data)
    session_data["colonies"] = [c for c in colonies if int(c["id"]) not in secondary_ids]

    return {
        "merged_into_id": primary_id,
        "merged_count": len(selected),
        "parts_count": len(primary["polygons"]),
        "genus": primary["genus"],
        "area_cm2": primary["area_cm2"],
        "area_pct": primary["area_pct"]
    }


def modify_colony_part_in_session(
    session_data: Dict[str, Any],
    colony_id: int,
    part_index: int = 0,
    action: str = "split"
) -> Dict[str, Any]:
    """
    Removes or separates sub-polygons from a multi-polygon Colony/Group:
      - 'split': detaches `polygons[part_index]` as a new active single-polygon colony
      - 'discard_part': removes `polygons[part_index]` from the group and marks that part discarded
      - 'explode': ungroups all sub-polygons of `colony_id` into independent colonies
    """
    colonies = session_data.get("colonies", [])
    cid = int(colony_id)
    target_idx = next((i for i, c in enumerate(colonies) if int(c["id"]) == cid), None)
    if target_idx is None:
        raise ValueError(f"Colônia/Grupo #{cid} não encontrado.")

    target = colonies[target_idx]
    polys = list(target.get("polygons") or ([target["polygon"]] if target.get("polygon") else []))
    max_id = max((int(c["id"]) for c in colonies), default=0)

    def _clone_single_part(poly_pts: List[List[int]], new_id: int, discarded_flag: bool = False) -> Dict[str, Any]:
        cloned = copy.deepcopy(target)
        cloned["id"] = new_id
        cloned["polygons"] = [poly_pts]
        cloned["polygon"] = poly_pts
        cloned["parts_count"] = 1
        cloned["is_grouped"] = False
        cloned["manual_locked"] = True
        cloned["discarded"] = discarded_flag
        cloned["discard_reason"] = "manual" if discarded_flag else ""
        recompute_colony_geometry(cloned, session_data)
        return cloned

    if action == "split":
        if len(polys) < 2:
            raise ValueError("Esta colônia possui apenas 1 polígono e não tem sub-partes para separar.")
        if not (0 <= part_index < len(polys)):
            raise ValueError(f"Índice de sub-polígono inválido ({part_index}).")

        extracted = polys.pop(part_index)
        target["polygons"] = polys
        if len(polys) <= 1:
            target["is_grouped"] = False
        recompute_colony_geometry(target, session_data)

        new_col = _clone_single_part(extracted, max_id + 1, discarded_flag=False)
        colonies.insert(target_idx + 1, new_col)
        return {
            "action": "split",
            "target_id": cid,
            "new_colony_id": new_col["id"],
            "remaining_parts": len(target["polygons"])
        }

    elif action == "discard_part":
        if not (0 <= part_index < len(polys)):
            raise ValueError(f"Índice de sub-polígono inválido ({part_index}).")
        if len(polys) <= 1:
            target["discarded"] = True
            target["discard_reason"] = "manual"
            target["manual_locked"] = True
            return {
                "action": "discard_part",
                "target_id": cid,
                "discarded_colony_id": cid,
                "remaining_parts": 0
            }

        extracted = polys.pop(part_index)
        target["polygons"] = polys
        if len(polys) <= 1:
            target["is_grouped"] = False
        recompute_colony_geometry(target, session_data)

        disc_col = _clone_single_part(extracted, max_id + 1, discarded_flag=True)
        colonies.append(disc_col)
        return {
            "action": "discard_part",
            "target_id": cid,
            "discarded_colony_id": disc_col["id"],
            "remaining_parts": len(target["polygons"])
        }

    elif action == "explode":
        if len(polys) < 2:
            raise ValueError("Esta colônia possui apenas 1 polígono (não é um grupo).")

        target["polygons"] = [polys[0]]
        target["is_grouped"] = False
        recompute_colony_geometry(target, session_data)

        created_ids: List[int] = []
        insert_pos = target_idx + 1
        for extra_poly in polys[1:]:
            max_id += 1
            new_col = _clone_single_part(extra_poly, max_id, discarded_flag=False)
            colonies.insert(insert_pos, new_col)
            insert_pos += 1
            created_ids.append(max_id)

        return {
            "action": "explode",
            "target_id": cid,
            "created_ids": created_ids,
            "remaining_parts": 1
        }

    else:
        raise ValueError(f"Ação de sub-polígono desconhecida: '{action}'.")


def _load_classification_image_for_session(
    session_data: Dict[str, Any],
    output_dir: str,
    filtered_dir: Optional[str] = None,
) -> Image.Image:
    """
    Loads the color-compensated RGB image for single-colony BioCLIP 2.5 multi-scale feature extraction.
    Reuses the cached enhanced JPEG in `filtered_dir` (or `output_dir`) whenever available.
    """
    filter_mode = (session_data.get("filter_mode") or "combined").lower().strip()
    enh_name = session_data.get("enhanced_image_filename")
    if filter_mode != "none" and enh_name:
        for base_d in ([filtered_dir, output_dir] if filtered_dir else [output_dir]):
            if base_d:
                enh_path = os.path.join(base_d, enh_name)
                if os.path.exists(enh_path):
                    with Image.open(enh_path) as im:
                        return im.convert("RGB")

    with Image.open(session_data["image"]) as orig_im:
        orig_rgb = orig_im.convert("RGB")
    quad_corners = session_data.get("quadrat_corners") if session_data.get("has_quadrat_roi") else None
    target_mode = "wb" if filter_mode == "none" else filter_mode
    return enhance_underwater_image(orig_rgb, filter_mode=target_mode, quadrat_corners=quad_corners)


def extract_single_colony_bioclip_features(
    col: Dict[str, Any],
    session_data: Dict[str, Any],
    output_dir: str,
    colab_url: Optional[str] = None,
    filtered_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extracts the 1024-D BioCLIP 2.5 ReefNet multi-scale signature vector (Macro + up to 4 native
    224x224 Micro corallite crops) and Zero-Shot similarities for a manually drawn or edited polygon.
    """
    clean_url = (colab_url or "").strip() or None
    pts = col.get("sample_points") or [tuple(col.get("centroid", [0, 0]))]

    if clean_url:
        try:
            clf_img = _load_classification_image_for_session(session_data, output_dir, filtered_dir=filtered_dir)
            sam_client = RemoteSAMClient(colab_url=clean_url, timeout=25)
            bioclip_resp = sam_client.classify_colonies_bioclip(
                enhanced_image=clf_img,
                masks=[col],
                colony_points_list=[pts]
            )
            if bioclip_resp and bioclip_resp.get("results"):
                return {
                    "used_remote_bioclip": True,
                    "used_local_fallback": False,
                    "raw": bioclip_resp["results"][0]
                }
        except Exception as e:
            print(f"[!] Aviso ao extrair vetor BioCLIP 2.5 do polígono manual/editado ({e}).")

    # If the session itself was generated in offline local simulation mode, extract compatible local features
    if not session_data.get("is_bioclip", False):
        try:
            clf_img = _load_classification_image_for_session(session_data, output_dir, filtered_dir=filtered_dir)
            local_clf = get_coral_classifier()
            local_res = local_clf.extract_offline_bioclip_like(
                pil_image=clf_img,
                masks=[col],
                colony_points_list=[pts]
            )
            if local_res:
                return {
                    "used_remote_bioclip": False,
                    "used_local_fallback": True,
                    "raw": local_res[0]
                }
        except Exception as e:
            print(f"[!] Aviso no fallback local de polígono manual ({e}).")

    return {
        "used_remote_bioclip": False,
        "used_local_fallback": False,
        "raw": None
    }


def _sanitize_and_clip_manual_polygon(
    polygon_points: List[List[float]],
    session_data: Dict[str, Any],
    simplify_dense_freehand: bool = False
) -> List[List[List[int]]]:
    """
    Validates user-supplied polygon vertices [x, y], optionally simplifies ultra-dense freehand
    strokes (>140 vertices), and clips strictly to the 4-corner quadrat ROI ONLY if any vertex
    extends outside the quadrat boundary (preserving exact user vertices when already inside).
    """
    if not isinstance(polygon_points, list) or len(polygon_points) < 3:
        raise ValueError("O polígono precisa ter pelo menos 3 vértices.")

    w = max(1, int(session_data.get("image_width", 1000)))
    h = max(1, int(session_data.get("image_height", 1000)))

    clean_pts: List[List[int]] = []
    for pt in polygon_points:
        if not isinstance(pt, (list, tuple)) or len(pt) < 2:
            continue
        px = max(0, min(w - 1, int(round(float(pt[0])))))
        py = max(0, min(h - 1, int(round(float(pt[1])))))
        if not clean_pts or clean_pts[-1] != [px, py]:
            clean_pts.append([px, py])

    if len(clean_pts) > 1 and clean_pts[0] == clean_pts[-1]:
        clean_pts.pop()

    if len(clean_pts) < 3:
        raise ValueError("O polígono precisa ter pelo menos 3 vértices distintos.")

    if simplify_dense_freehand and len(clean_pts) > 140:
        cnt = np.array(clean_pts, dtype=np.int32).reshape((-1, 1, 2))
        approx = cv2.approxPolyDP(cnt, epsilon=1.5, closed=True)
        if len(approx) >= 3:
            clean_pts = [[int(p[0]), int(p[1])] for p in approx.reshape(-1, 2).tolist()]

    raw_area = float(cv2.contourArea(np.array(clean_pts, dtype=np.float32)))
    if raw_area < 25.0:
        raise ValueError("O polígono desenhado é muito pequeno (área menor que 25 pixels).")

    quad_corners = session_data.get("quadrat_corners")
    has_roi = bool(session_data.get("has_quadrat_roi")) and isinstance(quad_corners, list) and len(quad_corners) == 4
    if has_roi:
        ordered = order_quad_corners(quad_corners)
        quad_cnt = np.round(ordered).astype(np.int32)
        any_outside = any(
            cv2.pointPolygonTest(quad_cnt, (float(px), float(py)), False) < 0
            for px, py in clean_pts
        )
        if any_outside:
            full_mask = build_quadrat_mask(w, h, ordered)
            c_polys, c_area, _, _ = clip_polygons_to_quadrat([clean_pts], full_mask)
            if c_area < 25 or not c_polys:
                raise ValueError(
                    "O polígono desenhado está fora da área demarcada pelos 4 cantos do quadrante."
                )
            return c_polys

    return [clean_pts]


def add_manual_colony_in_session(
    session_data: Dict[str, Any],
    polygon_points: List[List[float]],
    output_dir: str,
    genus: Optional[str] = None,
    colab_url: Optional[str] = None,
    filtered_dir: Optional[str] = None,
    fewshot_memory_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates a new post-processing manually drawn coral colony in `session_data`, computes exact
    perspective-rectified area_cm2 via 4-point Homography, and extracts the 1024-D BioCLIP 2.5
    ReefNet vector from Colab whenever available (for auto-classification and/or Few-Shot teaching).
    """
    polys = _sanitize_and_clip_manual_polygon(
        polygon_points=polygon_points,
        session_data=session_data,
        simplify_dense_freehand=True
    )

    colonies = session_data.get("colonies", [])
    new_id = max((int(c["id"]) for c in colonies), default=0) + 1
    auto_mode = (not genus) or (genus == "__AUTO_BIOCLIP__")

    if not auto_mode and genus not in CORAL_GENERA:
        raise ValueError(f"Gênero inválido '{genus}'. Selecione um dos 11 gêneros de corais.")

    new_col: Dict[str, Any] = {
        "id": new_id,
        "genus": genus if not auto_mode else CORAL_GENERA[0],
        "confidence": 1.0,
        "zero_shot_genus": genus if not auto_mode else CORAL_GENERA[0],
        "used_fewshot": False,
        "best_prototype_sim": 0.0,
        "non_coral_sim": 0.0,
        "manual_locked": not auto_mode,
        "is_manual_drawn": True,
        "is_geometry_edited": False,
        "is_grouped": False,
        "parts_count": len(polys),
        "discarded": False,
        "discard_reason": "",
        "consensus_ratio": 1.0,
        "sample_points_count": 1,
        "views_count": 1,
        "sample_points": [],
        "color": CLASS_COLORS.get(genus if not auto_mode else CORAL_GENERA[0], "#38bdf8"),
        "bbox": [0, 0, 1, 1],
        "bbox_pct": {"left": 0.0, "top": 0.0, "width": 0.0, "height": 0.0},
        "polygon": polys[0],
        "polygons": polys,
        "centroid": [0, 0],
        "area_pixels": 1,
        "area_cm2": 0.0,
        "area_pct": 0.0,
        "alternatives": [],
        "zero_shot_sims": {},
        "embedding": []
    }

    recompute_colony_geometry(new_col, session_data)

    # Extract BioCLIP 2.5 ReefNet 1024-D vector (bonus!) when Colab is connected (or local fallback in offline mode)
    feat_info = extract_single_colony_bioclip_features(
        col=new_col,
        session_data=session_data,
        output_dir=output_dir,
        colab_url=colab_url,
        filtered_dir=filtered_dir,
    )

    if feat_info["raw"]:
        raw_c = feat_info["raw"]
        zs_sims = raw_c.get("zero_shot_sims", {})
        emb = raw_c.get("embedding", [])
        mem_data = load_fewshot_memory(fewshot_memory_path)
        fused = fuse_zeroshot_and_fewshot(
            zero_shot_sims=zs_sims,
            embedding=emb,
            memory_data=mem_data
        )
        new_col["embedding"] = emb
        new_col["zero_shot_sims"] = zs_sims
        new_col["zero_shot_genus"] = fused["zero_shot_genus"]
        new_col["best_prototype_sim"] = fused["best_prototype_sim"]
        new_col["non_coral_sim"] = fused.get("non_coral_sim", 0.0)
        new_col["alternatives"] = fused["alternatives"]
        new_col["consensus_ratio"] = round(float(raw_c.get("consensus_ratio", 1.0)), 3)
        new_col["views_count"] = int(raw_c.get("views_count", new_col["sample_points_count"] + 1))

        if auto_mode:
            new_col["genus"] = fused["genus"]
            new_col["confidence"] = round(fused["confidence"], 4)
            new_col["used_fewshot"] = fused["used_fewshot"]
            new_col["manual_locked"] = False
    else:
        if auto_mode:
            raise ValueError(
                "Não foi possível conectar ao BioCLIP 2.5 no Colab para auto-classificar. "
                "Conecte a URL do Colab ou escolha diretamente o Gênero Coralíneo na lista para salvar offline."
            )

    new_col["color"] = CLASS_COLORS.get(new_col["genus"], "#38bdf8")
    colonies.append(new_col)
    session_data["colonies"] = colonies

    return {
        "new_colony_id": new_id,
        "genus": new_col["genus"],
        "area_cm2": new_col["area_cm2"],
        "area_pct": new_col["area_pct"],
        "extracted_bioclip": bool(feat_info.get("used_remote_bioclip")),
        "has_embedding": bool(new_col.get("embedding"))
    }


def update_colony_polygon_vertices_in_session(
    session_data: Dict[str, Any],
    colony_id: int,
    part_index: int,
    polygon_points: List[List[float]],
    output_dir: str,
    colab_url: Optional[str] = None,
    refresh_bioclip: bool = True,
    filtered_dir: Optional[str] = None,
    fewshot_memory_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Updates the vertices of an existing colony polygon (or specific sub-polygon `part_index` of a group),
    recomputes perspective-rectified area_cm2 & coverage %, and optionally refreshes the 1024-D
    BioCLIP 2.5 ReefNet vector on Colab to match the refined coral boundary.
    """
    colonies = session_data.get("colonies", [])
    cid = int(colony_id)
    target = next((c for c in colonies if int(c["id"]) == cid), None)
    if target is None:
        raise ValueError(f"Colônia/Grupo #{cid} não encontrado.")

    polys = list(target.get("polygons") or ([target["polygon"]] if target.get("polygon") else []))
    if not (0 <= part_index < len(polys)):
        raise ValueError(f"Índice de sub-polígono inválido ({part_index}).")

    clipped_replacement = _sanitize_and_clip_manual_polygon(
        polygon_points=polygon_points,
        session_data=session_data,
        simplify_dense_freehand=False
    )

    polys[part_index:part_index + 1] = clipped_replacement
    target["polygons"] = polys
    target["is_geometry_edited"] = True
    recompute_colony_geometry(target, session_data)

    refreshed_bioclip = False
    if refresh_bioclip and ((colab_url and colab_url.strip()) or not session_data.get("is_bioclip", False)):
        feat_info = extract_single_colony_bioclip_features(
            col=target,
            session_data=session_data,
            output_dir=output_dir,
            colab_url=colab_url,
            filtered_dir=filtered_dir,
        )
        if feat_info["raw"]:
            raw_c = feat_info["raw"]
            zs_sims = raw_c.get("zero_shot_sims", {})
            emb = raw_c.get("embedding", [])
            mem_data = load_fewshot_memory(fewshot_memory_path)
            fused = fuse_zeroshot_and_fewshot(
                zero_shot_sims=zs_sims,
                embedding=emb,
                memory_data=mem_data
            )
            target["embedding"] = emb
            target["zero_shot_sims"] = zs_sims
            target["zero_shot_genus"] = fused["zero_shot_genus"]
            target["alternatives"] = fused["alternatives"]
            target["best_prototype_sim"] = fused["best_prototype_sim"]
            target["consensus_ratio"] = round(float(raw_c.get("consensus_ratio", 1.0)), 3)
            target["views_count"] = int(raw_c.get("views_count", target["sample_points_count"] + 1))
            refreshed_bioclip = bool(feat_info.get("used_remote_bioclip"))

            if not target.get("manual_locked", False):
                target["genus"] = fused["genus"]
                target["confidence"] = round(fused["confidence"], 4)
                target["used_fewshot"] = fused["used_fewshot"]
                target["color"] = fused["color"]

    return {
        "colony_id": cid,
        "genus": target["genus"],
        "parts_count": len(target["polygons"]),
        "area_cm2": target["area_cm2"],
        "area_pct": target["area_pct"],
        "refreshed_bioclip": refreshed_bioclip,
        "has_embedding": bool(target.get("embedding"))
    }


def render_and_export_session(
    session_data: Dict[str, Any],
    output_dir: str,
    recompute_unlocked: bool = False,
    polygons_dir: Optional[str] = None,
    filtered_dir: Optional[str] = None,
    fewshot_memory_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Recomputes ecological coverage summaries (strictly active coral genera, excluding discarded
    non-coral polygons), exports the updated CSV and Matplotlib high-resolution semantic map,
    saves the hash-linked polygon session file, and returns the lightweight JSON payload.
    """
    os.makedirs(output_dir, exist_ok=True)
    mem_data = load_fewshot_memory(fewshot_memory_path)
    fewshot_summary = get_fewshot_summary(fewshot_memory_path)

    total_area_cm2 = float(session_data.get("total_area_cm2", 2500.0))
    quadrat_width_cm = float(session_data.get("quadrat_width_cm", 50.0))
    quadrat_height_cm = float(session_data.get("quadrat_height_cm", 50.0))
    base_name = os.path.splitext(os.path.basename(session_data["image_filename"]))[0]

    genus_area_counter = Counter()
    genus_cm2_counter = Counter()
    genus_colony_counter = Counter()

    colonies = session_data.get("colonies", [])
    for col in colonies:
        col.setdefault("discarded", False)
        col.setdefault("discard_reason", "")
        polys_ref = col.get("polygons") or ([col["polygon"]] if col.get("polygon") else [])
        col["parts_count"] = len(polys_ref)
        col.setdefault("is_grouped", False)
        col.setdefault("is_manual_drawn", False)
        col.setdefault("is_geometry_edited", False)

        if recompute_unlocked and not col.get("manual_locked", False):
            zs_sims = col.get("zero_shot_sims")
            emb = col.get("embedding")
            if zs_sims:
                fused = fuse_zeroshot_and_fewshot(
                    zero_shot_sims=zs_sims,
                    embedding=emb,
                    memory_data=mem_data
                )
                col["genus"] = fused["genus"]
                col["confidence"] = round(fused["confidence"], 4)
                col["color"] = fused["color"]
                col["used_fewshot"] = fused["used_fewshot"]
                col["best_prototype_sim"] = fused["best_prototype_sim"]
                col["non_coral_sim"] = fused.get("non_coral_sim", 0.0)
                col["alternatives"] = fused["alternatives"]

                if fused.get("auto_discard_non_coral", False):
                    col["discarded"] = True
                    col["discard_reason"] = "fewshot_non_coral"
                elif col.get("discard_reason") == "fewshot_non_coral":
                    col["discarded"] = False
                    col["discard_reason"] = ""

        # Guarantee strictly valid coral genus
        if col["genus"] not in CORAL_GENERA:
            col["genus"] = CORAL_GENERA[0]
        col["color"] = CLASS_COLORS.get(col["genus"], "#38bdf8")

        if not col.get("discarded", False):
            g = col["genus"]
            genus_area_counter[g] += int(col["area_pixels"])
            genus_cm2_counter[g] += float(col["area_cm2"])
            genus_colony_counter[g] += 1

    active_colonies = [c for c in colonies if not c.get("discarded", False)]
    discarded_colonies = [c for c in colonies if c.get("discarded", False)]

    genus_summary = []
    total_coral_cm2 = 0.0
    for genus, count in genus_colony_counter.most_common():
        cm2 = genus_cm2_counter[genus]
        total_coral_cm2 += cm2
        pct = (cm2 / total_area_cm2) * 100.0 if total_area_cm2 > 0 else 0.0
        genus_summary.append({
            "genus": genus,
            "count": count,
            "color": CLASS_COLORS.get(genus, "#38bdf8"),
            "area_pixels": genus_area_counter[genus],
            "area_cm2": round(cm2, 2),
            "coverage_pct": round(pct, 2)
        })

    total_coral_cover_pct = round((total_coral_cm2 / total_area_cm2) * 100.0, 2) if total_area_cm2 > 0 else 0.0

    output_image_path = os.path.join(output_dir, f"{base_name}_sam_coralnet.jpg")
    output_csv_path = os.path.join(output_dir, f"{base_name}_ecological_report.csv")

    # 1. Export CSV Report (Strictly Active Coral Colonies / Groups & Coral Genera ONLY)
    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "Colony_Group_ID", "Coral_Genus", "Is_Grouped", "Polygon_Parts",
            "Confidence", "Classification_Source",
            "Consensus_Ratio", "Sample_Points",
            "Area_Pixels", "Area_cm2", "Coverage_Pct",
            "Centroid_Y", "Centroid_X", "BBox_X", "BBox_Y", "BBox_W", "BBox_H"
        ])
        for col in active_colonies:
            bx, by, bw, bh = col["bbox"]
            cy, cx = col["centroid"]
            if col.get("is_manual_drawn"):
                src_tag = "Manual_Drawn+BioCLIP2.5" if col.get("embedding") else "Manual_Drawn"
            elif col.get("manual_locked"):
                src_tag = "Manual_Grouped" if col.get("is_grouped") else "Manual_Confirmed"
            elif col.get("used_fewshot"):
                src_tag = "BioCLIP2.5+FewShot"
            else:
                src_tag = "BioCLIP2.5_ZeroShot"
            if col.get("is_geometry_edited") and not col.get("is_manual_drawn"):
                src_tag += "+EditedBorder"
            writer.writerow([
                col["id"], col["genus"], "Yes" if col.get("is_grouped") else "No",
                len(col.get("polygons", [])),
                col["confidence"], src_tag,
                col.get("consensus_ratio", 1.0),
                col.get("sample_points_count", 1),
                col["area_pixels"], col["area_cm2"], col["area_pct"],
                cy, cx, bx, by, bw, bh
            ])

    # 2. Render Matplotlib Static Semantic Map onto Original (or Enhanced) Photo (Active Colonies Only)
    image_path = session_data["image"]
    target_filtered_dir = filtered_dir or output_dir
    enh_fname = session_data.get("enhanced_image_filename") or ""
    enhanced_path = os.path.join(target_filtered_dir, enh_fname) if enh_fname else ""
    if enh_fname and not os.path.exists(enhanced_path):
        alt_enh = os.path.join(output_dir, enh_fname)
        if os.path.exists(alt_enh):
            enhanced_path = alt_enh
    render_on_enhanced = bool(session_data.get("render_on_enhanced", False))
    bg_path = enhanced_path if (render_on_enhanced and enhanced_path and os.path.exists(enhanced_path)) else image_path

    with Image.open(bg_path) as im_disk:
        bg_display_img = im_disk.convert("RGB")

    fig, (ax_img, ax_legend) = plt.subplots(
        1, 2, figsize=(16, 9),
        gridspec_kw={'width_ratios': [4, 1.28]}, dpi=140
    )

    ax_img.imshow(bg_display_img)
    seg_engine = "CoralSCOP ViT-B" if session_data.get("is_coralscop") else session_data.get("remote_model", "CoralSCOP")
    clf_engine = session_data.get("classifier_model", "BioCLIP 2.5 ReefNet")
    ax_img.set_title(
        f"{seg_engine} + {clf_engine}: {session_data['image_filename']} [{quadrat_width_cm:.0f}x{quadrat_height_cm:.0f} cm]",
        fontsize=12.0, fontweight='bold'
    )
    ax_img.axis('off')

    quad_corners = session_data.get("quadrat_corners")
    if session_data.get("has_quadrat_roi") and quad_corners:
        quad_patch = mpatches.Polygon(
            quad_corners,
            closed=True,
            fill=False,
            edgecolor="#38bdf8",
            linewidth=2.0,
            linestyle="--",
            alpha=0.9
        )
        ax_img.add_patch(quad_patch)

    for col in active_colonies:
        color = col["color"]
        polys = col.get("polygons") or ([col["polygon"]] if col.get("polygon") else [])

        drew_poly = False
        for poly_pts in polys:
            if poly_pts and len(poly_pts) >= 3:
                polygon_patch = mpatches.Polygon(
                    poly_pts,
                    closed=True,
                    facecolor=color,
                    edgecolor=color,
                    linewidth=1.7,
                    alpha=0.40
                )
                ax_img.add_patch(polygon_patch)
                drew_poly = True

        if not drew_poly:
            x, y, bw, bh = col["bbox"]
            rect = mpatches.Rectangle(
                (x, y), bw, bh, linewidth=1.5,
                edgecolor=color, facecolor=color, alpha=0.32
            )
            ax_img.add_patch(rect)

        if col.get("sample_points_count", 1) > 1:
            for pr, pc in col.get("sample_points", []):
                ax_img.plot(pc, pr, marker='+', markersize=4, color='white', markeredgewidth=1.0)

        cy, cx = col["centroid"]
        if col["area_pct"] >= 0.12 or col["id"] <= 35:
            grp_tag = f" ({len(polys)}p)" if (col.get("is_grouped") or len(polys) > 1) else ""
            ax_img.text(
                cx, cy, f"#{col['id']}{grp_tag} {col['genus']}\n{col['area_cm2']}cm²",
                color='white', fontsize=6.8, fontweight='bold',
                ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.2", fc=color, ec="black", lw=0.6, alpha=0.88)
            )

    ax_legend.axis('off')
    fs_note = (
        f"Ativa ({fewshot_summary['total_samples']} ref)"
        if (fewshot_summary["enabled"] and fewshot_summary["total_samples"] > 0)
        else "Zero-Shot Puro"
    )
    summary_lines = [
        "=== Cobertura de Corais ===",
        f"Segm.: {seg_engine}",
        f"Taxon.: {clf_engine[:24]}",
        f"Memória: {fs_note}",
        f"Filtro: {session_data.get('filter_mode', 'combined').upper()}",
        f"ROI 4-Cantos: {'Sim (Homografia)' if session_data.get('has_quadrat_roi') else 'Não'}",
        f"Escala: {quadrat_width_cm:.0f}x{quadrat_height_cm:.0f} cm ({total_area_cm2:.0f} cm²)",
        f"Colônias/Grupos: {len(active_colonies)}",
        f"Cobertura Total: {total_coral_cm2:.1f} cm² ({total_coral_cover_pct}%)",
    ]
    if discarded_colonies:
        summary_lines.append(f"Não-Coral Ocultos: {len(discarded_colonies)}")
    summary_lines.append("")

    for row in genus_summary:
        summary_lines.append(f"{row['genus']}:\n  {row['count']} col ({row['area_cm2']} cm² | {row['coverage_pct']}%)")

    ax_legend.text(
        0.03, 0.97, "\n".join(summary_lines),
        transform=ax_legend.transAxes, fontsize=8.5, family='monospace',
        verticalalignment='top', bbox=dict(boxstyle="round,pad=0.55", fc="#f8f9fa", ec="#cccccc", lw=1)
    )

    plt.tight_layout()
    plt.savefig(output_image_path, bbox_inches='tight', dpi=140)
    plt.close(fig)

    # Update session metadata & persist full hash-linked polygon session (with 1024-D embeddings) to disk
    session_data["total_colonies"] = len(active_colonies)
    session_data["discarded_count"] = len(discarded_colonies)
    session_data["grouped_colonies_count"] = sum(
        1 for c in active_colonies if c.get("is_grouped") or c.get("parts_count", 1) > 1
    )
    session_data["total_coral_cm2"] = round(total_coral_cm2, 2)
    session_data["total_coral_cover_pct"] = total_coral_cover_pct
    session_data["genus_summary"] = genus_summary
    session_data["output_image"] = output_image_path
    session_data["output_image_filename"] = os.path.basename(output_image_path)
    session_data["output_csv"] = output_csv_path
    session_data["output_csv_filename"] = os.path.basename(output_csv_path)
    save_pipeline_session(session_data, output_dir, polygons_dir=polygons_dir)

    return session_to_public_payload(session_data, fewshot_memory_path=fewshot_memory_path)


def run_hybrid_pipeline(
    image_path: str,
    colab_url: str = None,
    output_dir: str = "output",
    min_area: int = 1500,
    iou_thresh: float = 0.60,
    containment_thresh: float = 0.82,
    n_points_multi: int = 5,
    min_area_multi: int = 4000,
    quadrat_width_cm: float = 50.0,
    quadrat_height_cm: float = 50.0,
    points_per_side: int = 32,
    pred_iou_thresh: float = 0.72,
    stability_score_thresh: float = 0.62,
    crop_n_layers: int = 1,
    crop_n_points_downscale_factor: int = 2,
    filter_mode: str = "combined",
    quadrat_corners: Optional[List[List[float]]] = None,
    render_on_enhanced: bool = False,
    filtered_dir: Optional[str] = None,
    polygons_dir: Optional[str] = None,
    fewshot_memory_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes the Automated Benthic Coral Segmentation & Genus Classification Pipeline:
    0. Underwater Preprocessing (White Balance + LAB CLAHE) & Optional 4-Corner Quadrat ROI
    1. Remote CoralSCOP ViT-B on Colab GPU: Semantic coral-only colony segmentation
    2. Reprojection onto full original photo & strict 4-corner quadrat polygon clipping
    3. Polygon-Mask Hierarchical NMS: Eliminates redundant overlapping masks
    4. Multi-Scale (Macro Colony + Full-Res Micro Corallite 224x224) Cropping & BioCLIP 2.5 ReefNet
       Classification on Colab GPU (strictly Coral Genera) + Optional Tip-Adapter Few-Shot Memory
    5. Perspective-Rectified Physical Metrics (cm² via 4-point Homography)
    6. Multi-Polygon Contour Rendering on Original Image, Hash-Bound Polygon Save & CSV Export
    """
    target_filtered_dir = filtered_dir or output_dir
    target_polygons_dir = polygons_dir or output_dir
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(target_filtered_dir, exist_ok=True)
    os.makedirs(target_polygons_dir, exist_ok=True)

    image_sha256 = compute_file_sha256(image_path)
    hash_short = image_sha256[:10]

    with Image.open(image_path) as im_raw:
        orig_image = im_raw.convert("RGB")
    w, h = orig_image.size
    base_name = os.path.splitext(os.path.basename(image_path))[0]

    total_area_cm2 = float(quadrat_width_cm) * float(quadrat_height_cm)
    has_quadrat_roi = bool(quadrat_corners and len(quadrat_corners) == 4)
    ordered_corners = order_quad_corners(quadrat_corners) if has_quadrat_roi else None
    roi_corners_arg = quadrat_corners if has_quadrat_roi else None

    # Stage 0: Underwater Optical Enhancement (saved into `filtered_images/`)
    filter_mode_clean = (filter_mode or "combined").lower().strip()
    enhanced_image = enhance_underwater_image(
        orig_image,
        filter_mode=filter_mode_clean,
        quadrat_corners=roi_corners_arg
    )

    enhanced_filename = f"{base_name}_enhanced_{filter_mode_clean}_{hash_short}.jpg"
    enhanced_path = os.path.join(target_filtered_dir, enhanced_filename)
    enhanced_image.save(enhanced_path, format="JPEG", quality=93)

    # For BioCLIP 2.5 classification, always use color-compensated image (gentle WB if user chose 'none')
    if filter_mode_clean == "none":
        classification_image = enhance_underwater_image(orig_image, filter_mode="wb", quadrat_corners=roi_corners_arg)
    else:
        classification_image = enhanced_image

    # Prepare ROI Crop & Perspective Homography if 4 corners were marked
    if has_quadrat_roi:
        roi_data = prepare_quadrat_roi_crop(enhanced_image, ordered_corners, pad_px=8)
        image_for_gpu = roi_data["cropped_image"]
        offset_x, offset_y = roi_data["offset_x"], roi_data["offset_y"]
        full_quadrat_mask = roi_data["full_mask"]
        homography_matrix = build_quadrat_homography(ordered_corners, quadrat_width_cm, quadrat_height_cm)
        effective_area_pixels = max(1, int(np.count_nonzero(full_quadrat_mask)))
    else:
        image_for_gpu = enhanced_image
        offset_x, offset_y = 0, 0
        full_quadrat_mask = None
        homography_matrix = None
        effective_area_pixels = max(1, w * h)

    fallback_cm2_per_pixel = total_area_cm2 / float(effective_area_pixels)

    print(f"\n{'='*76}")
    print(f"[*] Iniciando Pipeline CoralSCOP + BioCLIP 2.5 ReefNet: {os.path.basename(image_path)} ({w}x{h} px | sha256:{hash_short})")
    print(f"    Filtro Subaquático: {FILTER_LABELS.get(filter_mode_clean, filter_mode_clean)}")
    print(f"    Quadrante ROI 4-Cantos: {'Ativo (Homografia Calibrada)' if has_quadrat_roi else 'Imagem Inteira'}")
    print(f"    GPU Params: pts/side={points_per_side} | pred_iou={pred_iou_thresh} | stability={stability_score_thresh} | crops={crop_n_layers}")
    print(f"    Filtros: min_area={min_area}px | nms_iou={iou_thresh} | escala={quadrat_width_cm}x{quadrat_height_cm}cm")
    print(f"{'='*76}")

    # Stage 1: CoralSCOP Segmentation on Colab GPU (or Local Simulation Fallback)
    sam_client = RemoteSAMClient(colab_url=colab_url)
    remote_model_name = "Modo Simulado Local"
    is_coralscop = False

    if colab_url:
        sam_data = sam_client.segment_image(
            image_path=image_path,
            min_area=min_area,
            pred_iou_thresh=pred_iou_thresh,
            points_per_side=points_per_side,
            stability_score_thresh=stability_score_thresh,
            crop_n_layers=crop_n_layers,
            crop_n_points_downscale_factor=crop_n_points_downscale_factor,
            pil_image=image_for_gpu,
            offset_x=offset_x,
            offset_y=offset_y,
            full_image_size=(w, h),
            bridge_strings=True
        )
        raw_masks = sam_data.get("masks", [])
        remote_model_name = sam_data.get("model", "CoralSCOP ViT-B")
        is_coralscop = "coralscop" in remote_model_name.lower() or sam_data.get("engine") == "coralscop"
    else:
        print("[!] Nenhuma URL do Google Colab fornecida. Executando simulação local...")
        raw_masks = []
        grid_dim = 4
        rx0 = offset_x if has_quadrat_roi else 0
        ry0 = offset_y if has_quadrat_roi else 0
        rw = image_for_gpu.size[0]
        rh = image_for_gpu.size[1]
        for r_idx in range(grid_dim):
            y0 = ry0 + int(r_idx * rh / grid_dim)
            y1 = ry0 + int((r_idx + 1) * rh / grid_dim)
            for c_idx in range(grid_dim):
                x0 = rx0 + int(c_idx * rw / grid_dim)
                x1 = rx0 + int((c_idx + 1) * rw / grid_dim)
                bbox = [x0, y0, x1 - x0, y1 - y0]
                area = (x1 - x0) * (y1 - y0)
                if area < min_area:
                    continue
                poly = generate_approx_polygon(bbox)
                raw_masks.append({
                    "id": len(raw_masks) + 1,
                    "bbox": bbox,
                    "polygon": poly,
                    "polygons": [poly],
                    "centroid": [(y0 + y1) // 2, (x0 + x1) // 2],
                    "area": area,
                    "area_pct": (area / effective_area_pixels) * 100.0,
                    "predicted_iou": 0.88,
                    "stability_score": 0.85
                })

    print(f"[*] Servidor ({remote_model_name}) retornou {len(raw_masks)} máscaras candidatas.")

    # Stage 1.5: Strict 4-Corner Quadrat Polygon Clipping
    if has_quadrat_roi and full_quadrat_mask is not None:
        clipped_masks = []
        for m in raw_masks:
            polys = m.get("polygons") or ([m["polygon"]] if m.get("polygon") else [])
            c_polys, c_area, c_bbox, c_centroid = clip_polygons_to_quadrat(polys, full_quadrat_mask)
            if c_area < min_area or not c_polys:
                continue
            m["polygons"] = c_polys
            m["polygon"] = c_polys[0]
            m["area"] = c_area
            m["bbox"] = c_bbox
            m["centroid"] = c_centroid
            clipped_masks.append(m)
        print(f"[*] [Recorte Quadrante 4-Cantos] {len(clipped_masks)} colônias internas mantidas ({len(raw_masks) - len(clipped_masks)} externas/bordas removidas).")
        raw_masks = clipped_masks

    # Stage 2: Polygon-Mask Hierarchical NMS
    filtered_masks = apply_hierarchical_nms(
        raw_masks,
        iou_thresh=iou_thresh,
        containment_thresh=containment_thresh
    )
    suppressed_count = len(raw_masks) - len(filtered_masks)
    # Re-index clean 1..N colony IDs after clipping & NMS
    for idx, m in enumerate(filtered_masks, 1):
        m["id"] = idx

    print(f"[*] [NMS Poligonal] Suprimidas {suppressed_count} máscaras redundantes -> {len(filtered_masks)} colônias finais.")

    # Stage 3: Multi-Point Interior Sampling
    colony_points_list = []
    multi_point_colonies = 0

    for m in filtered_masks:
        pts = sample_interior_points(
            bbox=m["bbox"],
            polygon=m.get("polygon"),
            n_points=n_points_multi,
            min_area_multi=min_area_multi,
            polygons=m.get("polygons"),
            centroid=m.get("centroid")
        )
        if len(pts) > 1:
            multi_point_colonies += 1
        colony_points_list.append(pts)

    # Stage 4: BioCLIP 2.5 ReefNet Multi-Scale Classification on Colab GPU (Strictly Coral Genera)
    bioclip_resp = None
    classifier_model_name = "BioCLIP 2.5 ReefNet"
    is_bioclip = False

    if colab_url and filtered_masks:
        bioclip_resp = sam_client.classify_colonies_bioclip(
            enhanced_image=classification_image,
            masks=filtered_masks,
            colony_points_list=colony_points_list
        )

    if bioclip_resp and bioclip_resp.get("results"):
        raw_classifications = bioclip_resp["results"]
        classifier_model_name = bioclip_resp.get("classifier_model", "BioCLIP 2.5 ViT-H/14 ReefNet")
        is_bioclip = True
    else:
        classifier_model_name = "Fallback Local (Atualize o Colab p/ BioCLIP 2.5)" if colab_url else "Simulador Local (11 Gêneros)"
        local_clf = get_coral_classifier()
        raw_classifications = local_clf.extract_offline_bioclip_like(
            pil_image=classification_image,
            masks=filtered_masks,
            colony_points_list=colony_points_list
        )

    # Stage 5: Fuse BioCLIP 2.5 Zero-Shot with Optional Few-Shot Memory & Compute Homography cm²
    mem_data = load_fewshot_memory(fewshot_memory_path)
    colonies_report = []

    for m, raw_c, pts in zip(filtered_masks, raw_classifications, colony_points_list):
        zs_sims = raw_c.get("zero_shot_sims", {})
        emb = raw_c.get("embedding", [])
        fused = fuse_zeroshot_and_fewshot(
            zero_shot_sims=zs_sims,
            embedding=emb,
            memory_data=mem_data
        )

        polys = m.get("polygons") or ([m["polygon"]] if m.get("polygon") else [])
        area_px = int(m.get("area", m["bbox"][2] * m["bbox"][3]))
        area_cm2 = compute_polygons_area_cm2(
            polygons=polys,
            homography_matrix=homography_matrix,
            fallback_cm2_per_pixel=fallback_cm2_per_pixel,
            area_pixels=area_px
        )
        cov_pct = (area_cm2 / total_area_cm2) * 100.0 if total_area_cm2 > 0 else 0.0

        bx, by, bw, bh = m["bbox"]
        auto_disc = bool(fused.get("auto_discard_non_coral", False))
        colonies_report.append({
            "id": m["id"],
            "genus": fused["genus"],
            "confidence": round(fused["confidence"], 4),
            "zero_shot_genus": fused["zero_shot_genus"],
            "used_fewshot": fused["used_fewshot"],
            "best_prototype_sim": fused["best_prototype_sim"],
            "non_coral_sim": fused.get("non_coral_sim", 0.0),
            "manual_locked": False,
            "is_grouped": False,
            "parts_count": len(polys),
            "discarded": auto_disc,
            "discard_reason": "fewshot_non_coral" if auto_disc else "",
            "consensus_ratio": round(float(raw_c.get("consensus_ratio", 1.0)), 3),
            "sample_points_count": len(pts),
            "views_count": int(raw_c.get("views_count", len(pts) + 1)),
            "sample_points": pts,
            "color": fused["color"],
            "bbox": m["bbox"],
            "bbox_pct": {
                "left": (bx / w) * 100.0,
                "top": (by / h) * 100.0,
                "width": (bw / w) * 100.0,
                "height": (bh / h) * 100.0
            },
            "polygon": m.get("polygon", []),
            "polygons": polys,
            "centroid": m["centroid"],
            "area_pixels": area_px,
            "area_cm2": round(area_cm2, 2),
            "area_pct": round(cov_pct, 2),
            "alternatives": fused["alternatives"],
            "zero_shot_sims": zs_sims,
            "embedding": emb
        })

    session_data = {
        "image": image_path,
        "image_filename": os.path.basename(image_path),
        "image_sha256": image_sha256,
        "image_hash_short": image_sha256[:12],
        "enhanced_image_filename": enhanced_filename,
        "filter_mode": filter_mode_clean,
        "filter_label": FILTER_LABELS.get(filter_mode_clean, filter_mode_clean),
        "render_on_enhanced": render_on_enhanced,
        "remote_model": remote_model_name,
        "classifier_model": classifier_model_name,
        "is_coralscop": is_coralscop,
        "is_bioclip": is_bioclip,
        "has_quadrat_roi": has_quadrat_roi,
        "quadrat_corners": ordered_corners.tolist() if ordered_corners is not None else None,
        "effective_area_pixels": effective_area_pixels,
        "image_width": w,
        "image_height": h,
        "suppressed_redundant_masks": suppressed_count,
        "multi_point_colonies": multi_point_colonies,
        "quadrat_width_cm": quadrat_width_cm,
        "quadrat_height_cm": quadrat_height_cm,
        "total_area_cm2": round(total_area_cm2, 2),
        "sam_params": {
            "points_per_side": points_per_side,
            "pred_iou_thresh": pred_iou_thresh,
            "stability_score_thresh": stability_score_thresh,
            "crop_n_layers": crop_n_layers,
            "crop_n_points_downscale_factor": crop_n_points_downscale_factor,
            "min_area": min_area
        },
        "colonies": colonies_report
    }

    public_result = render_and_export_session(
        session_data,
        output_dir=output_dir,
        recompute_unlocked=False,
        polygons_dir=target_polygons_dir,
        filtered_dir=target_filtered_dir,
        fewshot_memory_path=fewshot_memory_path,
    )

    print("\n--- Relatório Ecológico Automatizado (Somente Gêneros de Corais) ---")
    print(f"{'Gênero Coralíneo':<22} | {'Colônias':<10} | {'Área (cm²)':<12} | {'Cobertura (%)':<15}")
    print("-" * 66)
    for row in public_result["genus_summary"]:
        print(f"{row['genus']:<22} | {row['count']:<10} | {row['area_cm2']:<12.1f} | {row['coverage_pct']:.1f}%")
    print("-" * 66)
    print(f"Cobertura Coralínea Total: {public_result['total_coral_cm2']:.1f} cm² ({public_result['total_coral_cover_pct']:.1f}% do quadrante)")

    return public_result
