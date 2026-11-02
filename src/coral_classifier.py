import os
import math
from typing import List, Dict, Any, Tuple
import cv2
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms

from src.few_shot_memory import CORAL_GENERA, CLASS_COLORS

# Strictly 11 Coral Genera (kept as TARGET_CLASSES alias for compatibility)
TARGET_CLASSES = CORAL_GENERA

# Canonical WoRMS / TreeOfLife-200M / ReefNet Taxonomic & Morphological Prompts per Coral Genus
GENUS_TAXONOMIC_PROMPTS: Dict[str, List[str]] = {
    "Montastraea": [
        "Animalia Cnidaria Anthozoa Scleractinia Montastraeidae Montastraea cavernosa",
        "Animalia Cnidaria Anthozoa Scleractinia Montastraeidae Montastraea",
        "underwater close-up of Montastraea cavernosa great star hard coral colony with large protruding plocoid corallites"
    ],
    "Mussismilia": [
        "Animalia Cnidaria Anthozoa Scleractinia Mussidae Mussismilia hispida",
        "Animalia Cnidaria Anthozoa Scleractinia Mussidae Mussismilia braziliensis",
        "Animalia Cnidaria Anthozoa Scleractinia Mussidae Mussismilia harttii",
        "Animalia Cnidaria Anthozoa Scleractinia Mussidae Mussismilia leptophylla",
        "Animalia Cnidaria Anthozoa Scleractinia Faviidae Mussismilia",
        "underwater close-up of Mussismilia massive Brazilian hard coral colony with large spinose toothed calices"
    ],
    "Porites": [
        "Animalia Cnidaria Anthozoa Scleractinia Poritidae Porites astreoides",
        "Animalia Cnidaria Anthozoa Scleractinia Poritidae Porites branneri",
        "Animalia Cnidaria Anthozoa Scleractinia Poritidae Porites",
        "underwater close-up of Porites astreoides mustard hill porous hard coral colony with tiny smooth pinhole corallites"
    ],
    "Siderastrea": [
        "Animalia Cnidaria Anthozoa Scleractinia Siderastreidae Siderastrea stellata",
        "Animalia Cnidaria Anthozoa Scleractinia Rhizangiidae Siderastrea stellata",
        "Animalia Cnidaria Anthozoa Scleractinia Siderastreidae Siderastrea siderea",
        "Animalia Cnidaria Anthozoa Scleractinia Siderastreidae Siderastrea radians",
        "underwater close-up of Siderastrea starlet encrusting hard coral colony with small cerioid star-shaped corallites"
    ],
    "Agaricia": [
        "Animalia Cnidaria Anthozoa Scleractinia Agariciidae Agaricia agaricites",
        "Animalia Cnidaria Anthozoa Scleractinia Agariciidae Agaricia humilis",
        "Animalia Cnidaria Anthozoa Scleractinia Agariciidae Agaricia fragilis",
        "underwater close-up of Agaricia lettuce plate hard coral colony with fine parallel ridges and valleys"
    ],
    "Millepora": [
        "Animalia Cnidaria Hydrozoa Anthoathecata Milleporidae Millepora alcicornis",
        "Animalia Cnidaria Hydrozoa Anthoathecata Milleporidae Millepora braziliensis",
        "Animalia Cnidaria Hydrozoa Anthoathecata Milleporidae Millepora nitida",
        "underwater close-up of Millepora smooth yellow-brown branching or blade fire hydrocoral colony with white tips"
    ],
    "Madracis": [
        "Animalia Cnidaria Anthozoa Scleractinia Astrocoeniidae Madracis decactis",
        "Animalia Cnidaria Anthozoa Scleractinia Pocilloporidae Madracis decactis",
        "Animalia Cnidaria Anthozoa Scleractinia Pocilloporidae Madracis",
        "underwater close-up of Madracis decactis nodular finger hard coral colony with ten-ray star septa"
    ],
    "Meandrina": [
        "Animalia Cnidaria Anthozoa Scleractinia Meandrinidae Meandrina braziliensis",
        "Animalia Cnidaria Anthozoa Scleractinia Meandrinidae Meandrina meandrites",
        "underwater close-up of Meandrina maze brain hard coral colony with sinuous valleys and thick bright septa"
    ],
    "Stephanocoenia": [
        "Animalia Cnidaria Anthozoa Scleractinia Astrocoeniidae Stephanocoenia intersepta",
        "Animalia Cnidaria Anthozoa Scleractinia Astrocoeniidae Stephanocoenia",
        "underwater close-up of Stephanocoenia intersepta blushing star hard coral colony with closely packed star corallites"
    ],
    "Scolymia": [
        "Animalia Cnidaria Anthozoa Scleractinia Mussidae Scolymia wellsi",
        "Animalia Cnidaria Anthozoa Scleractinia Mussidae Scolymia cubensis",
        "underwater close-up of Scolymia solitary circular fleshy disk hard coral polyp with radial septa"
    ],
    "Favia": [
        "Animalia Cnidaria Anthozoa Scleractinia Faviidae Favia gravida",
        "Animalia Cnidaria Anthozoa Scleractinia Mussidae Favia fragum",
        "Animalia Cnidaria Anthozoa Scleractinia Faviidae Favia",
        "underwater close-up of Favia gravida small golfball hard coral colony with raised oval corallites"
    ]
}


