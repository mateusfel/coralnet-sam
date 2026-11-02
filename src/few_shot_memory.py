import os
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import Counter
import numpy as np

# Strictly 11 Brazilian / South Atlantic Coral Genera ONLY (Scleractinia + Milleporidae)
CORAL_GENERA = [
    "Montastraea",
    "Mussismilia",
    "Porites",
    "Siderastrea",
    "Agaricia",
    "Millepora",
    "Madracis",
    "Meandrina",
    "Stephanocoenia",
    "Scolymia",
    "Favia"
]

# Special negative Few-Shot prototype class to auto-filter non-coral false positives
NON_CORAL_LABEL = "__NON_CORAL__"
NON_CORAL_DISPLAY = "Não é Coral (Descartar)"

CLASS_COLORS = {
    "Montastraea": "#e6194b",
    "Mussismilia": "#3cb44b",
    "Porites": "#ffe119",
    "Siderastrea": "#4363d8",
    "Agaricia": "#f58231",
    "Millepora": "#911eb4",
    "Madracis": "#42d4f4",
    "Meandrina": "#f032e6",
    "Stephanocoenia": "#bfef45",
    "Scolymia": "#fabed4",
    "Favia": "#469990"
}

_MEMORY_LOCK = threading.Lock()


def get_default_memory_path() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    return os.path.join(models_dir, "bioclip_fewshot_memory.json")


def _empty_memory_dict() -> Dict[str, Any]:
    return {
        "version": 2,
        "enabled": True,
        "alpha": 1.25,
        "beta": 14.0,
        "non_coral_sim_thresh": 0.875,
        "samples": []
    }


def load_fewshot_memory(memory_path: Optional[str] = None) -> Dict[str, Any]:
    path = memory_path or get_default_memory_path()
    with _MEMORY_LOCK:
        if not os.path.exists(path):
            return _empty_memory_dict()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return _empty_memory_dict()
            allowed_labels = set(CORAL_GENERA) | {NON_CORAL_LABEL}
            valid_samples = [
                s for s in data.get("samples", [])
                if s.get("genus") in allowed_labels and isinstance(s.get("embedding"), list) and len(s["embedding"]) > 0
            ]
            data["samples"] = valid_samples
            data.setdefault("enabled", True)
            data.setdefault("alpha", 1.25)
            data.setdefault("beta", 14.0)
            data.setdefault("non_coral_sim_thresh", 0.875)
            return data
        except Exception:
            return _empty_memory_dict()


def save_fewshot_memory(data: Dict[str, Any], memory_path: Optional[str] = None) -> None:
    path = memory_path or get_default_memory_path()
    with _MEMORY_LOCK:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def get_fewshot_summary(memory_path: Optional[str] = None) -> Dict[str, Any]:
    mem = load_fewshot_memory(memory_path)
    counts = Counter(s["genus"] for s in mem.get("samples", []))
    by_genus = [
        {"genus": g, "label": g, "count": counts[g], "color": CLASS_COLORS.get(g, "#38bdf8")}
        for g in CORAL_GENERA if counts[g] > 0
    ]
    non_coral_count = counts.get(NON_CORAL_LABEL, 0)
    if non_coral_count > 0:
        by_genus.append({
            "genus": NON_CORAL_LABEL,
            "label": "Não é Coral",
            "count": non_coral_count,
            "color": "#94a3b8"
        })
    return {
        "enabled": bool(mem.get("enabled", True)),
        "total_samples": len(mem.get("samples", [])),
        "non_coral_samples": non_coral_count,
        "genera_covered": sum(1 for g in CORAL_GENERA if counts[g] > 0),
        "by_genus": by_genus
    }


def set_fewshot_enabled(enabled: bool, memory_path: Optional[str] = None) -> Dict[str, Any]:
    mem = load_fewshot_memory(memory_path)
    mem["enabled"] = bool(enabled)
    save_fewshot_memory(mem, memory_path)
    return get_fewshot_summary(memory_path)


def clear_fewshot_memory(memory_path: Optional[str] = None) -> Dict[str, Any]:
    mem = load_fewshot_memory(memory_path)
    was_enabled = bool(mem.get("enabled", True))
    fresh = _empty_memory_dict()
    fresh["enabled"] = was_enabled
    save_fewshot_memory(fresh, memory_path)
    return get_fewshot_summary(memory_path)


