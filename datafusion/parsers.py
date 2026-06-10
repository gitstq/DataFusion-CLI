"""
Data Parsers - JSON, CSV, and other format parsers
"""

import json
import csv
import os
from typing import List, Dict, Any


def parse_json(filepath: str) -> List[Dict[str, Any]]:
    """Parse JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        # Single object wrapped in list
        return [data]
    return data


def parse_csv(filepath: str) -> List[Dict[str, Any]]:
    """Parse CSV file"""
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings
            record = {}
            for k, v in row.items():
                if v is None:
                    record[k] = None
                elif v.lower() in ('true', 'yes'):
                    record[k] = True
                elif v.lower() in ('false', 'no'):
                    record[k] = False
                else:
                    try:
                        if '.' in v:
                            record[k] = float(v)
                        else:
                            record[k] = int(v)
                    except ValueError:
                        record[k] = v
            records.append(record)
    return records


def parse_file(filepath: str) -> List[Dict[str, Any]]:
    """Auto-detect and parse file"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.json':
        return parse_json(filepath)
    elif ext == '.csv':
        return parse_csv(filepath)
    else:
        # Try JSON first, then CSV
        try:
            return parse_json(filepath)
        except (json.JSONDecodeError, ValueError):
            return parse_csv(filepath)
