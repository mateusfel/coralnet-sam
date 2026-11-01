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
    def classify_colonies_multipoint(
        self,
        image: Image.Image,
        colony_points_list: List[List[Tuple[int, int]]]
    ) -> List[Dict[str, Any]]:
        """
        Classifies colonies using Multi-Point Voting (Fase 2).
        For each colony, extracts patches from multiple interior points,
        computes consensus voting and averages probability distributions.
        """
        results = []
        if not colony_points_list:
            return results

        # Flatten all points while tracking colony boundaries
        all_points = []
        colony_slices = []
        for pts in colony_points_list:
            start = len(all_points)
            all_points.extend(pts)
            end = len(all_points)
            colony_slices.append((start, end))

        # Batch feature extraction through EfficientNet-B0
        all_probs = []
        batch_size = 16

        for i in range(0, len(all_points), batch_size):
            batch_pts = all_points[i:i + batch_size]
            tensors = [self.preprocess(self.extract_patch(image, r, c)) for r, c in batch_pts]
            batch_tensor = torch.stack(tensors).to(self.device)

            features = self.backbone(batch_tensor)
            logits = self.head(features)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
            all_probs.append(probs)

        all_probs = np.vstack(all_probs) if all_probs else np.empty((0, len(self.classes)))

        # Aggregate multi-point predictions per colony
        for start, end in colony_slices:
            col_probs = all_probs[start:end]
            mean_probs = np.mean(col_probs, axis=0)
            votes = [np.argmax(p) for p in col_probs]

            # Consensus ratio (how many sample points agreed with the majority)
            top_idx = int(np.argmax(mean_probs))
            consensus_votes = sum(1 for v in votes if v == top_idx)
            consensus_ratio = float(consensus_votes / len(votes)) if votes else 1.0

            sorted_indices = np.argsort(mean_probs)[::-1]
            top_genus = self.classes[top_idx]

            results.append({
                "genus": top_genus,
                "confidence": float(mean_probs[top_idx]),
                "color": CLASS_COLORS.get(top_genus, "#38bdf8"),
                "sample_points_count": len(votes),
                "consensus_ratio": consensus_ratio,
                "alternatives": [
                    {"genus": self.classes[idx], "confidence": float(mean_probs[idx])}
                    for idx in sorted_indices[1:3]
                ]
            })

        return results

    @torch.no_grad()
    def classify_centroids(self, image: Image.Image, centroids: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """
        Backward compatible classification for single centroids.
        """
        return self.classify_colonies_multipoint(image, [[pt] for pt in centroids])

