import os
from typing import List, Dict, Any, Tuple
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np

# 11 Brazilian / South Atlantic Coral Genera + Key Substrates
TARGET_CLASSES = [
    "Montastraea",
    "Mussismilia",
    "Porites",
    "Siderastrea",
    "Agaricia",
    "Millepora",
    "Madracis",
    "Meandrina",
    "Stephanocoenia",
    "Scolymia",
    "Favia",
    "Algae (Macroalgae / Turf / CCA)",
    "Hard Substrate (Rock / Pavement)",
    "Soft Substrate (Sand / Rubble)",
    "Other Invertebrates (Sponges / Soft Coral)"
]

CLASS_COLORS = {
    "Montastraea": "#e6194b",
    "Mussismilia": "#3cb44b",
    "Porites": "#ffe119",
    "Siderastrea": "#4363d8",
    "Agaricia": "#f58231",
    "Millepora": "#911eb4",
    "Madracis": "#42d4f4",
    "Meandrina": "#f032e6",
    "Stephanocoenia": "#bfef45",
    "Scolymia": "#fabed4",
    "Favia": "#469990",
    "Algae (Macroalgae / Turf / CCA)": "#9a6324",
    "Hard Substrate (Rock / Pavement)": "#808080",
    "Soft Substrate (Sand / Rubble)": "#fffac8",
    "Other Invertebrates (Sponges / Soft Coral)": "#aaffc3"
}


class CoralNetClassifierHead(nn.Module):
    def __init__(self, in_features: int = 1280, num_classes: int = len(TARGET_CLASSES)):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class LocalCoralClassifier:
    """
    Local Classifier using CoralNet EfficientNet-B0 weights stored in models/
    to classify colonies discovered by the remote SAM.
    """

    def __init__(self, weights_path: str = None, patch_size: int = 224, device: str = None):
        self.patch_size = patch_size
        self.classes = TARGET_CLASSES
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        # 1. Load Backbone from local copied weights
        if weights_path is None:
            default_weights = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "models", "efficientnet_b0_ver1.pth"
            )
            weights_path = default_weights if os.path.exists(default_weights) else None

        print(f"[*] Inicializando Classificador CoralNet no dispositivo: {self.device}")
        self.backbone = models.efficientnet_b0(weights=None)
        
        if weights_path and os.path.exists(weights_path):
            print(f"[*] Carregando pesos do CoralNet local de: {weights_path}")
            state_dict = torch.load(weights_path, map_location="cpu")
            self.backbone.load_state_dict(state_dict, strict=False)
        else:
            print("[*] Pesos locais não encontrados. Carregando padrão do hub...")
            self.backbone = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)

        self.backbone.classifier = nn.Identity()
        self.backbone.eval()
        self.backbone.to(self.device)

        # 2. Classification Head
        self.head = CoralNetClassifierHead(in_features=1280, num_classes=len(self.classes))
        self.head.eval()
        self.head.to(self.device)

        self.preprocess = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def extract_patch(self, image: Image.Image, row: int, col: int) -> Image.Image:
        w, h = image.size
        half = self.patch_size // 2
        left, top = max(0, col - half), max(0, row - half)
        right, bottom = min(w, left + self.patch_size), min(h, top + self.patch_size)
        return image.crop((left, top, right, bottom))

    @torch.no_grad()
    def classify_centroids(self, image: Image.Image, centroids: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """
        Classifies each colony centroid using EfficientNet-B0 embeddings.
        """
        results = []
        batch_size = 16

        for i in range(0, len(centroids), batch_size):
            batch_pts = centroids[i:i + batch_size]
            tensors = [self.preprocess(self.extract_patch(image, r, c)) for r, c in batch_pts]
            batch_tensor = torch.stack(tensors).to(self.device)

            features = self.backbone(batch_tensor)
            logits = self.head(features)
            probs = torch.softmax(logits, dim=1).cpu().numpy()

            for p in probs:
                top_indices = np.argsort(p)[::-1][:3]
                results.append({
                    "genus": self.classes[top_indices[0]],
                    "confidence": float(p[top_indices[0]]),
                    "color": CLASS_COLORS.get(self.classes[top_indices[0]], "#38bdf8"),
                    "alternatives": [
                        {"genus": self.classes[idx], "confidence": float(p[idx])}
                        for idx in top_indices[1:]
                    ]
                })

        return results
