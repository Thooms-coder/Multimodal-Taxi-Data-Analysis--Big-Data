#!/usr/bin/env python3
"""
parse_logs_to_csv.py

Stream-parse traffic log JSON lines (traffic.txt*) into a flat CSV suitable
for analysis and joins with image/audio quality tables.
"""

import argparse
import csv
import glob
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Iterable, List, Optional


# -------------------------------------------------------------------
# LOGGING
# -------------------------------------------------------------------
def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


# -------------------------------------------------------------------
# ARGUMENTS
# -------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse traffic.txt* JSON logs into a flat CSV."
    )
    parser.add_argument("--logs-root", required=True, help="Folder containing logs")
    parser.add_argument("--output", required=True, help="Output CSV file")
    parser.add_argument("--max-lines", type=int, default=None,
                        help="Max number of lines to parse (optional)")
    return parser.parse_args()


# -------------------------------------------------------------------
# UTILS
# -------------------------------------------------------------------
def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def iter_log_files(logs_root: Path) -> Iterable[Path]:
    pattern = str(logs_root / "traffic.txt*")
    for fname in sorted(glob.glob(pattern)):
        yield Path(fname)


# -------------------------------------------------------------------
# FLATTENING A SINGLE RECORD
# -------------------------------------------------------------------
def flatten_log_record(rec: Dict[str, Any], log_file: str) -> Dict[str, Any]:

    # -------- DATE/TIME --------
    frame_dto = rec.get("frame_dto")
    dto = rec.get("dto")

    date_str = None
    time_str = None

    if isinstance(frame_dto, str) and " " in frame_dto:
        date_str, time_str = frame_dto.split()[:2]

    if date_str is None and isinstance(dto, str) and " " in dto:
        date_str = dto.split()[0]

    # -------- IMAGE --------
    img_path = rec.get("img")
    img_file = None

    if isinstance(img_path, str):
        img_file = img_path.split("/")[-1]
        folder = img_path.split("/")[0]
        if date_str is None and len(folder) >= 10:
            if folder[4] == "-" and folder[7] == "-":
                date_str = folder[:10]

    # -------- AUDIO --------
    dba = rec.get("dba")
    dba_dto = rec.get("dba_dto")

    # -------- INTERSECTION / CROSS --------
    intersection = rec.get("intersection") or []
    cross = rec.get("cross") or []

    intersection_0 = intersection[0] if len(intersection) > 0 else None
    intersection_1 = intersection[1] if len(intersection) > 1 else None

    cross_0_0 = cross_0_1 = cross_1_0 = cross_1_1 = None
    if len(cross) > 0 and isinstance(cross[0], list):
        cross_0_0 = cross[0][0] if len(cross[0]) > 0 else None
        cross_0_1 = cross[0][1] if len(cross[0]) > 1 else None
    if len(cross) > 1 and isinstance(cross[1], list):
        cross_1_0 = cross[1][0] if len(cross[1]) > 0 else None
        cross_1_1 = cross[1][1] if len(cross[1]) > 1 else None

    # -------- DETECTION --------
    probs = rec.get("probs")
    cls = rec.get("cls")
    point_len = rec.get("point_len")
    tid = rec.get("tid")
    seq_len = rec.get("seq_len")
    seq_path = rec.get("seq_path")

    # -------- BOX --------
    box = rec.get("box") or []
    if not isinstance(box, list):
        box = []

    box_x1 = box[0] if len(box) > 0 else None
    box_y1 = box[1] if len(box) > 1 else None
    box_x2 = box[2] if len(box) > 2 else None
    box_y2 = box[3] if len(box) > 3 else None

    return {
        "date": date_str,
        "time": time_str,
        "frame_dto": frame_dto,
        "dto": dto,
        "img_path": img_path,
        "img_file": img_file,
        "dba": dba,
        "dba_dto": dba_dto,
        "intersection_0": intersection_0,
        "intersection_1": intersection_1,
        "cross_0_0": cross_0_0,
        "cross_0_1": cross_0_1,
        "cross_1_0": cross_1_0,
        "cross_1_1": cross_1_1,
        "probs": probs,
        "cls": cls,
        "point_len": point_len,
        "box_x1": box_x1,
        "box_y1": box_y1,
        "box_x2": box_x2,
        "box_y2": box_y2,
        "tid": tid,
        "seq_len": seq_len,
        "seq_path": seq_path,
        "log_file": log_file,
    }


# -------------------------------------------------------------------
# MAIN FUNCTION (missing before — now restored)
# -------------------------------------------------------------------
def main() -> None:
    setup_logging()
    args = parse_args()

    logs_root = Path(args.logs_root).resolve()
    output_path = Path(args.output).resolve()

    ensure_parent_dir(output_path)

    log_files = list(iter_log_files(logs_root))
    if not log_files:
        logging.error("No traffic.txt* files found.")
        sys.exit(1)

    logging.info(f"Found {len(log_files)} log files.")

    fieldnames = [
        "date", "time", "frame_dto", "dto",
        "img_path", "img_file",
        "dba", "dba_dto",
        "intersection_0", "intersection_1",
        "cross_0_0", "cross_0_1", "cross_1_0", "cross_1_1",
        "probs", "cls", "point_len",
        "box_x1", "box_y1", "box_x2", "box_y2",
        "tid", "seq_len", "seq_path",
        "log_file"
    ]

    total_lines = 0
    parsed = 0
    errors = 0

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for lf in log_files:
            logging.info(f"Parsing {lf}...")
            with lf.open("r", encoding="utf-8") as fin:
                for line in fin:
                    if args.max_lines and total_lines >= args.max_lines:
                        logging.info("Reached max-lines limit.")
                        return

                    total_lines += 1
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        rec = json.loads(line)
                        writer.writerow(flatten_log_record(rec, lf.name))
                        parsed += 1

                    except Exception as e:
                        errors += 1
                        if errors <= 10:
                            logging.warning(f"Error parsing line {total_lines}: {e}")
                        continue

                    if parsed % 100000 == 0:
                        logging.info(f"Parsed {parsed} lines...")

    logging.info("Done.")
    logging.info(f"Total lines read: {total_lines}")
    logging.info(f"Parsed: {parsed}")
    logging.info(f"Errors: {errors}")
    logging.info(f"Wrote CSV -> {output_path}")


if __name__ == "__main__":
    main()
