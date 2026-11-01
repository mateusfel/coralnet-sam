import cv2
import numpy as np
from PIL import Image
from typing import List, Tuple, Optional, Dict, Any


def order_quad_corners(pts: List[List[float]]) -> np.ndarray:
    """
    Orders 4 arbitrary 2D points [x, y] canonically as:
    [top-left, top-right, bottom-right, bottom-left].
    Works regardless of the order in which the user clicked the 4 corners
    and handles tilted/trapezoidal perspective quadrats.
    """
    arr = np.array(pts, dtype=np.float32)
    if arr.shape != (4, 2):
        raise ValueError("quadrat_corners deve conter exatamente 4 pontos [x, y].")

    # Sort by Y coordinate first to separate top pair from bottom pair
    y_sorted = arr[np.argsort(arr[:, 1])]
    top_pair = y_sorted[:2]
    bottom_pair = y_sorted[2:]

    # Sort top pair by X -> (top-left, top-right)
    tl, tr = top_pair[np.argsort(top_pair[:, 0])]
    # Sort bottom pair by X -> (bottom-left, bottom-right)
    bl, br = bottom_pair[np.argsort(bottom_pair[:, 0])]

    return np.array([tl, tr, br, bl], dtype=np.float32)


def build_quadrat_mask(width: int, height: int, corners: np.ndarray) -> np.ndarray:
    """
    Creates a uint8 binary mask (255 inside quadrat, 0 outside) of shape (height, width).
    """
    mask = np.zeros((height, width), dtype=np.uint8)
    poly = np.round(corners).astype(np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(mask, [poly], 255)
    return mask


def apply_clahe_rgb(img_rgb: np.ndarray, clip_limit: float = 2.0, grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Applies CLAHE strictly on the L (luminance) channel in CIE-LAB color space.
    Enhances 3D corallite/polyp relief without distorting chromatic hue.
    """
    lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
    cl = clahe.apply(l_ch)
    return cv2.cvtColor(cv2.merge((cl, a_ch, b_ch)), cv2.COLOR_LAB2RGB)


def apply_white_balance_rgb(
    img_rgb: np.ndarray,
    p_low: float = 1.0,
    p_high: float = 99.0,
    roi_mask: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Underwater chromatic compensation via percentile dynamic-range stretching per RGB channel.
    Removes cyan/green water-column attenuation.
    If roi_mask is provided, percentiles are calibrated exclusively on benthic pixels inside the quadrat
    (ignoring bright white PVC pipes and calibration stickers).
    """
    res = np.zeros_like(img_rgb, dtype=np.float32)
    use_roi = roi_mask is not None and np.count_nonzero(roi_mask) > 500

    for c in range(3):
        ch = img_rgb[:, :, c].astype(np.float32)
        sample = ch[roi_mask > 0] if use_roi else ch
        v_min = np.percentile(sample, p_low)
        v_max = np.percentile(sample, p_high)
        res[:, :, c] = np.clip((ch - v_min) / (v_max - v_min + 1e-5) * 255.0, 0.0, 255.0)

    return res.astype(np.uint8)


def enhance_underwater_image(
    pil_image: Image.Image,
    filter_mode: str = "combined",
    quadrat_corners: Optional[List[List[float]]] = None
) -> Image.Image:
    """
    Applies the selected underwater enhancement pipeline to a PIL RGB image:
    - 'none': Original image untouched
    - 'clahe': LAB Luminance CLAHE (clip_limit=2.5)
    - 'wb': Percentile Underwater White Balance (1% - 99%)
    - 'combined': White Balance + LAB CLAHE (clip_limit=2.0) [Recommended]
    """
    mode = (filter_mode or "combined").lower().strip()
    if mode == "none":
        return pil_image.copy()

    img_rgb = np.array(pil_image.convert("RGB"))
    h, w = img_rgb.shape[:2]

    roi_mask = None
    if quadrat_corners and len(quadrat_corners) == 4:
        ordered = order_quad_corners(quadrat_corners)
        roi_mask = build_quadrat_mask(w, h, ordered)

    if mode == "clahe":
        out_rgb = apply_clahe_rgb(img_rgb, clip_limit=2.5, grid_size=(8, 8))
    elif mode == "wb":
        out_rgb = apply_white_balance_rgb(img_rgb, p_low=1.0, p_high=99.0, roi_mask=roi_mask)
    else:  # 'combined'
        wb_rgb = apply_white_balance_rgb(img_rgb, p_low=1.0, p_high=99.0, roi_mask=roi_mask)
        out_rgb = apply_clahe_rgb(wb_rgb, clip_limit=2.0, grid_size=(8, 8))

    return Image.fromarray(out_rgb)


def prepare_quadrat_roi_crop(
    pil_image: Image.Image,
    ordered_corners: np.ndarray,
    pad_px: int = 8
) -> Dict[str, Any]:
    """
    Crops the tight bounding box around the 4-corner quadrat polygon and fills
    exterior pixels (PVC pipes, stickers, outside reef) with the smooth median benthic color
    from inside the quadrat so no artificial high-contrast border is introduced.

    Returns:
      - cropped_image: PIL.Image ready for CoralSCOP / SAM
      - offset_x, offset_y: top-left pixel offset in the original full image
      - crop_mask: uint8 binary mask (255 inside quadrat) in cropped coordinates
      - full_mask: uint8 binary mask (255 inside quadrat) in full-image coordinates
    """
    img_rgb = np.array(pil_image.convert("RGB"))
    h, w = img_rgb.shape[:2]
    full_mask = build_quadrat_mask(w, h, ordered_corners)

    xs = ordered_corners[:, 0]
    ys = ordered_corners[:, 1]
    x0 = max(0, int(np.floor(xs.min())) - pad_px)
    y0 = max(0, int(np.floor(ys.min())) - pad_px)
    x1 = min(w, int(np.ceil(xs.max())) + pad_px)
    y1 = min(h, int(np.ceil(ys.max())) + pad_px)

    crop_rgb = img_rgb[y0:y1, x0:x1].copy()
    crop_mask = full_mask[y0:y1, x0:x1]

    interior_pixels = crop_rgb[crop_mask > 0]
    if len(interior_pixels) > 0:
        fill_color = np.median(interior_pixels, axis=0).astype(np.uint8)
    else:
        fill_color = np.array([60, 70, 65], dtype=np.uint8)

    # Smoothly mask out everything outside the 4-corner quadrat polygon
    crop_rgb[crop_mask == 0] = fill_color

    return {
        "cropped_image": Image.fromarray(crop_rgb),
        "offset_x": x0,
        "offset_y": y0,
        "crop_width": x1 - x0,
        "crop_height": y1 - y0,
        "crop_mask": crop_mask,
        "full_mask": full_mask
    }


def clip_polygons_to_quadrat(
    polygons: List[List[List[int]]],
    full_quadrat_mask: np.ndarray
) -> Tuple[List[List[List[int]]], int, List[int], List[int]]:
    """
    Intersects a colony's polygon list (in full-image coordinates) with the 4-corner quadrat mask.
    Trims any coral parts extending under/outside the PVC pipes and returns:
      (clipped_polygons_sorted_by_area, clipped_area_px, new_bbox_xywh, new_centroid_yx)
    """
    h, w = full_quadrat_mask.shape[:2]
    if not polygons:
        return [], 0, [0, 0, 0, 0], [0, 0]

    # Compute tight local ROI around polygons for ultra-fast bitwise clipping
    all_pts = [pt for poly in polygons if len(poly) >= 3 for pt in poly]
    if not all_pts:
        return [], 0, [0, 0, 0, 0], [0, 0]

    pts_arr = np.array(all_pts, dtype=np.int32)
    x0 = max(0, int(pts_arr[:, 0].min()) - 2)
    y0 = max(0, int(pts_arr[:, 1].min()) - 2)
    x1 = min(w, int(pts_arr[:, 0].max()) + 3)
    y1 = min(h, int(pts_arr[:, 1].max()) + 3)

    if x1 <= x0 or y1 <= y0:
        return [], 0, [0, 0, 0, 0], [0, 0]

    local_mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    shifted_polys = []
    for poly in polygons:
        if len(poly) >= 3:
            p = np.array(poly, dtype=np.int32) - np.array([x0, y0], dtype=np.int32)
            shifted_polys.append(p.reshape((-1, 1, 2)))

    cv2.fillPoly(local_mask, shifted_polys, 255)
    clipped = cv2.bitwise_and(local_mask, full_quadrat_mask[y0:y1, x0:x1])

    area_px = int(np.count_nonzero(clipped))
    if area_px == 0:
        return [], 0, [0, 0, 0, 0], [0, 0]

    contours, _ = cv2.findContours(clipped, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    out_polys = []
    for cnt in contours:
        if cv2.contourArea(cnt) < 25:
            continue
        approx = cv2.approxPolyDP(cnt, epsilon=1.8, closed=True)
        if len(approx) >= 3:
            pts_full = (approx.reshape(-1, 2) + np.array([x0, y0])).tolist()
            out_polys.append([[int(px), int(py)] for px, py in pts_full])

    if not out_polys:
        return [], 0, [0, 0, 0, 0], [0, 0]

    ys, xs = np.nonzero(clipped)
    bx0, by0 = int(xs.min()) + x0, int(ys.min()) + y0
    bx1, by1 = int(xs.max()) + x0, int(ys.max()) + y0
    bbox = [bx0, by0, max(1, bx1 - bx0), max(1, by1 - by0)]

    # Centroid inside largest contour
    M = cv2.moments(contours[0])
    if M["m00"] > 0:
        cx = int(M["m10"] / M["m00"]) + x0
        cy = int(M["m01"] / M["m00"]) + y0
    else:
        cx = bx0 + bbox[2] // 2
        cy = by0 + bbox[3] // 2

    return out_polys, area_px, bbox, [cy, cx]


def build_quadrat_homography(
    ordered_corners: np.ndarray,
    quadrat_width_cm: float,
    quadrat_height_cm: float
) -> np.ndarray:
    """
    Computes the 3x3 perspective homography matrix H mapping full-image pixel coordinates
    (even from oblique/tilted camera angles and arbitrary diver distances) directly onto
    real-world quadrat centimeter coordinates [0..quadrat_width_cm, 0..quadrat_height_cm].
    """
    dst_cm = np.array([
        [0.0, 0.0],
        [float(quadrat_width_cm), 0.0],
        [float(quadrat_width_cm), float(quadrat_height_cm)],
        [0.0, float(quadrat_height_cm)]
    ], dtype=np.float32)
    return cv2.getPerspectiveTransform(ordered_corners.astype(np.float32), dst_cm)


def compute_polygons_area_cm2(
    polygons: List[List[List[int]]],
    homography_matrix: Optional[np.ndarray],
    fallback_cm2_per_pixel: float,
    area_pixels: int
) -> float:
    """
    Computes the true physical area (in cm²) of a multi-part coral colony.
    If a 4-corner quadrat homography matrix H is available, transforms every polygon vertex
    into perspective-rectified centimeter space and sums exact planar areas.
    """
    if homography_matrix is None or not polygons:
        return float(area_pixels) * fallback_cm2_per_pixel

    total_cm2 = 0.0
    for poly in polygons:
        if len(poly) < 3:
            continue
        pts_px = np.array(poly, dtype=np.float32).reshape((-1, 1, 2))
        pts_cm = cv2.perspectiveTransform(pts_px, homography_matrix)
        total_cm2 += float(cv2.contourArea(pts_cm))

    if total_cm2 <= 0.0:
        return float(area_pixels) * fallback_cm2_per_pixel
    return total_cm2
