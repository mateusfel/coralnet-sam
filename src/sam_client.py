import os
import requests
from typing import Dict, Any, List
from PIL import Image


class RemoteSAMClient:
    """
    Client that communicates with the Google Colab SAM ViT-H microservice.
    Sends high-resolution coral reef survey photos and receives
    fully-automated class-agnostic colony masks.
    """

    def __init__(self, colab_url: str = None, timeout: int = 120):
        self.colab_url = colab_url.rstrip("/") if colab_url else None
        self.timeout = timeout

    def is_connected(self) -> bool:
        if not self.colab_url:
            return False
        try:
            resp = requests.get(f"{self.colab_url}/health", timeout=8)
            return resp.status_code == 200
        except Exception:
            return False

    def segment_image(self, image_path: str) -> Dict[str, Any]:
        """
        Sends an image file to the remote SAM ViT-H server on Google Colab.
        """
        if not self.colab_url:
            raise ValueError(
                "Nenhuma URL do Colab informada. Abra o notebook 'colab/sam_server_colab.ipynb' "
                "no Google Colab, inicie o servidor e passe a URL gerada pelo ngrok."
            )

        endpoint = f"{self.colab_url}/segment"
        print(f"[*] Enviando imagem para o SAM ViT-H no Google Colab: {endpoint}...")

        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, "image/jpeg")}
            response = requests.post(endpoint, files=files, timeout=self.timeout)

        if response.status_code != 200:
            raise RuntimeError(f"Erro retornado pelo Colab ({response.status_code}): {response.text}")

        data = response.json()
        print(f"[OK] SAM ViT-H detectou com sucesso {data.get('total_masks', 0)} colônias/objetos!")
        return data