def add_fewshot_prototype(
    genus: str,
    embedding: List[float],
    source_image: str = "",
    colony_id: int = 0,
    area_cm2: float = 0.0,
    memory_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Stores or updates a 1024-D L2-normalized BioCLIP 2.5 ReefNet visual prototype for one of
    the 11 CORAL_GENERA or NON_CORAL_LABEL ('__NON_CORAL__').
    """
    if genus not in CORAL_GENERA and genus != NON_CORAL_LABEL:
        raise ValueError(f"Rótulo inválido '{genus}'. Permitidos apenas gêneros de corais ou '{NON_CORAL_LABEL}'.")
    if not embedding or len(embedding) < 8:
        raise ValueError("Este polígono não possui vetor de assinatura visual BioCLIP disponível.")

    vec = np.array(embedding, dtype=np.float32)
    norm = float(np.linalg.norm(vec))
    if norm > 1e-7:
        vec = vec / norm
    compact_emb = [round(float(x), 5) for x in vec.tolist()]

    mem = load_fewshot_memory(memory_path)
    samples = mem.get("samples", [])

    updated = False
    for s in samples:
        if source_image and colony_id and s.get("source_image") == source_image and s.get("colony_id") == colony_id:
            s["genus"] = genus
            s["embedding"] = compact_emb
            s["area_cm2"] = round(float(area_cm2), 2)
            s["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated = True
            break

    if not updated:
        samples.append({
            "sample_id": f"{os.path.splitext(source_image)[0]}_c{colony_id}_{int(time.time()*1000)}",
            "genus": genus,
            "source_image": source_image,
            "colony_id": int(colony_id),
            "area_cm2": round(float(area_cm2), 2),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "embedding": compact_emb
        })

    mem["samples"] = samples
    mem["enabled"] = True
    save_fewshot_memory(mem, memory_path)
    return get_fewshot_summary(memory_path)


def fuse_zeroshot_and_fewshot(
    zero_shot_sims: Dict[str, float],
    embedding: Optional[List[float]] = None,
    memory_data: Optional[Dict[str, Any]] = None,
    logit_scale: float = 34.0
) -> Dict[str, Any]:
    """
    Combines BioCLIP 2.5 ReefNet Zero-Shot genus cosine similarities with optional
    Tip-Adapter Few-Shot visual prototypes (ECCV 2022), plus strict Non-Coral auto-filtering:
      - Always assigns a valid coral genus from CORAL_GENERA.
      - Additionally evaluates similarity against saved NON_CORAL_LABEL prototypes: if similarity
        exceeds `non_coral_sim_thresh` (0.875) and beats any taught coral prototype by >= 0.015,
        flags `auto_discard_non_coral=True` so the polygon is automatically ignored from coral cover.
    """
    sims_vec = np.array([float(zero_shot_sims.get(g, 0.0)) for g in CORAL_GENERA], dtype=np.float64)

    scaled_logits = sims_vec * float(logit_scale)
    scaled_logits -= np.max(scaled_logits)
    exp_logits = np.exp(scaled_logits)
    p_zs = exp_logits / max(1e-12, float(np.sum(exp_logits)))

    used_fewshot = False
    best_proto_sim = 0.0
    max_non_coral_sim = 0.0
    auto_discard_non_coral = False
    p_final = p_zs.copy()

    if (
        memory_data
        and memory_data.get("enabled", True)
        and memory_data.get("samples")
        and embedding
        and len(embedding) > 0
    ):
        q_vec = np.array(embedding, dtype=np.float64)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 1e-8:
            q_vec = q_vec / q_norm
            dim = q_vec.shape[0]

            alpha = float(memory_data.get("alpha", 1.25))
            beta = float(memory_data.get("beta", 14.0))
            non_coral_thresh = float(memory_data.get("non_coral_sim_thresh", 0.875))

            sims_by_genus: Dict[int, List[float]] = {}
            non_coral_sims: List[float] = []

            for s in memory_data["samples"]:
                g_name = s.get("genus")
                s_emb = s.get("embedding")
                if not s_emb or len(s_emb) != dim:
                    continue
                k_vec = np.array(s_emb, dtype=np.float64)
                k_norm = np.linalg.norm(k_vec)
                if k_norm <= 1e-8:
                    continue
                cos_sim = float(np.dot(q_vec, k_vec / k_norm))

                if g_name == NON_CORAL_LABEL:
                    non_coral_sims.append(cos_sim)
                    if cos_sim > max_non_coral_sim:
                        max_non_coral_sim = cos_sim
                elif g_name in CORAL_GENERA:
                    g_idx = CORAL_GENERA.index(g_name)
                    sims_by_genus.setdefault(g_idx, []).append(cos_sim)
                    if cos_sim > best_proto_sim:
                        best_proto_sim = cos_sim

            if sims_by_genus:
                affinity_vec = np.zeros(len(CORAL_GENERA), dtype=np.float64)
                for g_idx, g_sims in sims_by_genus.items():
                    top_k = sorted(g_sims, reverse=True)[:3]
                    affinities = [np.exp(-beta * max(0.0, 1.0 - c)) for c in top_k]
                    affinity_vec[g_idx] = float(np.mean(affinities))

                unnorm = p_zs + alpha * affinity_vec
                total_mass = float(np.sum(unnorm))
                if total_mass > 1e-12:
                    p_final = unnorm / total_mass
                    used_fewshot = True

            # Strict safety check for Non-Coral auto-filtering
            if non_coral_sims and max_non_coral_sim >= non_coral_thresh:
                if max_non_coral_sim >= (best_proto_sim + 0.015):
                    auto_discard_non_coral = True

    sorted_indices = np.argsort(p_final)[::-1]
    top_idx = int(sorted_indices[0])
    top_genus = CORAL_GENERA[top_idx]

    return {
        "genus": top_genus,
        "confidence": float(p_final[top_idx]),
        "zero_shot_genus": CORAL_GENERA[int(np.argmax(p_zs))],
        "zero_shot_confidence": float(np.max(p_zs)),
        "color": CLASS_COLORS.get(top_genus, "#38bdf8"),
        "used_fewshot": used_fewshot,
        "best_prototype_sim": round(best_proto_sim, 4),
        "auto_discard_non_coral": auto_discard_non_coral,
        "non_coral_sim": round(max_non_coral_sim, 4),
        "alternatives": [
            {
                "genus": CORAL_GENERA[int(idx)],
                "confidence": round(float(p_final[int(idx)]), 4),
                "color": CLASS_COLORS.get(CORAL_GENERA[int(idx)], "#38bdf8")
            }
            for idx in sorted_indices[1:4]
        ]
    }
