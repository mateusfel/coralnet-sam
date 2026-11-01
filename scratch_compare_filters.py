import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Directories
WORKSPACE_DIR = r"D:\coralnet-sam"
IMAGE_PATH = os.path.join(WORKSPACE_DIR, "images", "2.0_P5112611.JPG")
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "output")
ARTIFACT_DIR = r"C:\Users\mateu\.gemini\antigravity\brain\c6b88eab-5681-491f-af9f-f7f5edc1edd9"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

print(f"[*] Carregando imagem de teste: {IMAGE_PATH}")
bgr = cv2.imread(IMAGE_PATH)
h, w, _ = bgr.shape

# 1. CLAHE in LAB Color Space (Preserves color hue, enhances local texture)
def apply_clahe(img_bgr, clip_limit=2.5, grid_size=(8, 8)):
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
    cl = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)

# 2. Underwater White Balance (Percentile-based dynamic range stretching per channel)
def apply_white_balance(img_bgr, p_low=1.0, p_high=99.0):
    res = np.zeros_like(img_bgr, dtype=np.float32)
    for c in range(3):
        ch = img_bgr[:, :, c].astype(np.float32)
        v_min = np.percentile(ch, p_low)
        v_max = np.percentile(ch, p_high)
        res[:, :, c] = np.clip((ch - v_min) / (v_max - v_min + 1e-5) * 255.0, 0, 255)
    return res.astype(np.uint8)

# 3. Combined Pipeline (White Balance + CLAHE)
def apply_combined(img_bgr):
    wb = apply_white_balance(img_bgr, p_low=1.0, p_high=99.0)
    return apply_clahe(wb, clip_limit=2.0, grid_size=(8, 8))

print("[*] Processando filtros em alta resolucao (4000x3000)...")
img_orig = bgr
img_clahe = apply_clahe(bgr, clip_limit=2.5)
img_wb = apply_white_balance(bgr)
img_comb = apply_combined(bgr)

# Save resized overview (1200x900) for full transect visual comparison
def make_overview_grid():
    target_w, target_h = 1000, 750
    down_orig = cv2.resize(img_orig, (target_w, target_h))
    down_clahe = cv2.resize(img_clahe, (target_w, target_h))
    down_wb = cv2.resize(img_wb, (target_w, target_h))
    down_comb = cv2.resize(img_comb, (target_w, target_h))

    def add_label(img, text):
        out = img.copy()
        cv2.rectangle(out, (0, 0), (target_w, 42), (20, 20, 20), -1)
        cv2.putText(out, text, (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        return out

    top = np.hstack([add_label(down_orig, "1. ORIGINAL (In-situ / Turva)"), 
                     add_label(down_clahe, "2. CLAHE (Realce de Textura / LAB)")])
    bottom = np.hstack([add_label(down_wb, "3. BALANCO DE BRANCO (Compensacao Cromatica)"), 
                        add_label(down_comb, "4. COMBINADO (Balanco + CLAHE)")])
    grid = np.vstack([top, bottom])
    
    macro_path = os.path.join(OUTPUT_DIR, "transect_filters_macro_comparison.jpg")
    cv2.imwrite(macro_path, grid, [cv2.IMWRITE_JPEG_QUALITY, 92])
    cv2.imwrite(os.path.join(ARTIFACT_DIR, "transect_filters_macro_comparison.jpg"), grid, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"[+] Visao macro salva: {macro_path}")

make_overview_grid()

# 4. Extract 224x224 Patches from Key Benthic Colonies
# Centers: (cy, cx, label)
PATCH_LOCATIONS = [
    (1074, 2640, "Agaricia (Coral Folhoso)"),
    (1214, 3730, "Porites (Coral Massivo)"),
    (1613, 3750, "Substrato / Macroalga")
]

patch_size = 224
half = patch_size // 2

def extract_patch(source_img, cy, cx):
    y1, y2 = max(0, cy - half), min(h, cy + half)
    x1, x2 = max(0, cx - half), min(w, cx + half)
    # Ensure exact 224x224
    if y2 - y1 < patch_size: y2 = y1 + patch_size
    if x2 - x1 < patch_size: x2 = x1 + patch_size
    return source_img[y1:y2, x1:x2]

# Build side-by-side patch comparison matrix
# Rows = Patches, Cols = Original, CLAHE, White Balance, Combined
# Magnified by 2x (448x448) for easy inspection
display_size = 350
rows = []

for cy, cx, colony_name in PATCH_LOCATIONS:
    p_orig = cv2.resize(extract_patch(img_orig, cy, cx), (display_size, display_size), interpolation=cv2.INTER_NEAREST)
    p_clahe = cv2.resize(extract_patch(img_clahe, cy, cx), (display_size, display_size), interpolation=cv2.INTER_NEAREST)
    p_wb = cv2.resize(extract_patch(img_wb, cy, cx), (display_size, display_size), interpolation=cv2.INTER_NEAREST)
    p_comb = cv2.resize(extract_patch(img_comb, cy, cx), (display_size, display_size), interpolation=cv2.INTER_NEAREST)

    # Put labels on each
    def tag_patch(img, title, subtitle):
        out = img.copy()
        cv2.rectangle(out, (0, 0), (display_size, 38), (15, 23, 42), -1)
        cv2.rectangle(out, (0, display_size - 32), (display_size, display_size), (15, 23, 42), -1)
        cv2.putText(out, title, (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (56, 189, 248), 2, cv2.LINE_AA)
        cv2.putText(out, subtitle, (10, display_size - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (226, 232, 240), 1, cv2.LINE_AA)
        # Add subtle 1px border
        cv2.rectangle(out, (0, 0), (display_size - 1, display_size - 1), (100, 116, 139), 1)
        return out

    row = np.hstack([
        tag_patch(p_orig, "ORIGINAL", colony_name),
        tag_patch(p_clahe, "+ CLAHE (LAB)", "Realce de Valas/Clices"),
        tag_patch(p_wb, "+ BALANCO DE BRANCO", "Remocao do Tom Azul/Verde"),
        tag_patch(p_comb, "+ COMBINADO", "Balanco + CLAHE")
    ])
    rows.append(row)

patch_grid = np.vstack(rows)
patches_path = os.path.join(OUTPUT_DIR, "patches_224_comparison.jpg")
cv2.imwrite(patches_path, patch_grid, [cv2.IMWRITE_JPEG_QUALITY, 94])
cv2.imwrite(os.path.join(ARTIFACT_DIR, "patches_224_comparison.jpg"), patch_grid, [cv2.IMWRITE_JPEG_QUALITY, 94])
print(f"[+] Comparacao de patches 224x224 salva: {patches_path}")

print("[*] Processamento concluido com sucesso!")
