"""
src/export_utils.py
-------------------
Utilitários de exportação do Offshore Intelligence System (OIS).

Uso:
    python src/export_utils.py --notebook notebooks/OIS_Project.ipynb

Extrai imagens PNG embutidas no notebook Jupyter e as salva em images/.
"""

import json
import base64
import argparse
import os
from pathlib import Path


def extract_images_from_notebook(notebook_path: str, output_dir: str = "images") -> None:
    """Extrai todas as imagens PNG de outputs de um notebook Jupyter.

    Args:
        notebook_path: Caminho para o arquivo .ipynb.
        output_dir: Pasta onde as imagens serão salvas (criada se não existir).
    """
    notebook_path = Path(notebook_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not notebook_path.exists():
        raise FileNotFoundError(f"Notebook não encontrado: {notebook_path}")

    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    img_idx = 1
    for cell in nb.get("cells", []):
        for output in cell.get("outputs", []):
            if "data" in output and "image/png" in output["data"]:
                img_data = output["data"]["image/png"]
                img_name = output_dir / f"grafico_{img_idx:02d}.png"
                with open(img_name, "wb") as img_f:
                    img_f.write(base64.b64decode(img_data))
                print(f"✅  Imagem salva: {img_name}")
                img_idx += 1

    print(f"\n🎉  Total de imagens extraídas: {img_idx - 1}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrai imagens de um notebook Jupyter.")
    parser.add_argument(
        "--notebook",
        default="notebooks/OIS_Project.ipynb",
        help="Caminho para o notebook .ipynb (default: notebooks/OIS_Project.ipynb)",
    )
    parser.add_argument(
        "--output",
        default="images",
        help="Pasta de saída para as imagens (default: images/)",
    )
    args = parser.parse_args()
    extract_images_from_notebook(args.notebook, args.output)
