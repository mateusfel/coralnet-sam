import os
import io
import json
import time
import cv2
import numpy as np
import requests
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image

from src.geometry import generate_approx_polygon
from src.coral_classifier import pack_colonies_spritesheet


class RemoteSAMClient:
    """
    Client that communicates with the Google Colab CoralSCOP + BioCLIP 2.5 ReefNet GPU microservice.
    1. /segment: Sends underwater-enhanced / quadrat-cropped survey photo to CoralSCOP ViT-B.
    2. /classify_bioclip: Sends full-resolution multi-scale (Macro + Micro) 224x224 colony sprite-sheet
       to BioCLIP 2.5 ViT-H/14 ReefNet on the same Colab GPU, returning genus similarities and 1024-D signatures.
    """

    def __init__(self, colab_url: str = None, timeout: int = 300, max_dimension: int = 1024):
        self.colab_url = colab_url.rstrip("/") if colab_url else None
        self.timeout = timeout
        self.max_dimension = max_dimension

    def _headers(self) -> Dict[str, str]:
        return {
            "ngrok-skip-browser-warning": "true",
            "Bypass-Tunnel-Reminder": "true",
            "User-Agent": "CoralSCOP-BioCLIP25-Client/3.0"
        }

    def is_connected(self) -> bool:
        if not self.colab_url:
            return False
        try:
            resp = requests.get(f"{self.colab_url}/health", headers=self._headers(), timeout=8)
            return resp.status_code == 200
        except Exception:
            return False

    def segment_image(
        self,
        image_path: str,
        min_area: int = 1500,
        pred_iou_thresh: float = 0.72,
        points_per_side: int = 32,
        stability_score_thresh: float = 0.62,
        crop_n_layers: int = 1,
        crop_n_points_downscale_factor: int = 2,
        pil_image: Optional[Image.Image] = None,
        offset_x: int = 0,
        offset_y: int = 0,
        full_image_size: Optional[Tuple[int, int]] = None,
        bridge_strings: bool = True
    ) -> Dict[str, Any]:
        """
        Sends an image (or prepared quadrat ROI PIL.Image) to the remote CoralSCOP / SAM server
        on Google Colab. Scales min_area proportionally to the transmitted resolution so lobes
        bisected by quadrat strings are never prematurely erased, and reprojects all detections
        back to full original photo coordinates via (offset_x, offset_y).
        """
        if not self.colab_url:
            raise ValueError(
                "Nenhuma URL do Colab informada. Abra o notebook 'colab/sam_server_colab.ipynb' "
                "no Google Colab, inicie o servidor CoralSCOP + BioCLIP 2.5 e passe a URL gerada pelo ngrok."
            )

        endpoint = f"{self.colab_url}/segment"

        if pil_image is not None:
            work_img = pil_image.convert("RGB")
        else:
            with Image.open(image_path) as disk_img:
                work_img = disk_img.convert("RGB")

        src_w, src_h = work_img.size
        full_w, full_h = full_image_size if full_image_size else (src_w + offset_x, src_h + offset_y)

        needs_downscale = max(src_w, src_h) > self.max_dimension
        if needs_downscale:
            send_img = work_img.copy()
            send_img.thumbnail((self.max_dimension, self.max_dimension), Image.Resampling.LANCZOS)
        else:
            send_img = work_img

        send_w, send_h = send_img.size
        area_downscale_factor = (send_w * send_h) / float(max(1, src_w * src_h))
        # Scale min_area down proportionally (with 0.45 margin for colonies split by nylon strings)
        remote_min_area = max(25, int(min_area * area_downscale_factor * 0.45))

        params = {
            "min_area": remote_min_area,
            "pred_iou_thresh": pred_iou_thresh,
            "points_per_side": points_per_side,
            "stability_score_thresh": stability_score_thresh,
            "crop_n_layers": crop_n_layers,
            "crop_n_points_downscale_factor": crop_n_points_downscale_factor,
            "bridge_strings": str(bridge_strings).lower()
        }

        print(
            f"[*] Enviando região ({src_w}x{src_h} -> {send_w}x{send_h}px) ao Colab: {endpoint} "
            f"(min_area_orig={min_area}px -> min_area_gpu={remote_min_area}px, "
            f"pts/side={points_per_side}, pred_iou={pred_iou_thresh}, stability={stability_score_thresh})..."
        )

        buf = io.BytesIO()
        send_img.save(buf, format="JPEG", quality=95)
        buf.seek(0)

        files = {"file": (os.path.basename(image_path), buf, "image/jpeg")}

        t0 = time.time()
        try:
            response = requests.post(
                endpoint, files=files, params=params, headers=self._headers(), timeout=self.timeout
            )
        except requests.exceptions.ConnectionError as ce:
            raise ConnectionError(
                f"Conexão perdida com o Colab ({self.colab_url}). O túnel foi encerrado pelo servidor remoto. "
                f"Verifique se a Célula 6 do Colab ainda está ativa ou use NGROK_AUTHTOKEN."
            ) from ce
        except requests.exceptions.Timeout as te:
            raise TimeoutError(
                f"Tempo limite excedido ({self.timeout}s) aguardando o servidor no Colab."
            ) from te

        elapsed = round(time.time() - t0, 1)
        if response.status_code in (502, 504):
            is_lt = "loca.lt" in (self.colab_url or "")
            tunnel_tip = (
                "Você está conectado via Localtunnel (.loca.lt), que corta requisições acima de ~90–120s (como Grade 64x64). "
                "No Colab, clique no ícone de Chave 🔑 (Secrets) à esquerda, ative o acesso ao 'NGROK_AUTHTOKEN' para este notebook "
                "e rode apenas a Célula 6 novamente (ou reduza a Grade de Sondagem para 32)."
                if is_lt else
                "O proxy do túnel encerrou a conexão por tempo limite. Tente reduzir a Grade de Sondagem de 64 para 32 ou reexecute a Célula 6 no Colab."
            )
            raise RuntimeError(f"Tempo limite do túnel ({response.status_code} Bad Gateway após {elapsed}s). {tunnel_tip}")
        if response.status_code != 200:
            raise RuntimeError(f"Erro retornado pelo Colab ({response.status_code}): {response.text[:300]}")

        data = response.json()
        engine_name = data.get("model", "CoralSCOP / SAM")
        total = data.get("total_masks", 0)
        print(f"[OK] {engine_name} respondeu em {elapsed}s com {total} máscaras candidatas!")

        # Rescale masks from transmitted GPU dimensions back to src_img, then add (offset_x, offset_y)
        sent_w = data.get("image_width", send_w)
        sent_h = data.get("image_height", send_h)
        sx = src_w / float(sent_w) if sent_w else 1.0
        sy = src_h / float(sent_h) if sent_h else 1.0

        filtered_masks = []
        for m in data.get("masks", []):
            bx, by, bw, bh = m["bbox"]
            m["bbox"] = [
                int(round(bx * sx)) + offset_x,
                int(round(by * sy)) + offset_y,
                max(1, int(round(bw * sx))),
                max(1, int(round(bh * sy)))
            ]
            cy, cx = m["centroid"]
            m["centroid"] = [
                int(round(cy * sy)) + offset_y,
                int(round(cx * sx)) + offset_x
            ]
            m["area"] = int(round(m["area"] * (sx * sy)))

            # Discard micro-fragments below user's original-scale min_area
            if m["area"] < min_area:
                continue

            # Extract & scale all contour polygons, sorted by contour area descending
            raw_polys = m.get("polygons") or ([] if not m.get("polygon") else [m["polygon"]])
            scaled_polys = []
            for poly in raw_polys:
                if poly and len(poly) >= 3:
                    sp = [
                        [int(round(pt[0] * sx)) + offset_x, int(round(pt[1] * sy)) + offset_y]
                        for pt in poly
                    ]
                    scaled_polys.append(sp)

            if scaled_polys:
                scaled_polys.sort(
                    key=lambda p: float(cv2.contourArea(np.array(p, dtype=np.int32))),
                    reverse=True
                )
                m["polygons"] = scaled_polys
                m["polygon"] = scaled_polys[0]
            else:
                approx_p = generate_approx_polygon(m["bbox"])
                m["polygons"] = [approx_p]
                m["polygon"] = approx_p

            filtered_masks.append(m)

        data["masks"] = filtered_masks
        data["total_masks"] = len(filtered_masks)
        data["image_width"] = full_w
        data["image_height"] = full_h
        data["elapsed_gpu_sec"] = elapsed

        return data

    def classify_colonies_bioclip(
        self,
        enhanced_image: Image.Image,
        masks: List[Dict[str, Any]],
        colony_points_list: List[List[Tuple[int, int]]]
    ) -> Optional[Dict[str, Any]]:
        """
        Packs full-resolution (4000x3000) Multi-Scale Macro + Micro 224x224 crops for all
        NMS-filtered colonies into a compact JPEG sprite-sheet and sends a single batch request
        to BioCLIP 2.5 ViT-H/14 ReefNet on the Colab GPU (/classify_bioclip).
        Returns None if /classify_bioclip is unavailable (e.g., outdated Colab session).
        """
        if not self.colab_url or not masks:
            return None

        endpoint = f"{self.colab_url}/classify_bioclip"
        sheet_img, metadata = pack_colonies_spritesheet(
            pil_image=enhanced_image,
            masks=masks,
            colony_points_list=colony_points_list,
            tile_size=224,
            grid_cols=10
        )

        buf = io.BytesIO()
        sheet_img.save(buf, format="JPEG", quality=94)
        payload_kb = round(buf.tell() / 1024.0, 1)
        buf.seek(0)

        print(
            f"[*] Enviando {metadata['total_tiles']} recortes Multi-Escala 224x224 ({len(masks)} colônias, "
            f"{payload_kb} KB) ao BioCLIP 2.5 ReefNet no Colab: {endpoint}..."
        )

        files = {"file": ("colonies_spritesheet.jpg", buf, "image/jpeg")}
        form_data = {"metadata_json": json.dumps(metadata)}

        t0 = time.time()
        try:
            resp = requests.post(
                endpoint, files=files, data=form_data, headers=self._headers(), timeout=self.timeout
            )
        except Exception as e:
            print(f"[!] Aviso ao contatar /classify_bioclip no Colab ({e}). Usando fallback local.")
            return None

        elapsed = round(time.time() - t0, 2)
        if resp.status_code == 404:
            print("[!] Servidor Colab atual ainda não possui a rota /classify_bioclip (atualize o notebook no Colab).")
            return None
        if resp.status_code != 200:
            raise RuntimeError(f"Erro no BioCLIP 2.5 do Colab ({resp.status_code}): {resp.text[:300]}")

        res_data = resp.json()
        res_data["elapsed_bioclip_sec"] = elapsed
        print(
            f"[OK] {res_data.get('classifier_model', 'BioCLIP 2.5 ReefNet')} classificou "
            f"{len(res_data.get('results', []))} colônias em {elapsed}s!"
        )
        return res_data
