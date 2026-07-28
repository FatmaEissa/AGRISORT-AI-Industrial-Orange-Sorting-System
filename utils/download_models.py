from pathlib import Path
from huggingface_hub import hf_hub_download

REPO_ID = "FatmaEissa1/AgriSort-orange-classifier"

BASE_DIR = Path(__file__).resolve().parent.parent

CLASSIFICATION_PATH = BASE_DIR / "models" / "classification" / "best_orange_model.pth"
DETECTION_PATH = BASE_DIR / "models" / "detection" / "best.pt"


def download_models():
    CLASSIFICATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    DETECTION_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not CLASSIFICATION_PATH.exists():
        path = hf_hub_download(
            repo_id=REPO_ID,
            filename="best_orange_model.pth",
        )
        CLASSIFICATION_PATH.write_bytes(Path(path).read_bytes())

    if not DETECTION_PATH.exists():
        path = hf_hub_download(
            repo_id=REPO_ID,
            filename="best.pt",
        )
        DETECTION_PATH.write_bytes(Path(path).read_bytes())

    return str(CLASSIFICATION_PATH), str(DETECTION_PATH)