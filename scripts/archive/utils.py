"""
Utility functions for traffic dataset scanning and validation.
"""

import os
import re
from datetime import datetime


# ============================================================
# Configuration
# ============================================================

# Valid dataset year range (editable)
VALID_YEAR_MIN = 2022
VALID_YEAR_MAX = 2025

# Folder naming pattern:
#   YYYY-MM-DD
#   YYYY-MM-DD_h
#   YYYY-MM-DD_l
FOLDER_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}(_[hl])?$")


# ============================================================
# Folder name parsing
# ============================================================

def parse_folder_name(folder_name):
    """
    Parse folder name into (date_str, quality).

    Examples:
        '2023-10-21'     → ('2023-10-21', 'u')
        '2023-10-21_h'   → ('2023-10-21', 'h')
        '2023-10-21_l'   → ('2023-10-21', 'l')
    """
    if "_" in folder_name:
        date_str, q = folder_name.split("_")
        return date_str, q
    return folder_name, "u"   # unspecified quality


def extract_date(folder_name):
    """Return 'YYYY-MM-DD' part of folder name."""
    return folder_name.split("_")[0]


def extract_quality(folder_name):
    """Return quality ('h','l','u')."""
    if "_" in folder_name:
        return folder_name.split("_")[1]
    return "u"


# ============================================================
# Validation helpers
# ============================================================

def is_valid_folder_name(folder_name):
    """Return True if folder matches date pattern."""
    return bool(FOLDER_PATTERN.match(folder_name))


def is_valid_year(date_str):
    """
    Return True if the date's year is within allowed dataset range.
    """
    try:
        year = int(date_str[:4])
        return VALID_YEAR_MIN <= year <= VALID_YEAR_MAX
    except Exception:
        return False


def is_valid_date(date_str):
    """
    Full date validation:
      - Must parse as a real date
      - Year must be within dataset range
    """
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return VALID_YEAR_MIN <= d.year <= VALID_YEAR_MAX
    except ValueError:
        return False


# ============================================================
# Filesystem utilities
# ============================================================

def list_candidate_folders(root_path):
    """
    Return all folder names in root that match the date-name regex.
    Does NOT filter by year range.
    """
    try:
        entries = os.listdir(root_path)
    except FileNotFoundError:
        return []

    return sorted([
        d for d in entries
        if is_valid_folder_name(d) and os.path.isdir(os.path.join(root_path, d))
    ])


def list_valid_folders(root_path):
    """
    Return all folders that:
      - match date pattern
      - AND have valid year
    """
    candidates = list_candidate_folders(root_path)
    return sorted([
        d for d in candidates
        if is_valid_year(extract_date(d))
    ])


def list_invalid_year_folders(root_path):
    """
    Return folders matching the regex but failing year check.
    """
    candidates = list_candidate_folders(root_path)
    return sorted([
        d for d in candidates
        if not is_valid_year(extract_date(d))
    ])


def compute_folder_stats(folder_path):
    """
    Count number of files and sum of file sizes.

    Returns:
        (file_count, total_size_bytes)
    """
    try:
        files = os.listdir(folder_path)
    except Exception:
        return 0, 0

    file_count = 0
    total_size = 0

    for f in files:
        fp = os.path.join(folder_path, f)
        if os.path.isfile(fp):
            file_count += 1
            try:
                total_size += os.path.getsize(fp)
            except OSError:
                pass

    return file_count, total_size


# ============================================================
# Unified folder scanner (used by both scripts)
# ============================================================

def scan_modality_root(root_path, modality):
    """
    Scan one modality root (image or audio).

    Returns:
        valid_records   – list of dicts for dataset_summary.csv
        invalid_records – list of dicts for dataset_invalid_dates.csv
    """
    valid_records = []
    invalid_records = []

    candidates = list_candidate_folders(root_path)

    for folder in candidates:
        folder_path = os.path.join(root_path, folder)

        date_str, quality = parse_folder_name(folder)
        file_count, total_size = compute_folder_stats(folder_path)

        if is_valid_date(date_str):
            valid_records.append({
                "date": date_str,
                "modality": modality,
                "quality": quality,
                "file_count": file_count,
                "total_size": total_size
            })
        else:
            invalid_records.append({
                "folder_name": folder,
                "parsed_date": date_str,
                "modality": modality,
                "quality": quality,
                "file_count": file_count,
                "total_size": total_size,
                "reason": "invalid_year_or_bad_date"
            })

    return valid_records, invalid_records