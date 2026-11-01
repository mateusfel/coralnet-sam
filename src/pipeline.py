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


def run_hybrid_pipeline(
    image_path: str,
    colab_url: str = None,
    output_dir: str = "output"
) -> Dict[str, Any]:
    """
    Executes the 100% automated 2-Stage Benthic Segmentation:
    1. Remote SAM ViT-H on Colab GPU: Discovers all colonies & boundaries (Zero human clicks)
    2. Local CoralNet EfficientNet-B0: Classifies each colony into Brazilian reef taxonomy
    """
    os.makedirs(output_dir, exist_ok=True)
    image = Image.open(image_path).convert("RGB")
    w, h = image.size

    print(f"\n{'='*70}")
    print(f"[*] Iniciando Pipeline Híbrido: {os.path.basename(image_path)} ({w}x{h} px)")
    print(f"{'='*70}")

    # Stage 1: Segment Anything Model (Remote on Colab GPU)
    sam_client = RemoteSAMClient(colab_url=colab_url)
    
    if colab_url:
        sam_data = sam_client.segment_image(image_path)
        masks = sam_data.get("masks", [])
    else:
        print("[!] Nenhuma URL do Google Colab fornecida.")
        print("    Gerando grade de segmentação representativa para teste local...")
        # Local simulated test proposal
        masks = []
        grid_dim = 6
        for r_idx in range(grid_dim):
            y0 = int(r_idx * h / grid_dim)
            y1 = int((r_idx + 1) * h / grid_dim)
            for c_idx in range(grid_dim):
                x0 = int(c_idx * w / grid_dim)
                x1 = int((c_idx + 1) * w / grid_dim)
                masks.append({
                    "id": len(masks) + 1,
                    "bbox": [x0, y0, x1 - x0, y1 - y0],
                    "centroid": [(y0 + y1) // 2, (x0 + x1) // 2],
                    "area": (x1 - x0) * (y1 - y0),
                    "area_pct": (((x1 - x0) * (y1 - y0)) / (w * h)) * 100.0
                })

    print(f"[*] Total de {len(masks)} colônias/zonas a classificar com o CoralNet...")

    # Stage 2: CoralNet Taxonomic Classification (Local EfficientNet-B0)
    classifier = LocalCoralClassifier()
    centroids = [tuple(m["centroid"]) for m in masks]
    classifications = classifier.classify_centroids(image, centroids)

    # Stage 3: Merge Masks + Taxonomy & Compute Real Ecological Area
    colonies_report = []
    genus_area_counter = Counter()
    genus_colony_counter = Counter()
    total_area_pixels = w * h

    for m, c in zip(masks, classifications):
        genus = c["genus"]
        area = m.get("area", 100)
        genus_area_counter[genus] += area
        genus_colony_counter[genus] += 1

        colonies_report.append({
            "id": m["id"],
            "genus": genus,
            "confidence": c["confidence"],
            "color": c["color"],
            "bbox": m["bbox"],
            "centroid": m["centroid"],
            "area_pixels": area,
            "area_pct": (area / total_area_pixels) * 100.0,
            "alternatives": c["alternatives"]
        })

    # Summary table in terminal
    print("\n--- Relatório Ecológico Automatizado ---")
    print(f"{'Gênero / Substrato':<32} | {'Colônias':<10} | {'Cobertura (%)':<15}")
    print("-" * 65)
    for genus, count in genus_colony_counter.most_common():
        pct = (genus_area_counter[genus] / total_area_pixels) * 100.0
        print(f"{genus:<32} | {count:<10} | {pct:.1f}%")

    # Stage 4: Render High-Resolution Annotated Semantic Map
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_image_path = os.path.join(output_dir, f"{base_name}_sam_coralnet.jpg")

    fig, (ax_img, ax_legend) = plt.subplots(
        1, 2, figsize=(16, 9),
        gridspec_kw={'width_ratios': [4, 1.2]}, dpi=120
    )

    ax_img.imshow(image)
    ax_img.set_title(f"SAM ViT-H + CoralNet: {os.path.basename(image_path)}", fontsize=13, fontweight='bold')
    ax_img.axis('off')

    # Draw semi-transparent polygons/rectangles
    for col in colonies_report:
        x, y, bw, bh = col["bbox"]
        color = col["color"]
        rect = mpatches.Rectangle((x, y), bw, bh, linewidth=1.5, edgecolor=color, facecolor=color, alpha=0.32)
        ax_img.add_patch(rect)
        ax_img.text(
            x + 5, y + 20, f"#{col['id']} {col['genus']}",
            color='white', fontsize=7.5, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.2", fc=color, ec="black", lw=0.6, alpha=0.85)
        )

    # Legend Panel
    ax_legend.axis('off')
    summary_lines = ["=== Cobertura Bêntica Real ===", f"Colônias Detectadas: {len(colonies_report)}", ""]
    for genus, count in genus_colony_counter.most_common():
        pct = (genus_area_counter[genus] / total_area_pixels) * 100.0
        summary_lines.append(f"{genus}:\n  {count} colônias ({pct:.1f}%)")

    ax_legend.text(
        0.05, 0.95, "\n".join(summary_lines),
        transform=ax_legend.transAxes, fontsize=10, family='monospace',
        verticalalignment='top', bbox=dict(boxstyle="round,pad=0.6", fc="#f8f9fa", ec="#cccccc", lw=1)
    )

    plt.tight_layout()
    plt.savefig(output_image_path, bbox_inches='tight', dpi=120)
    plt.close(fig)

    print(f"\n[OK] Mapa de segmentação semântica salvo: {output_image_path}")
    return {
        "image": image_path,
        "total_colonies": len(colonies_report),
        "output_image": output_image_path,
        "colonies": colonies_report
    }
