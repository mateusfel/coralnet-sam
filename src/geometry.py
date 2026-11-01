import math
from typing import List, Dict, Any, Tuple
import numpy as np
import cv2


def compute_bbox_iou(box1: List[int], box2: List[int]) -> float:
    """
    Computes Intersection over Union (IoU) between two bounding boxes [x, y, w, h].
    """
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    ix1 = max(x1, x2)
    iy1 = max(y1, y2)
    ix2 = min(x1 + w1, x2 + w2)
    iy2 = min(y1 + h1, y2 + h2)

    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)
    intersection = iw * ih

    if intersection == 0:
        return 0.0

    area1 = w1 * h1
    area2 = w2 * h2
    union = area1 + area2 - intersection
    return float(intersection / union) if union > 0 else 0.0


def compute_bbox_containment(box1: List[int], box2: List[int]) -> float:
    """
    Computes the containment ratio: intersection area / area of smaller box.
    Returns 1.0 if one box is completely inside the other.
    """
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    ix1 = max(x1, x2)
    iy1 = max(y1, y2)
    ix2 = min(x1 + w1, x2 + w2)
    iy2 = min(y1 + h1, y2 + h2)

    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)
    intersection = iw * ih

    if intersection == 0:
        return 0.0

    min_area = min(w1 * h1, w2 * h2)
    return float(intersection / min_area) if min_area > 0 else 0.0


def _get_candidate_polygons(mask_dict: Dict[str, Any]) -> List[List[List[int]]]:
    polys = mask_dict.get("polygons")
    if polys and isinstance(polys, list) and len(polys) > 0:
        valid = [p for p in polys if isinstance(p, list) and len(p) >= 3]
        if valid:
            return valid
    single = mask_dict.get("polygon")
    if single and len(single) >= 3:
        return [single]
    return []


def compute_polygon_overlap(mask1: Dict[str, Any], mask2: Dict[str, Any]) -> Tuple[float, float]:
    """
    Computes exact (iou, containment) between two masks using their actual polygon contours
    rasterized on a compact local union grid (max 256px). Prevents diagonal strings or
    L-shaped corals with large axis-aligned bounding boxes from suppressing nearby colonies.
    """
    b1 = mask1["bbox"]
    b2 = mask2["bbox"]

    # Fast O(1) bounding-box pre-check: if bboxes don't touch, polygons cannot overlap
    ix1 = max(b1[0], b2[0])
    iy1 = max(b1[1], b2[1])
    ix2 = min(b1[0] + b1[2], b2[0] + b2[2])
    iy2 = min(b1[1] + b1[3], b2[1] + b2[3])
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0, 0.0

    polys1 = _get_candidate_polygons(mask1)
    polys2 = _get_candidate_polygons(mask2)
    if not polys1 or not polys2:
        return compute_bbox_iou(b1, b2), compute_bbox_containment(b1, b2)

    ux1 = min(b1[0], b2[0])
    uy1 = min(b1[1], b2[1])
    ux2 = max(b1[0] + b1[2], b2[0] + b2[2])
    uy2 = max(b1[1] + b1[3], b2[1] + b2[3])
    uw = max(1, ux2 - ux1)
    uh = max(1, uy2 - uy1)

    max_grid = 256.0
    scale = min(1.0, max_grid / float(max(uw, uh)))
    gw = max(4, int(round(uw * scale)) + 2)
    gh = max(4, int(round(uh * scale)) + 2)

    canvas1 = np.zeros((gh, gw), dtype=np.uint8)
    canvas2 = np.zeros((gh, gw), dtype=np.uint8)

    def _draw(canvas: np.ndarray, polys: List[List[List[int]]]):
        shifted = []
        for poly in polys:
            arr = (np.array(poly, dtype=np.float32) - np.array([ux1, uy1], dtype=np.float32)) * scale
            shifted.append(np.round(arr).astype(np.int32).reshape((-1, 1, 2)))
        if shifted:
            cv2.fillPoly(canvas, shifted, 1)

    _draw(canvas1, polys1)
    _draw(canvas2, polys2)

    a1 = int(np.count_nonzero(canvas1))
    a2 = int(np.count_nonzero(canvas2))
    if a1 == 0 or a2 == 0:
        return 0.0, 0.0

    inter = int(np.count_nonzero(canvas1 & canvas2))
    if inter == 0:
        return 0.0, 0.0

    union = a1 + a2 - inter
    iou = float(inter / union) if union > 0 else 0.0
    containment = float(inter / min(a1, a2))
    return iou, containment


