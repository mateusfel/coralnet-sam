import os
import csv
from typing import Dict, Any, List, Optional
from collections import Counter
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from src.sam_client import RemoteSAMClient
from src.coral_classifier import get_coral_classifier, CLASS_COLORS
from src.geometry import (
    apply_hierarchical_nms,
    sample_interior_points,
    generate_approx_polygon
)
from src.preprocessing import (
    order_quad_corners,
    enhance_underwater_image,
    prepare_quadrat_roi_crop,
    clip_polygons_to_quadrat,
    build_quadrat_homography,
    compute_polygons_area_cm2
)


FILTER_LABELS = {
    "combined": "Combinado (Balanço de Branco + CLAHE)",
    "wb": "Balanço de Branco Subaquático",
    "clahe": "CLAHE (Realce de Textura LAB)",
    "none": "Original (Sem Filtro)"
}


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
    render_on_enhanced: bool = False
) -> Dict[str, Any]:
    """
    Executes the Automated Benthic Coral Segmentation Pipeline (CoralSCOP + CoralNet):
    0. Underwater Preprocessing (White Balance + LAB CLAHE) & Optional 4-Corner Quadrat ROI
    1. Remote CoralSCOP ViT-B (or SAM) on Colab GPU: Semantic coral-only colony segmentation
    2. Reprojection onto full original photo & strict 4-corner quadrat polygon clipping
    3. Polygon-Mask Hierarchical NMS: Eliminates redundant overlapping masks
    4. Multi-Point Interior Sampling & EfficientNet-B0 Taxonomic Classification
    5. Perspective-Rectified Physical Metrics (cm² via 4-point Homography)
    6. Multi-Polygon Contour Rendering on Original Image & CSV Export
    """
    os.makedirs(output_dir, exist_ok=True)
    orig_image = Image.open(image_path).convert("RGB")
    w, h = orig_image.size
    base_name = os.path.splitext(os.path.basename(image_path))[0]

    total_area_cm2 = float(quadrat_width_cm) * float(quadrat_height_cm)
    has_quadrat_roi = bool(quadrat_corners and len(quadrat_corners) == 4)
    ordered_corners = order_quad_corners(quadrat_corners) if has_quadrat_roi else None

    # Stage 0: Underwater Optical Enhancement
    filter_mode_clean = (filter_mode or "combined").lower().strip()
    enhanced_image = enhance_underwater_image(
        orig_image,
        filter_mode=filter_mode_clean,
        quadrat_corners=quadrat_corners if has_quadrat_roi else None
    )

    enhanced_filename = f"{base_name}_enhanced_{filter_mode_clean}.jpg"
    enhanced_path = os.path.join(output_dir, enhanced_filename)
    enhanced_image.save(enhanced_path, format="JPEG", quality=93)

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

    print(f"\n{'='*74}")
    print(f"[*] Iniciando Pipeline CoralSCOP + CoralNet: {os.path.basename(image_path)} ({w}x{h} px)")
    print(f"    Filtro Subaquático: {FILTER_LABELS.get(filter_mode_clean, filter_mode_clean)}")
    print(f"    Quadrante ROI 4-Cantos: {'Ativo (Homografia Calibrada)' if has_quadrat_roi else 'Imagem Inteira'}")
    print(f"    GPU Params: pts/side={points_per_side} | pred_iou={pred_iou_thresh} | stability={stability_score_thresh} | crops={crop_n_layers}")
    print(f"    Filtros: min_area={min_area}px | nms_iou={iou_thresh} | escala={quadrat_width_cm}x{quadrat_height_cm}cm")
    print(f"{'='*74}")

    # Stage 1: CoralSCOP / SAM Segmentation on Colab GPU (or Local Simulation Fallback)
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
        print("[!] Nenhuma URL do Google Colab fornecida.")
        print("    Gerando grade de segmentação representativa para teste local...")
        raw_masks = []
        grid_dim = 5
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

    # Stage 1.5: Strict 4-Corner Quadrat Polygon Clipping (discards pipes & outside corals)
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

    # Stage 2: Polygon-Mask Hierarchical NMS & Containment Suppression
    filtered_masks = apply_hierarchical_nms(
        raw_masks,
        iou_thresh=iou_thresh,
        containment_thresh=containment_thresh
    )
    suppressed_count = len(raw_masks) - len(filtered_masks)
    print(f"[*] [NMS Poligonal] Suprimidas {suppressed_count} máscaras sobrepostas redundantes.")
    print(f"[*] Total de {len(filtered_masks)} colônias refinadas para análise.")

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

    print(f"[*] [Multi-Ponto] {multi_point_colonies} colônias grandes receberam amostragem multi-ponto (até {n_points_multi} pontos).")

    # Stage 4: CoralNet Taxonomic Classification (on color-compensated enhanced image!)
    classifier = get_coral_classifier()
    classifications = classifier.classify_colonies_multipoint(
        enhanced_image,
        colony_points_list,
        coral_only=is_coralscop
    )

    # Stage 5: Merge Masks, Taxonomy & Perspective-Corrected Area in cm²
    colonies_report = []
    genus_area_counter = Counter()
    genus_cm2_counter = Counter()
    genus_colony_counter = Counter()

    for m, c, pts in zip(filtered_masks, classifications, colony_points_list):
        genus = c["genus"]
        polys = m.get("polygons") or ([m["polygon"]] if m.get("polygon") else [])
        area_px = int(m.get("area", m["bbox"][2] * m["bbox"][3]))
        area_cm2 = compute_polygons_area_cm2(
            polygons=polys,
            homography_matrix=homography_matrix,
            fallback_cm2_per_pixel=fallback_cm2_per_pixel,
            area_pixels=area_px
        )
        cov_pct = (area_cm2 / total_area_cm2) * 100.0 if total_area_cm2 > 0 else 0.0

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
            "polygons": polys,
            "centroid": m["centroid"],
            "area_pixels": area_px,
            "area_cm2": round(area_cm2, 2),
            "area_pct": round(cov_pct, 2),
            "alternatives": c["alternatives"]
        })

    # Build Ecological Summary Table
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

    # Summary table in terminal
    print("\n--- Relatório Ecológico Automatizado (cm² Corrigido & Taxonomia) ---")
    print(f"{'Gênero / Substrato':<32} | {'Colônias':<10} | {'Área (cm²)':<12} | {'Cobertura (%)':<15}")
    print("-" * 75)
    for row in genus_summary:
        print(f"{row['genus']:<32} | {row['count']:<10} | {row['area_cm2']:<12.1f} | {row['coverage_pct']:.1f}%")
    print("-" * 75)
    print(f"Cobertura Coralínea Total Detectada: {total_coral_cm2:.1f} cm² ({total_coral_cover_pct:.1f}% do quadrante)")

    output_image_path = os.path.join(output_dir, f"{base_name}_sam_coralnet.jpg")
    output_csv_path = os.path.join(output_dir, f"{base_name}_ecological_report.csv")

    # Export CSV Report
    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "Colony_ID", "Genus", "Confidence", "Consensus_Ratio", "Sample_Points",
            "Polygon_Parts", "Area_Pixels", "Area_cm2", "Coverage_Pct",
            "Centroid_Y", "Centroid_X", "BBox_X", "BBox_Y", "BBox_W", "BBox_H"
        ])
        for col in colonies_report:
            bx, by, bw, bh = col["bbox"]
            cy, cx = col["centroid"]
            writer.writerow([
                col["id"], col["genus"], col["confidence"], col["consensus_ratio"],
                col["sample_points_count"], len(col.get("polygons", [])),
                col["area_pixels"], col["area_cm2"], col["area_pct"],
                cy, cx, bx, by, bw, bh
            ])
    print(f"[OK] Relatório tabulado exportado: {output_csv_path}")

    # Stage 6: Render High-Resolution Annotated Semantic Map back onto Full Image
    bg_display_img = enhanced_image if render_on_enhanced else orig_image
    fig, (ax_img, ax_legend) = plt.subplots(
        1, 2, figsize=(16, 9),
        gridspec_kw={'width_ratios': [4, 1.25]}, dpi=140
    )

    ax_img.imshow(bg_display_img)
    title_engine = "CoralSCOP ViT-B" if is_coralscop else remote_model_name
    ax_img.set_title(
        f"{title_engine} + CoralNet: {os.path.basename(image_path)} [{quadrat_width_cm:.0f}x{quadrat_height_cm:.0f} cm]",
        fontsize=12.5, fontweight='bold'
    )
    ax_img.axis('off')

    # Draw demarcated 4-corner quadrat boundary if used
    if has_quadrat_roi and ordered_corners is not None:
        quad_patch = mpatches.Polygon(
            ordered_corners.tolist(),
            closed=True,
            fill=False,
            edgecolor="#38bdf8",
            linewidth=2.0,
            linestyle="--",
            alpha=0.9
        )
        ax_img.add_patch(quad_patch)

    # Draw all polygon parts for every colony onto the full photo
    for col in colonies_report:
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

        if col["sample_points_count"] > 1:
            for pr, pc in col["sample_points"]:
                ax_img.plot(pc, pr, marker='+', markersize=4, color='white', markeredgewidth=1.0)

        cy, cx = col["centroid"]
        if col["area_pct"] >= 0.12 or col["id"] <= 35:
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
        f"Motor: {title_engine}",
        f"Filtro: {filter_mode_clean.upper()}",
        f"ROI 4-Cantos: {'Sim (Homografia)' if has_quadrat_roi else 'Não (Foto toda)'}",
        f"Escala: {quadrat_width_cm:.0f}x{quadrat_height_cm:.0f} cm ({total_area_cm2:.0f} cm²)",
        f"Colônias: {len(colonies_report)}",
        f"Cobertura Total: {total_coral_cm2:.1f} cm² ({total_coral_cover_pct}%)",
        ""
    ]
    for row in genus_summary:
        summary_lines.append(f"{row['genus']}:\n  {row['count']} col ({row['area_cm2']} cm² | {row['coverage_pct']}%)")

    ax_legend.text(
        0.04, 0.96, "\n".join(summary_lines),
        transform=ax_legend.transAxes, fontsize=8.8, family='monospace',
        verticalalignment='top', bbox=dict(boxstyle="round,pad=0.6", fc="#f8f9fa", ec="#cccccc", lw=1)
    )

    plt.tight_layout()
    plt.savefig(output_image_path, bbox_inches='tight', dpi=140)
    plt.close(fig)

    print(f"[OK] Mapa de segmentação semântica salvo: {output_image_path}")
    return {
        "image": image_path,
        "image_filename": os.path.basename(image_path),
        "enhanced_image_filename": enhanced_filename,
        "filter_mode": filter_mode_clean,
        "filter_label": FILTER_LABELS.get(filter_mode_clean, filter_mode_clean),
        "remote_model": remote_model_name,
        "is_coralscop": is_coralscop,
        "has_quadrat_roi": has_quadrat_roi,
        "quadrat_corners": ordered_corners.tolist() if ordered_corners is not None else None,
        "image_width": w,
        "image_height": h,
        "total_colonies": len(colonies_report),
        "total_coral_cm2": round(total_coral_cm2, 2),
        "total_coral_cover_pct": total_coral_cover_pct,
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
