import os
import argparse
from src.pipeline import run_hybrid_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline Automatizado: Meta SAM ViT-H (Colab) + CoralNet (Local)"
    )
    parser.add_argument(
        "--image", type=str, default=None,
        help="Caminho da foto do transecto (ou nome do arquivo na pasta images/)"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Processar todas as imagens presentes na pasta images/"
    )
    parser.add_argument(
        "--sam-url", type=str, default=None,
        help="URL pública do Google Colab gerada pelo ngrok (ex: https://xxxx.ngrok-free.app)"
    )
    parser.add_argument(
        "--output", type=str, default="output",
        help="Diretório de saída para os mapas semânticos gerados"
    )
    parser.add_argument(
        "--iou-thresh", type=float, default=0.60,
        help="Limiar IoU para supressão de máscaras sobrepostas (Fase 2 NMS)"
    )
    parser.add_argument(
        "--containment-thresh", type=float, default=0.80,
        help="Limiar de contenção para eliminar fragmentos dentro de colônias maiores"
    )
    parser.add_argument(
        "--n-points", type=int, default=5,
        help="Número de pontos interiores para votação por consenso em colônias grandes"
    )

    args = parser.parse_args()

    # Determine images
    images_dir = "images"
    valid_exts = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")

    if args.all or args.image is None:
        found = [
            os.path.join(images_dir, f) for f in os.listdir(images_dir)
            if f.lower().endswith(valid_exts)
        ]
        if not found:
            print("[!] Nenhuma imagem encontrada na pasta images/.")
            return

        if args.image is None and not args.all:
            images_to_process = [found[0]]
            print(f"[*] Nenhuma imagem especificada. Executando na primeira foto de teste: {found[0]}")
            print("    (Para rodar em todas, use a flag --all)")
        else:
            images_to_process = found
    else:
        if os.path.exists(args.image):
            images_to_process = [args.image]
        elif os.path.exists(os.path.join(images_dir, args.image)):
            images_to_process = [os.path.join(images_dir, args.image)]
        else:
            print(f"[!] Imagem não encontrada: {args.image}")
            return

    for img_path in images_to_process:
        run_hybrid_pipeline(
            image_path=img_path,
            colab_url=args.sam_url,
            output_dir=args.output,
            iou_thresh=args.iou_thresh,
            containment_thresh=args.containment_thresh,
            n_points_multi=args.n_points
        )

    print("\n[OK] Pipeline concluído com sucesso!")


if __name__ == "__main__":
    main()
