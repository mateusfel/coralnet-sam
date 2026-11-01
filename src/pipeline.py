import os
from typing import Dict, Any, List
from collections import Counter
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from src.sam_client import RemoteSAMClient
from src.coral_classifier import LocalCoralClassifier, CLASS_COLORS
from src.geometry import (
    apply_hierarchical_nms,
    sample_interior_points,
    generate_approx_polygon
)


def run_hybrid_pipeline(
    image_path: str,
    colab_url: str = None,
    output_dir: str = "output",
    iou_thresh: float = 0.60,
    containment_thresh: float = 0.80,
    n_points_multi: int = 5,
    min_area_multi: int = 4000
) -> Dict[str, Any]:
    """
    Executes the 100% automated 2-Stage Benthic Segmentation (Fase 2):
    1. Remote SAM ViT-H on Colab GPU: Discovers all colonies & boundaries
    2. Hierarchical NMS & Containment Suppression: Eliminates redundant overlapping masks
    3. Multi-Point Interior Sampling & Consensus Voting: Robust classification of colonies
    4. Local CoralNet EfficientNet-B0: Classifies each colony into Brazilian reef taxonomy
    5. Real Polygon Contour Rendering: High-resolution visual output with organic shapes
    """
    os.makedirs(output_dir, exist_ok=True)
    image = Image.open(image_path).convert("RGB")
    w, h = image.size

    print(f"\n{'='*70}")
    print(f"[*] Iniciando Pipeline Híbrido (Fase 2): {os.path.basename(image_path)} ({w}x{h} px)")
    print(f"{'='*70}")

    # Stage 1: Segment Anything Model (Remote on Colab GPU or Local fallback)
    sam_client = RemoteSAMClient(colab_url=colab_url)
    
    if colab_url:
        sam_data = sam_client.segment_image(image_path)
        raw_masks = sam_data.get("masks", [])
    else:
        print("[!] Nenhuma URL do Google Colab fornecida.")
        print("    Gerando grade de segmentação representativa para teste local...")
        raw_masks = []
        grid_dim = 6
        for r_idx in range(grid_dim):
            y0 = int(r_idx * h / grid_dim)
            y1 = int((r_idx + 1) * h / grid_dim)
            for c_idx in range(grid_dim):
                x0 = int(c_idx * w / grid_dim)
                x1 = int((c_idx + 1) * w / grid_dim)
                bbox = [x0, y0, x1 - x0, y1 - y0]
                raw_masks.append({
                    "id": len(raw_masks) + 1,
                    "bbox": bbox,
                    "polygon": generate_approx_polygon(bbox),
                    "centroid": [(y0 + y1) // 2, (x0 + x1) // 2],
                    "area": (x1 - x0) * (y1 - y0),
                    "area_pct": (((x1 - x0) * (y1 - y0)) / (w * h)) * 100.0,
                    "stability_score": 0.95
                })

    print(f"[*] SAM detectou {len(raw_masks)} máscaras brutas.")

    # Stage 2: Fase 2 - Supressão Hierárquica e NMS de Sobreposição
    filtered_masks = apply_hierarchical_nms(
        raw_masks,
        iou_thresh=iou_thresh,
        containment_thresh=containment_thresh
    )
    suppressed_count = len(raw_masks) - len(filtered_masks)
    print(f"[*] [Fase 2 - NMS] Suprimidas {suppressed_count} máscaras sobrepostas redundantes.")
    print(f"[*] Total de {len(filtered_masks)} colônias refinadas para análise.")

    # Stage 3: Fase 2 - Amostragem Multi-Ponto e Votação por Consenso
    colony_points_list = []
    multi_point_colonies = 0

    for m in filtered_masks:
        bbox = m["bbox"]
        poly = m.get("polygon")
        pts = sample_interior_points(
            bbox=bbox,
            polygon=poly,
            n_points=n_points_multi,
            min_area_multi=min_area_multi
        )
        if len(pts) > 1:
            multi_point_colonies += 1
        colony_points_list.append(pts)

    print(f"[*] [Fase 2 - Multi-Ponto] {multi_point_colonies} colônias grandes receberam amostragem multi-ponto (até {n_points_multi} pontos).")

    # Stage 4: CoralNet Taxonomic Classification (Local EfficientNet-B0)
    classifier = LocalCoralClassifier()
    classifications = classifier.classify_colonies_multipoint(image, colony_points_list)

    # Stage 5: Merge Masks + Taxonomy & Compute Real Ecological Area
    colonies_report = []
    genus_area_counter = Counter()
    genus_colony_counter = Counter()
    total_area_pixels = w * h

    for m, c, pts in zip(filtered_masks, classifications, colony_points_list):
        genus = c["genus"]
        area = m.get("area", m["bbox"][2] * m["bbox"][3])
        genus_area_counter[genus] += area
        genus_colony_counter[genus] += 1

        colonies_report.append({
            "id": m["id"],
            "genus": genus,
            "confidence": c["confidence"],
            "consensus_ratio": c.get("consensus_ratio", 1.0),
            "sample_points_count": len(pts),
            "sample_points": pts,
            "color": c["color"],
            "bbox": m["bbox"],
            "polygon": m.get("polygon"),
            "centroid": m["centroid"],
            "area_pixels": area,
            "area_pct": (area / total_area_pixels) * 100.0,
            "alternatives": c["alternatives"]
        })

    # Summary table in terminal
    print("\n--- Relatório Ecológico Automatizado (Fase 2) ---")
    print(f"{'Gênero / Substrato':<32} | {'Colônias':<10} | {'Cobertura (%)':<15}")
    print("-" * 65)
    for genus, count in genus_colony_counter.most_common():
        pct = (genus_area_counter[genus] / total_area_pixels) * 100.0
        print(f"{genus:<32} | {count:<10} | {pct:.1f}%")

    # Stage 6: Render High-Resolution Annotated Semantic Map with Real Polygons
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_image_path = os.path.join(output_dir, f"{base_name}_sam_coralnet.jpg")

    fig, (ax_img, ax_legend) = plt.subplots(
        1, 2, figsize=(16, 9),
        gridspec_kw={'width_ratios': [4, 1.2]}, dpi=140
    )

    ax_img.imshow(image)
    ax_img.set_title(
        f"SAM ViT-H + CoralNet (Fase 2: Polígonos & Multi-Ponto): {os.path.basename(image_path)}",
        fontsize=13, fontweight='bold'
    )
    ax_img.axis('off')

    # Draw semi-transparent polygons with smooth organic contours
    for col in colonies_report:
        color = col["color"]
        poly_pts = col.get("polygon")

        if poly_pts and len(poly_pts) >= 3:
            polygon_patch = mpatches.Polygon(
                poly_pts,
                closed=True,
                facecolor=color,
                edgecolor=color,
                linewidth=1.6,
                alpha=0.38
            )
            ax_img.add_patch(polygon_patch)
        else:
            x, y, bw, bh = col["bbox"]
            rect = mpatches.Rectangle(
                (x, y), bw, bh, linewidth=1.5,
                edgecolor=color, facecolor=color, alpha=0.32
            )
            ax_img.add_patch(rect)

        # Draw subtle multi-point sample markers for large colonies
        if col["sample_points_count"] > 1:
            for pr, pc in col["sample_points"]:
                ax_img.plot(pc, pr, marker='+', markersize=4, color='white', markeredgewidth=1.0)

        # Place label at centroid (for clear visibility on significant colonies)
        cy, cx = col["centroid"]
        if col["area_pct"] >= 0.08 or col["id"] <= 35:
            ax_img.text(
                cx, cy, f"#{col['id']} {col['genus']}",
                color='white', fontsize=7.0, fontweight='bold',
                ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.2", fc=color, ec="black", lw=0.6, alpha=0.88)
            )

    # Legend Panel
    ax_legend.axis('off')
    summary_lines = [
        "=== Cobertura Bêntica Real ===",
        f"Colônias Selecionadas: {len(colonies_report)}",
        f"Filtro NMS: -{suppressed_count} sobreposições",
        f"Multi-Ponto: {multi_point_colonies} colônias",
        ""
    ]
    for genus, count in genus_colony_counter.most_common():
        pct = (genus_area_counter[genus] / total_area_pixels) * 100.0
        summary_lines.append(f"{genus}:\n  {count} colônias ({pct:.1f}%)")

    ax_legend.text(
        0.05, 0.95, "\n".join(summary_lines),
        transform=ax_legend.transAxes, fontsize=9.5, family='monospace',
        verticalalignment='top', bbox=dict(boxstyle="round,pad=0.6", fc="#f8f9fa", ec="#cccccc", lw=1)
    )

    plt.tight_layout()
    plt.savefig(output_image_path, bbox_inches='tight', dpi=140)
    plt.close(fig)

    print(f"\n[OK] Mapa de segmentação semântica salvo: {output_image_path}")
    return {
        "image": image_path,
        "total_colonies": len(colonies_report),
        "suppressed_redundant_masks": suppressed_count,
        "multi_point_colonies": multi_point_colonies,
        "output_image": output_image_path,
        "colonies": colonies_report
    }
