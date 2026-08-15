#!/usr/bin/env python3
"""Télécharge les modèles locaux (PII OpenMed, Whisper) sur la machine hôte.

À exécuter UNE SEULE FOIS, sur une machine avec accès réseau, AVANT le déploiement.
Le conteneur applicatif tourne ensuite strictement hors ligne (HF_HUB_OFFLINE=1).

Exemple :
    python scripts/download_models.py --out deploy/models
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_PII_REPO = "OpenMed/OpenMed-NER-PathologyDetect-PubMed-v2-109M"
DEFAULT_WHISPER_REPO = "Systran/faster-whisper-small"


def download(repo_id: str, destination: Path) -> None:
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        sys.exit("Installez d'abord : pip install huggingface_hub")

    destination.mkdir(parents=True, exist_ok=True)
    print(f"→ Téléchargement de {repo_id} vers {destination}")
    snapshot_download(repo_id=repo_id, local_dir=str(destination), local_dir_use_symlinks=False)
    print(f"✓ Terminé : {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="deploy/models", help="Répertoire de sortie des modèles")
    parser.add_argument("--pii-repo", default=DEFAULT_PII_REPO)
    parser.add_argument("--whisper-repo", default=DEFAULT_WHISPER_REPO)
    parser.add_argument("--skip-pii", action="store_true")
    parser.add_argument("--skip-whisper", action="store_true")
    args = parser.parse_args()

    out = Path(args.out).resolve()

    if not args.skip_pii:
        download(args.pii_repo, out / "openmed-pii")
    if not args.skip_whisper:
        download(args.whisper_repo, out / "faster-whisper-small")

    print(
        "\nDéfinissez ensuite dans backend/.env :\n"
        "  OPENMED_PII_MODEL=/models/openmed-pii\n"
        "  WHISPER_MODEL_PATH=/models/faster-whisper-small"
    )


if __name__ == "__main__":
    main()