from __future__ import annotations

import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ml_pipeline.training import build_training_artifacts


if __name__ == "__main__":
    artifacts = build_training_artifacts(output_root=Path(__file__).resolve().parents[2])
    print(json.dumps(artifacts, indent=2))