def _extract_square_masked_crop(
    img_rgb: np.ndarray,
    full_poly_list: List[List[List[int]]],
    cx: int,
    cy: int,
    side_px: int,
    out_size: int = 224,
    dim_outside_alpha: float = 0.65
) -> Image.Image:
    """
    Extracts a square crop of size `side_px x side_px` centered at (cx, cy) without
    aspect-ratio distortion, softly attenuating pixels outside the colony's polygon mask
    toward the interior median color so surrounding rock/neighbors never hijack classification.
    """
    h, w = img_rgb.shape[:2]
    half = max(16, side_px // 2)
    x0, y0 = cx - half, cy - half
    x1, y1 = x0 + 2 * half, y0 + 2 * half

    # Clamp intersection with image bounds
    ix0, iy0 = max(0, x0), max(0, y0)
    ix1, iy1 = min(w, x1), min(h, y1)

    sub_img = img_rgb[iy0:iy1, ix0:ix1]
    if sub_img.size == 0:
        return Image.fromarray(np.zeros((out_size, out_size, 3), dtype=np.uint8))

    # Build local polygon mask on the intersecting window
    local_mask = np.zeros((iy1 - iy0, ix1 - ix0), dtype=np.uint8)
    shifted = []
    for poly in full_poly_list:
        if poly and len(poly) >= 3:
            arr = np.array(poly, dtype=np.int32) - np.array([ix0, iy0], dtype=np.int32)
            shifted.append(arr.reshape((-1, 1, 2)))
    if shifted:
        cv2.fillPoly(local_mask, shifted, 255)

    inside_px = sub_img[local_mask > 0]
    if len(inside_px) > 20:
        med_color = np.median(inside_px, axis=0).astype(np.float32)
    else:
        med_color = np.median(sub_img.reshape(-1, 3), axis=0).astype(np.float32)

    # Create padded square canvas filled with neutral median color
    canvas = np.broadcast_to(med_color.astype(np.uint8), (2 * half, 2 * half, 3)).copy()
    mask_canvas = np.zeros((2 * half, 2 * half), dtype=np.uint8)

    px0, py0 = ix0 - x0, iy0 - y0
    px1, py1 = px0 + (ix1 - ix0), py0 + (iy1 - iy0)
    canvas[py0:py1, px0:px1] = sub_img
    mask_canvas[py0:py1, px0:px1] = local_mask

    if dim_outside_alpha > 0.0 and shifted:
        # Soft feather on mask border (5x5 blur) so colony outline stays natural
        soft_m = cv2.GaussianBlur(mask_canvas.astype(np.float32) / 255.0, (5, 5), 0)[..., None]
        keep_weight = (1.0 - dim_outside_alpha) + dim_outside_alpha * soft_m
        blended = canvas.astype(np.float32) * keep_weight + med_color[None, None, :] * (1.0 - keep_weight)
        canvas = np.clip(blended, 0, 255).astype(np.uint8)

    pil_crop = Image.fromarray(canvas)
    if canvas.shape[0] != out_size:
        pil_crop = pil_crop.resize((out_size, out_size), Image.Resampling.LANCZOS)
    return pil_crop


def build_colony_multiscale_crops(
    img_rgb: np.ndarray,
    mask_dict: Dict[str, Any],
    sample_points: List[Tuple[int, int]],
    tile_size: int = 224,
    max_micro_crops: int = 4
) -> Tuple[List[Image.Image], List[Image.Image]]:
    """
    Generates Multi-Scale 224x224 crops from the full-resolution color-compensated image:
      1. Macro View (1 crop): Full colony bounding box (+12% margin, square-padded, outside dimmed 70%)
         -> Captures overall colony growth form (brain/meandroid, massive dome, plate, branching).
      2. Micro Views (1..4 crops): Native-resolution 224x224 interior patches matching ReefNet 1.0's
         exact training protocol -> Captures razor-sharp corallite walls, calices, and septal teeth.
    """
    bx, by, bw, bh = mask_dict["bbox"]
    polys = mask_dict.get("polygons") or ([mask_dict["polygon"]] if mask_dict.get("polygon") else [])

    # 1. Macro Colony Crop
    macro_cx = bx + bw // 2
    macro_cy = by + bh // 2
    macro_side = max(96, int(round(max(bw, bh) * 1.14)))
    macro_crop = _extract_square_masked_crop(
        img_rgb=img_rgb,
        full_poly_list=polys,
        cx=macro_cx,
        cy=macro_cy,
        side_px=macro_side,
        out_size=tile_size,
        dim_outside_alpha=0.70
    )

    # 2. Micro Native-Scale Corallite Crops (ReefNet 224x224 protocol)
    pts = sample_points[:max_micro_crops] if sample_points else [(mask_dict["centroid"][0], mask_dict["centroid"][1])]
    min_dim = min(bw, bh)
    # Use native 224px on medium/large colonies; tighten window on tiny recruits so rock doesn't dominate
    micro_side = tile_size if min_dim >= 190 else max(84, int(round(min_dim * 0.92)))

    micro_crops = []
    for (pr, pc) in pts:
        mc = _extract_square_masked_crop(
            img_rgb=img_rgb,
            full_poly_list=polys,
            cx=int(pc),
            cy=int(pr),
            side_px=micro_side,
            out_size=tile_size,
            dim_outside_alpha=0.55
        )
        micro_crops.append(mc)

    return [macro_crop], micro_crops


def pack_colonies_spritesheet(
    pil_image: Image.Image,
    masks: List[Dict[str, Any]],
    colony_points_list: List[List[Tuple[int, int]]],
    tile_size: int = 224,
    grid_cols: int = 10
) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Packs all Macro + Micro 224x224 full-resolution colony crops into a single compact RGB
    sprite-sheet image + slice index manifest for a single fast GPU batch call to BioCLIP 2.5.
    """
    img_rgb = np.array(pil_image.convert("RGB"))
    all_tiles: List[Image.Image] = []
    colony_manifest = []

    for m, pts in zip(masks, colony_points_list):
        macro_list, micro_list = build_colony_multiscale_crops(
            img_rgb=img_rgb,
            mask_dict=m,
            sample_points=pts,
            tile_size=tile_size,
            max_micro_crops=4
        )
        macro_indices = []
        for crop in macro_list:
            macro_indices.append(len(all_tiles))
            all_tiles.append(crop)

        micro_indices = []
        for crop in micro_list:
            micro_indices.append(len(all_tiles))
            all_tiles.append(crop)

        colony_manifest.append({
            "id": m["id"],
            "macro_indices": macro_indices,
            "micro_indices": micro_indices
        })

    total_tiles = len(all_tiles)
    if total_tiles == 0:
        empty_sheet = Image.new("RGB", (tile_size, tile_size), (0, 0, 0))
        return empty_sheet, {"tile_size": tile_size, "cols": 1, "total_tiles": 0, "colonies": []}

    cols = min(grid_cols, total_tiles)
    rows = int(math.ceil(total_tiles / float(cols)))
    sheet = Image.new("RGB", (cols * tile_size, rows * tile_size), (0, 0, 0))

    for idx, tile in enumerate(all_tiles):
        r = idx // cols
        c = idx % cols
        sheet.paste(tile, (c * tile_size, r * tile_size))

    metadata = {
        "tile_size": tile_size,
        "cols": cols,
        "rows": rows,
        "total_tiles": total_tiles,
        "colonies": colony_manifest
    }
    return sheet, metadata


class LocalCoralClassifier:
    """
    Offline local fallback classifier (used ONLY when no Google Colab BioCLIP 2.5 GPU URL is provided).
    Outputs strictly the 11 CORAL_GENERA and produces normalized feature vectors + zero_shot_sims
    matching the BioCLIP 2.5 schema so local offline testing and Few-Shot UI remain functional.
    """

    def __init__(self, weights_path: str = None, patch_size: int = 224, device: str = None):
        self.patch_size = patch_size
        self.classes = CORAL_GENERA
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        if weights_path is None:
            default_weights = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "models", "efficientnet_b0_ver1.pth"
            )
            weights_path = default_weights if os.path.exists(default_weights) else None

        self.backbone = models.efficientnet_b0(weights=None)
        if weights_path and os.path.exists(weights_path):
            state_dict = torch.load(weights_path, map_location="cpu")
            self.backbone.load_state_dict(state_dict, strict=False)
        else:
            self.backbone = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)

        self.backbone.classifier = nn.Identity()
        self.backbone.eval()
        self.backbone.to(self.device)

        cpu_rng = torch.get_rng_state()
        torch.manual_seed(42)
        proj = torch.randn(1280, len(self.classes))
        proj = proj / torch.norm(proj, dim=0, keepdim=True)
        torch.set_rng_state(cpu_rng)
        self.genus_prototypes = proj.to(self.device)

        self.preprocess = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    @torch.no_grad()
    def extract_offline_bioclip_like(
        self,
        pil_image: Image.Image,
        masks: List[Dict[str, Any]],
        colony_points_list: List[List[Tuple[int, int]]]
    ) -> List[Dict[str, Any]]:
        img_rgb = np.array(pil_image.convert("RGB"))
        results = []
        if not masks:
            return results

        all_crops = []
        slices = []
        for m, pts in zip(masks, colony_points_list):
            macro_list, micro_list = build_colony_multiscale_crops(img_rgb, m, pts, tile_size=224, max_micro_crops=3)
            s0 = len(all_crops)
            all_crops.extend(macro_list)
            s_mid = len(all_crops)
            all_crops.extend(micro_list)
            s1 = len(all_crops)
            slices.append((s0, s_mid, s1))

        feats_list = []
        for i in range(0, len(all_crops), 16):
            batch = torch.stack([self.preprocess(c) for c in all_crops[i:i + 16]]).to(self.device)
            f = self.backbone(batch)
            f = f / torch.clamp(torch.norm(f, dim=1, keepdim=True), min=1e-7)
            feats_list.append(f)

        all_feats = torch.cat(feats_list, dim=0)

        for (s0, s_mid, s1) in slices:
            f_macro = all_feats[s0:s_mid].mean(dim=0)
            f_micro = all_feats[s_mid:s1].mean(dim=0) if s1 > s_mid else f_macro
            fused = 0.35 * f_macro + 0.65 * f_micro
            fused = fused / torch.clamp(torch.norm(fused), min=1e-7)

            view_sims = torch.matmul(all_feats[s0:s1], self.genus_prototypes)
            votes = torch.argmax(view_sims, dim=1).cpu().numpy().tolist()

            sims = torch.matmul(fused, self.genus_prototypes).cpu().numpy()
            top_idx = int(np.argmax(sims))
            consensus = float(sum(1 for v in votes if v == top_idx) / max(1, len(votes)))

            zero_shot_sims = {g: round(float(sims[idx]), 5) for idx, g in enumerate(self.classes)}
            results.append({
                "embedding": [round(float(x), 5) for x in fused.cpu().numpy().tolist()],
                "zero_shot_sims": zero_shot_sims,
                "consensus_ratio": round(consensus, 3),
                "views_count": int(s1 - s0)
            })

        return results


_CLASSIFIER_SINGLETON: LocalCoralClassifier = None


def get_coral_classifier() -> LocalCoralClassifier:
    global _CLASSIFIER_SINGLETON
    if _CLASSIFIER_SINGLETON is None:
        _CLASSIFIER_SINGLETON = LocalCoralClassifier()
    return _CLASSIFIER_SINGLETON
