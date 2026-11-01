import os
import io
import requests
from typing import Dict, Any, List
from PIL import Image

from src.geometry import generate_approx_polygon


class RemoteSAMClient:
    """
    Client that communicates with the Google Colab SAM ViT-H microservice.
    Sends high-resolution coral reef survey photos and receives
    fully-automated class-agnostic colony masks.
    """

    def __init__(self, colab_url: str = None, timeout: int = 300, max_dimension: int = 1536):
        self.colab_url = colab_url.rstrip("/") if colab_url else None
        self.timeout = timeout
        self.max_dimension = max_dimension

    def is_connected(self) -> bool:
        if not self.colab_url:
            return False
        try:
            resp = requests.get(f"{self.colab_url}/health", timeout=8)
            return resp.status_code == 200
        except Exception:
            return False

    def segment_image(
        self,
        image_path: str,
        min_area: int = 300,
        pred_iou_thresh: float = 0.86
    ) -> Dict[str, Any]:
        """
        Sends an image file to the remote SAM ViT-H server on Google Colab.
        Allows configuring minimum polygon area and IoU threshold remotely.
        Resizes temporarily if larger than max_dimension to avoid GPU VRAM OOM,
        and rescales returned detections back to original photo dimensions.
        """
        if not self.colab_url:
            raise ValueError(
                "Nenhuma URL do Colab informada. Abra o notebook 'colab/sam_server_colab.ipynb' "
                "no Google Colab, inicie o servidor e passe a URL gerada pelo ngrok."
            )

        endpoint = f"{self.colab_url}/segment"
        params = {"min_area": min_area, "pred_iou_thresh": pred_iou_thresh}
        print(f"[*] Enviando imagem para o SAM ViT-H no Google Colab: {endpoint} (min_area={min_area} px)...")

        # Open and check dimensions
        with Image.open(image_path) as orig_img:
            orig_w, orig_h = orig_img.size
            needs_downscale = max(orig_w, orig_h) > self.max_dimension

            if needs_downscale:
                print(f"[*] Otimizando resolução para envio ao SAM ({orig_w}x{orig_h} -> máx {self.max_dimension}px) para segurança de VRAM...")
                resized_img = orig_img.copy().convert("RGB")
                resized_img.thumbnail((self.max_dimension, self.max_dimension), Image.Resampling.LANCZOS)
                
                buf = io.BytesIO()
                resized_img.save(buf, format="JPEG", quality=95)
                buf.seek(0)
                files = {"file": (os.path.basename(image_path), buf, "image/jpeg")}
                response = requests.post(endpoint, files=files, params=params, timeout=self.timeout)
            else:
                with open(image_path, "rb") as f:
                    files = {"file": (os.path.basename(image_path), f, "image/jpeg")}
                    response = requests.post(endpoint, files=files, params=params, timeout=self.timeout)

        if response.status_code != 200:
            raise RuntimeError(f"Erro retornado pelo Colab ({response.status_code}): {response.text}")

        data = response.json()
        total = data.get("total_masks", 0)
        print(f"[OK] SAM ViT-H detectou com sucesso {total} colônias/objetos!")

        # Rescale masks back to original image coordinate space
        sent_w = data.get("image_width", orig_w)
        sent_h = data.get("image_height", orig_h)
        sx = orig_w / float(sent_w) if sent_w else 1.0
        sy = orig_h / float(sent_h) if sent_h else 1.0

        filtered_masks = []
        for m in data.get("masks", []):
            bx, by, bw, bh = m["bbox"]
            m["bbox"] = [int(bx * sx), int(by * sy), int(bw * sx), int(bh * sy)]
            cy, cx = m["centroid"]
            m["centroid"] = [int(cy * sy), int(cx * sx)]
            m["area"] = int(m["area"] * (sx * sy))

            # Discard micro-fragments below min_area
            if m["area"] < min_area:
                continue

            # Scale existing polygon or generate organic contour
            if "polygon" in m and m["polygon"]:
                m["polygon"] = [[int(pt[0] * sx), int(pt[1] * sy)] for pt in m["polygon"]]
            elif "polygons" in m and m["polygons"]:
                scaled_polys = []
                for poly in m["polygons"]:
                    scaled_polys.append([[int(pt[0] * sx), int(pt[1] * sy)] for pt in poly])
                m["polygon"] = scaled_polys[0] if scaled_polys else generate_approx_polygon(m["bbox"])
                m["polygons"] = scaled_polys
            else:
                m["polygon"] = generate_approx_polygon(m["bbox"])

            filtered_masks.append(m)

        data["masks"] = filtered_masks
        data["total_masks"] = len(filtered_masks)
        data["image_width"] = orig_w
        data["image_height"] = orig_h

        return data

