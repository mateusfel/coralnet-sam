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


def apply_hierarchical_nms(
    masks: List[Dict[str, Any]],
    iou_thresh: float = 0.60,
    containment_thresh: float = 0.85
) -> List[Dict[str, Any]]:
    """
    Suppresses redundant and heavily overlapping masks (Fase 2).
    Keeps masks with higher stability score / confidence or dominant area.
    """
    if not masks:
        return []

    # Sort primarily by stability_score, then area
    sorted_masks = sorted(
        masks,
        key=lambda m: (m.get("stability_score", 0.9), m.get("area", 0)),
        reverse=True
    )

    keep = []
    for candidate in sorted_masks:
        c_box = candidate["bbox"]
        c_area = candidate.get("area", c_box[2] * c_box[3])
        duplicate = False

        for selected in keep:
            s_box = selected["bbox"]
            iou = compute_bbox_iou(c_box, s_box)
            containment = compute_bbox_containment(c_box, s_box)

            # Suppress if heavy overlap or if candidate is almost fully enclosed in selected
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
    min_area_multi: int = 4000
) -> List[Tuple[int, int]]:
    """
    Extracts interior sampling points (row, col) inside a colony for Multi-Point Voting.
    If area < min_area_multi, returns just the centroid.
    If area >= min_area_multi, samples up to n_points inside the colony boundary.
    """
    x, y, w, h = bbox
    cx = x + w // 2
    cy = y + h // 2
    area = w * h

    if area < min_area_multi or n_points <= 1:
        return [(cy, cx)]

    points = [(cy, cx)]
    # Candidate offsets around the center (25% to 35% radius)
    dx_offset = max(4, int(w * 0.28))
    dy_offset = max(4, int(h * 0.28))

    candidates = [
        (cy - dy_offset, cx),
        (cy + dy_offset, cx),
        (cy, cx - dx_offset),
        (cy, cx + dx_offset),
        (cy - dy_offset, cx - dx_offset),
        (cy + dy_offset, cx + dx_offset),
    ]

    pts_np = np.array(polygon, dtype=np.int32) if (polygon and len(polygon) >= 3) else None

    for r_cand, c_cand in candidates:
        if len(points) >= n_points:
            break
        # Boundary check
        if not (y <= r_cand <= y + h and x <= c_cand <= x + w):
            continue

        if pts_np is not None:
            # Check if point is strictly inside the polygon
            dist = cv2.pointPolygonTest(pts_np, (float(c_cand), float(r_cand)), False)
            if dist >= 0:
                points.append((r_cand, c_cand))
        else:
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
