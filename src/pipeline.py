import os
import csv
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
    min_area: int = 300,
    iou_thresh: float = 0.60,
    containment_thresh: float = 0.80,
    n_points_multi: int = 5,
    min_area_multi: int = 4000,
    quadrat_width_cm: float = 50.0,
    quadrat_height_cm: float = 50.0
) -> Dict[str, Any]:
    """
    Executes the 100% automated 2-Stage Benthic Segmentation (Fase 2 & Fase 3):
    1. Remote SAM ViT-H on Colab GPU: Discovers all colonies & boundaries with configurable min_area
    2. Hierarchical NMS & Containment Suppression: Eliminates redundant overlapping masks
    3. Multi-Point Interior Sampling & Consensus Voting: Robust classification of colonies
    4. Local CoralNet EfficientNet-B0: Classifies each colony into Brazilian reef taxonomy
    5. Physical Metrics Calculation: Area in cm² based on quadrat scale
    6. Real Polygon Contour Rendering & CSV Export: High-resolution visual output and ecological data
    """
    os.makedirs(output_dir, exist_ok=True)
    image = Image.open(image_path).convert("RGB")
    w, h = image.size
    total_area_pixels = w * h
    total_area_cm2 = quadrat_width_cm * quadrat_height_cm
    cm2_per_pixel = total_area_cm2 / total_area_pixels if total_area_pixels > 0 else 0.0

    print(f"\n{'='*70}")
    print(f"[*] Iniciando Pipeline Híbrido (Fase 3): {os.path.basename(image_path)} ({w}x{h} px)")
    print(f"    Parâmetros: min_area={min_area}px | iou={iou_thresh} | multi_pts={n_points_multi} | escala={quadrat_width_cm}x{quadrat_height_cm}cm")
    print(f"{'='*70}")

    # Stage 1: Segment Anything Model (Remote on Colab GPU or Local fallback)
    sam_client = RemoteSAMClient(colab_url=colab_url)
    
    if colab_url:
        sam_data = sam_client.segment_image(image_path, min_area=min_area)
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
                area = (x1 - x0) * (y1 - y0)
                if area < min_area:
                    continue
                raw_masks.append({
                    "id": len(raw_masks) + 1,
                    "bbox": bbox,
                    "polygon": generate_approx_polygon(bbox),
                    "centroid": [(y0 + y1) // 2, (x0 + x1) // 2],
                    "area": area,
                    "area_pct": (area / total_area_pixels) * 100.0,
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

    # Stage 5: Fase 3 - Merge Masks, Taxonomia e Cálculo de Área Real em cm²
    colonies_report = []
    genus_area_counter = Counter()
    genus_cm2_counter = Counter()
    genus_colony_counter = Counter()

    for m, c, pts in zip(filtered_masks, classifications, colony_points_list):
        genus = c["genus"]
        area_px = m.get("area", m["bbox"][2] * m["bbox"][3])
        area_cm2 = area_px * cm2_per_pixel

        genus_area_counter[genus] += area_px
        genus_cm2_counter[genus] += area_cm2
        genus_colony_counter[genus] += 1

        bx, by, bw, bh = m["bbox"]
        colonies_report.append({
            "id": m["id"],
            "genus": genus,
            "confidence": round(c["confidence"], 4),
            "consensus_ratio": round(c.get("consensus_ratio", 1.0), 3),
            "sample_points_count": len(pts),
            "sample_points": pts,
            "color": c["color"],
            "bbox": m["bbox"],
            "bbox_pct": {
                "left": (bx / w) * 100.0,
                "top": (by / h) * 100.0,
                "width": (bw / w) * 100.0,
                "height": (bh / h) * 100.0
            },
            "polygon": m.get("polygon", []),
            "centroid": m["centroid"],
            "area_pixels": area_px,
            "area_cm2": round(area_cm2, 2),
            "area_pct": round((area_px / total_area_pixels) * 100.0, 2),
            "alternatives": c["alternatives"]
        })

    # Build Ecological Summary Table
    genus_summary = []
    for genus, count in genus_colony_counter.most_common():
        pct = (genus_area_counter[genus] / total_area_pixels) * 100.0
        cm2 = genus_cm2_counter[genus]
        genus_summary.append({
            "genus": genus,
            "count": count,
            "color": CLASS_COLORS.get(genus, "#38bdf8"),
            "area_pixels": genus_area_counter[genus],
            "area_cm2": round(cm2, 2),
            "coverage_pct": round(pct, 2)
        })

    # Summary table in terminal
    print("\n--- Relatório Ecológico Automatizado (Fase 3: cm² & Taxonomia) ---")
    print(f"{'Gênero / Substrato':<32} | {'Colônias':<10} | {'Área (cm²)':<12} | {'Cobertura (%)':<15}")
    print("-" * 75)
    for row in genus_summary:
        print(f"{row['genus']:<32} | {row['count']:<10} | {row['area_cm2']:<12.1f} | {row['coverage_pct']:.1f}%")

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_image_path = os.path.join(output_dir, f"{base_name}_sam_coralnet.jpg")
    output_csv_path = os.path.join(output_dir, f"{base_name}_ecological_report.csv")

    # Export CSV Report
    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "Colony_ID", "Genus", "Confidence", "Consensus_Ratio", "Sample_Points",
            "Area_Pixels", "Area_cm2", "Coverage_Pct",
            "Centroid_Y", "Centroid_X", "BBox_X", "BBox_Y", "BBox_W", "BBox_H"
        ])
        for col in colonies_report:
            bx, by, bw, bh = col["bbox"]
            cy, cx = col["centroid"]
            writer.writerow([
                col["id"], col["genus"], col["confidence"], col["consensus_ratio"],
                col["sample_points_count"], col["area_pixels"], col["area_cm2"],
                col["area_pct"], cy, cx, bx, by, bw, bh
            ])
    print(f"[OK] Relatório tabulado exportado: {output_csv_path}")

    # Stage 6: Render High-Resolution Annotated Semantic Map with Real Polygons
    fig, (ax_img, ax_legend) = plt.subplots(
        1, 2, figsize=(16, 9),
        gridspec_kw={'width_ratios': [4, 1.2]}, dpi=140
    )

    ax_img.imshow(image)
    ax_img.set_title(
        f"SAM ViT-H + CoralNet (Fase 3): {os.path.basename(image_path)} [{quadrat_width_cm:.0f}x{quadrat_height_cm:.0f} cm]",
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

        # Place label at centroid
        cy, cx = col["centroid"]
        if col["area_pct"] >= 0.08 or col["id"] <= 35:
            ax_img.text(
                cx, cy, f"#{col['id']} {col['genus']}\n{col['area_cm2']}cm²",
                color='white', fontsize=6.8, fontweight='bold',
                ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.2", fc=color, ec="black", lw=0.6, alpha=0.88)
            )

    # Legend Panel
    ax_legend.axis('off')
    summary_lines = [
        "=== Cobertura Bêntica Real ===",
        f"Escala: {quadrat_width_cm:.0f}x{quadrat_height_cm:.0f} cm ({total_area_cm2:.0f} cm²)",
        f"Colônias: {len(colonies_report)}",
        f"Filtro NMS: -{suppressed_count} sobreposições",
        f"Multi-Ponto: {multi_point_colonies} colônias",
        ""
    ]
    for row in genus_summary:
        summary_lines.append(f"{row['genus']}:\n  {row['count']} col ({row['area_cm2']} cm² | {row['coverage_pct']}%)")

    ax_legend.text(
        0.05, 0.95, "\n".join(summary_lines),
        transform=ax_legend.transAxes, fontsize=9.2, family='monospace',
        verticalalignment='top', bbox=dict(boxstyle="round,pad=0.6", fc="#f8f9fa", ec="#cccccc", lw=1)
    )

    plt.tight_layout()
    plt.savefig(output_image_path, bbox_inches='tight', dpi=140)
    plt.close(fig)

    print(f"[OK] Mapa de segmentação semântica salvo: {output_image_path}")
    return {
        "image": image_path,
        "image_filename": os.path.basename(image_path),
        "image_width": w,
        "image_height": h,
        "total_colonies": len(colonies_report),
        "suppressed_redundant_masks": suppressed_count,
        "multi_point_colonies": multi_point_colonies,
        "quadrat_width_cm": quadrat_width_cm,
        "quadrat_height_cm": quadrat_height_cm,
        "total_area_cm2": round(total_area_cm2, 2),
        "output_image": output_image_path,
        "output_image_filename": os.path.basename(output_image_path),
        "output_csv": output_csv_path,
        "output_csv_filename": os.path.basename(output_csv_path),
        "genus_summary": genus_summary,
        "colonies": colonies_report
    }
