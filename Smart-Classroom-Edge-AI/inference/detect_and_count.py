"""Run classroom detection and report per-frame student/cleaner counts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "model" / "best.pt"


def parse_source(value: str) -> str | int:
    """Convert a numeric source to a webcam index; leave paths/URLs unchanged."""
    return int(value) if value.isdigit() else value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect people and cleaners in classroom images, videos, or streams."
    )
    parser.add_argument(
        "source",
        help="Image/video path, stream URL, directory, glob, or webcam index (for example 0).",
    )
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL, help="YOLO weights path.")
    parser.add_argument("--conf", type=float, default=0.35, help="Confidence threshold (0-1).")
    parser.add_argument("--iou", type=float, default=0.45, help="NMS IoU threshold (0-1).")
    parser.add_argument("--device", default=None, help="Device such as cpu, 0, or 0,1.")
    parser.add_argument("--show", action="store_true", help="Display annotated frames.")
    parser.add_argument("--save", action="store_true", help="Save annotated output.")
    parser.add_argument("--project", type=Path, default=ROOT / "runs", help="Output directory.")
    parser.add_argument("--name", default="classroom", help="Output run name.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print one JSON object per result instead of readable text.",
    )
    return parser


def class_counts(result: Any, names: dict[int, str]) -> dict[str, int]:
    counts = {name: 0 for name in names.values()}
    if result.boxes is None:
        return counts

    for class_id in result.boxes.cls.tolist():
        name = names.get(int(class_id), f"class_{int(class_id)}")
        counts[name] = counts.get(name, 0) + 1
    return counts


def main() -> None:
    args = build_parser().parse_args()
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit(
            "Ultralytics is not installed. Run: "
            "python -m pip install -r requirements.txt"
        ) from exc

    if not args.model.is_file():
        raise SystemExit(f"Model not found: {args.model}")
    if not 0 <= args.conf <= 1 or not 0 <= args.iou <= 1:
        raise SystemExit("--conf and --iou must be between 0 and 1.")

    model = YOLO(str(args.model))
    names = {int(key): value for key, value in model.names.items()}
    results = model.predict(
        source=parse_source(args.source),
        stream=True,
        conf=args.conf,
        iou=args.iou,
        device=args.device,
        show=args.show,
        save=args.save,
        project=str(args.project),
        name=args.name,
        verbose=False,
    )

    for index, result in enumerate(results):
        counts = class_counts(result, names)
        record = {
            "frame": index,
            "students": counts.get("person", 0),
            "cleaners": counts.get("cleaner", 0),
            "detections": sum(counts.values()),
        }
        if args.json:
            print(json.dumps(record))
        else:
            print(
                f"Frame {index}: students={record['students']}, "
                f"cleaners={record['cleaners']}, detections={record['detections']}"
            )


if __name__ == "__main__":
    main()