def apply_hierarchical_nms(
    masks: List[Dict[str, Any]],
    iou_thresh: float = 0.60,
    containment_thresh: float = 0.85
) -> List[Dict[str, Any]]:
    """
    Suppresses redundant and heavily overlapping masks (Fase 2) using true polygon masks.
    Balances predicted_iou + stability_score in 2% buckets so complete coral colonies
    with larger area take precedence over tiny internal polyp/crevice fragments.
    """
    if not masks:
        return []

    def _rank_key(m: Dict[str, Any]):
        p_iou = float(m.get("predicted_iou", 0.80))
        stab = float(m.get("stability_score", 0.80))
        quality_bucket = round((p_iou * 0.65 + stab * 0.35) * 50.0) / 50.0
        return (quality_bucket, m.get("area", 0))

    sorted_masks = sorted(masks, key=_rank_key, reverse=True)

    keep = []
    for candidate in sorted_masks:
        duplicate = False

        for selected in keep:
            iou, containment = compute_polygon_overlap(candidate, selected)

            # Suppress if heavy polygon overlap or if candidate is almost fully enclosed
            if iou > iou_thresh or containment > containment_thresh:
                duplicate = True
                break

        if not duplicate:
            keep.append(candidate)

    # Re-index remaining masks cleanly
    for idx, m in enumerate(keep, 1):
        m["id"] = idx

    return keep


def sample_interior_points(
    bbox: List[int],
    polygon: List[List[int]] = None,
    n_points: int = 5,
    min_area_multi: int = 4000,
    polygons: List[List[List[int]]] = None,
    centroid: List[int] = None
) -> List[Tuple[int, int]]:
    """
    Extracts interior sampling points (row, col) inside a colony for Multi-Point Voting.
    If area < min_area_multi, returns just the interior centroid.
    If area >= min_area_multi, samples up to n_points strictly inside the colony polygon(s).
    """
    x, y, w, h = bbox
    if centroid and len(centroid) == 2:
        cy, cx = int(centroid[0]), int(centroid[1])
    else:
        cx = x + w // 2
        cy = y + h // 2
    area = w * h

    poly_list = []
    if polygons:
        poly_list = [np.array(p, dtype=np.int32) for p in polygons if len(p) >= 3]
    elif polygon and len(polygon) >= 3:
        poly_list = [np.array(polygon, dtype=np.int32)]

    def _is_inside(r_pt: int, c_pt: int) -> bool:
        if not poly_list:
            return True
        for p_np in poly_list:
            if cv2.pointPolygonTest(p_np, (float(c_pt), float(r_pt)), False) >= 0:
                return True
        return False

    # Ensure primary point lands inside actual coral tissue (handles crescent colonies)
    primary = (cy, cx)
    if poly_list and not _is_inside(cy, cx):
        M = cv2.moments(poly_list[0])
        if M["m00"] > 0:
            mcx = int(M["m10"] / M["m00"])
            mcy = int(M["m01"] / M["m00"])
            if _is_inside(mcy, mcx):
                primary = (mcy, mcx)

    if area < min_area_multi or n_points <= 1:
        return [primary]

    points = [primary]
    p_cy, p_cx = primary
    dx_offset = max(4, int(w * 0.24))
    dy_offset = max(4, int(h * 0.24))

    candidates = [
        (p_cy - dy_offset, p_cx),
        (p_cy + dy_offset, p_cx),
        (p_cy, p_cx - dx_offset),
        (p_cy, p_cx + dx_offset),
        (p_cy - dy_offset, p_cx - dx_offset),
        (p_cy + dy_offset, p_cx + dx_offset),
        (p_cy - dy_offset, p_cx + dx_offset),
        (p_cy + dy_offset, p_cx - dx_offset),
    ]

    for r_cand, c_cand in candidates:
        if len(points) >= n_points:
            break
        if not (y <= r_cand <= y + h and x <= c_cand <= x + w):
            continue
        if _is_inside(r_cand, c_cand):
            points.append((r_cand, c_cand))

    return points


def generate_approx_polygon(bbox: List[int]) -> List[List[int]]:
    """
    Generates an 8-sided organic rounded polygon fitting a bounding box
    when exact SAM polygons are not yet transmitted.
    """
    x, y, w, h = bbox
    cx, cy = x + w / 2, y + h / 2
    rx, ry = w / 2, h / 2

    pts = []
    n_pts = 16
    for i in range(n_pts):
        angle = 2 * math.pi * i / n_pts
        # Slightly modulate radius for natural contour
        r_mod = 1.0 - 0.05 * math.sin(3 * angle)
        px = int(cx + rx * math.cos(angle) * r_mod)
        py = int(cy + ry * math.sin(angle) * r_mod)
        pts.append([px, py])
    return pts
