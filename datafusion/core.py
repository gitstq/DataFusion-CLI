"""
Core DataFusion Engine - Multi-source data fusion, conflict detection & resolution
"""

import json
import csv
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse


class DataSource:
    """Represents a single data source"""

    def __init__(self, name: str, source_type: str, data: List[Dict[str, Any]],
                 metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.source_type = source_type  # 'json', 'csv', 'api', 'rss', 'manual'
        self.data = data
        self.metadata = metadata or {}
        self.ingested_at = datetime.now().isoformat()
        self.record_count = len(data)

    def get_schema(self) -> Dict[str, str]:
        """Infer schema from data"""
        if not self.data:
            return {}
        schema = {}
        for key in self.data[0].keys():
            types = set(type(v).__name__ for v in (row.get(key) for row in self.data) if v is not None)
            schema[key] = list(types)[0] if len(types) == 1 else "mixed"
        return schema


class DataFusionEngine:
    """Core engine for fusing data from multiple sources"""

    def __init__(self):
        self.sources: Dict[str, DataSource] = {}
        self.fused_data: List[Dict[str, Any]] = []
        self.conflicts: List[Dict[str, Any]] = []
        self.link_map: Dict[str, List[str]] = {}

    def add_source(self, source: DataSource) -> None:
        """Add a data source to the engine"""
        self.sources[source.name] = source

    def remove_source(self, name: str) -> None:
        """Remove a data source"""
        if name in self.sources:
            del self.sources[name]

    def get_all_schemas(self) -> Dict[str, Dict[str, str]]:
        """Get schemas from all sources"""
        return {name: source.get_schema() for name, source in self.sources.items()}

    def find_common_keys(self) -> List[str]:
        """Find keys common across all sources"""
        if not self.sources:
            return []
        schemas = self.get_all_schemas()
        common = set(next(iter(schemas.values())).keys())
        for schema in schemas.values():
            common &= set(schema.keys())
        return list(common)

    def compute_record_hash(self, record: Dict[str, Any], keys: List[str]) -> str:
        """Compute hash for record deduplication"""
        content = "|".join(str(record.get(k, "")) for k in sorted(keys))
        return hashlib.md5(content.encode()).hexdigest()

    def detect_conflicts(self, key_field: str) -> List[Dict[str, Any]]:
        """Detect conflicting records across sources for the same key"""
        conflicts = []
        key_groups: Dict[str, Dict[str, List[Dict]]] = {}

        for source_name, source in self.sources.items():
            for record in source.data:
                key_val = str(record.get(key_field, ""))
                if not key_val:
                    continue
                if key_val not in key_groups:
                    key_groups[key_val] = {}
                if source_name not in key_groups[key_val]:
                    key_groups[key_val][source_name] = []
                key_groups[key_val][source_name].append(record)

        for key_val, sources_data in key_groups.items():
            if len(sources_data) > 1:
                # Check for conflicts
                all_records = []
                for src, records in sources_data.items():
                    for r in records:
                        all_records.append((src, r))

                for i in range(len(all_records)):
                    for j in range(i + 1, len(all_records)):
                        src1, rec1 = all_records[i]
                        src2, rec2 = all_records[j]
                        diff_fields = self._compare_records(rec1, rec2)
                        if diff_fields:
                            conflicts.append({
                                "key": key_val,
                                "key_field": key_field,
                                "source_a": src1,
                                "source_b": src2,
                                "diff_fields": diff_fields,
                                "record_a": rec1,
                                "record_b": rec2
                            })

        self.conflicts = conflicts
        return conflicts

    def _compare_records(self, rec1: Dict, rec2: Dict) -> List[Dict]:
        """Compare two records and return differing fields"""
        diffs = []
        all_keys = set(rec1.keys()) | set(rec2.keys())
        for key in all_keys:
            v1 = rec1.get(key)
            v2 = rec2.get(key)
            if v1 != v2:
                diffs.append({
                    "field": key,
                    "value_a": v1,
                    "value_b": v2,
                    "severity": "high" if v1 and v2 else "medium"
                })
        return diffs

    def resolve_conflicts(self, strategy: str = "newest") -> List[Dict[str, Any]]:
        """Resolve conflicts using specified strategy"""
        resolved = []
        for conflict in self.conflicts:
            if strategy == "newest":
                winner = conflict["record_b"]  # Assume second source is newer
            elif strategy == "oldest":
                winner = conflict["record_a"]
            elif strategy == "source_priority":
                winner = conflict["record_a"]  # First source wins
            elif strategy == "merge":
                winner = self._merge_records(conflict["record_a"], conflict["record_b"])
            else:
                winner = conflict["record_b"]

            resolved.append({
                "key": conflict["key"],
                "resolved_record": winner,
                "strategy": strategy,
                "sources": [conflict["source_a"], conflict["source_b"]]
            })

        return resolved

    def _merge_records(self, rec1: Dict, rec2: Dict) -> Dict[str, Any]:
        """Merge two records, preferring non-null values"""
        merged = dict(rec1)
        for key, val in rec2.items():
            if key not in merged or merged[key] is None:
                merged[key] = val
            elif val is not None and merged[key] != val:
                # Keep both values as list
                existing = merged[key]
                if not isinstance(existing, list):
                    existing = [existing]
                if val not in existing:
                    existing.append(val)
                merged[key] = existing
        return merged

    def fuse(self, key_field: str, conflict_strategy: str = "merge") -> List[Dict[str, Any]]:
        """Fuse all sources into unified dataset"""
        fused_map: Dict[str, Dict[str, Any]] = {}

        for source_name, source in self.sources.items():
            for record in source.data:
                key_val = str(record.get(key_field, ""))
                if not key_val:
                    continue

                # Add metadata
                enriched = dict(record)
                enriched["_source"] = source_name
                enriched["_ingested_at"] = source.ingested_at

                if key_val in fused_map:
                    fused_map[key_val] = self._merge_records(fused_map[key_val], enriched)
                    fused_map[key_val]["_sources"] = fused_map[key_val].get("_sources", []) + [source_name]
                else:
                    enriched["_sources"] = [source_name]
                    fused_map[key_val] = enriched

        self.fused_data = list(fused_map.values())
        return self.fused_data

    def compute_statistics(self) -> Dict[str, Any]:
        """Compute fusion statistics"""
        if not self.fused_data:
            return {}

        source_counts = {}
        for record in self.fused_data:
            for src in record.get("_sources", []):
                source_counts[src] = source_counts.get(src, 0) + 1

        return {
            "total_sources": len(self.sources),
            "total_records_fused": len(self.fused_data),
            "total_conflicts": len(self.conflicts),
            "source_contributions": source_counts,
            "avg_fields_per_record": sum(len(r) for r in self.fused_data) / len(self.fused_data),
            "fusion_timestamp": datetime.now().isoformat()
        }

    def find_relations(self, key_field: str, relation_fields: List[str]) -> Dict[str, List[str]]:
        """Find relationships between records based on common field values"""
        relations: Dict[str, List[str]] = {}

        for record in self.fused_data:
            key_val = str(record.get(key_field, ""))
            if not key_val:
                continue

            for field in relation_fields:
                val = record.get(field)
                if val:
                    rel_key = f"{field}:{val}"
                    if rel_key not in relations:
                        relations[rel_key] = []
                    if key_val not in relations[rel_key]:
                        relations[rel_key].append(key_val)

        # Filter to groups with multiple records
        return {k: v for k, v in relations.items() if len(v) > 1}

    def export_fused(self, format_type: str = "json") -> str:
        """Export fused data to string"""
        if format_type == "json":
            return json.dumps(self.fused_data, indent=2, ensure_ascii=False)
        elif format_type == "csv":
            if not self.fused_data:
                return ""
            output = []
            headers = list(self.fused_data[0].keys())
            output.append(",".join(headers))
            for record in self.fused_data:
                row = []
                for h in headers:
                    val = record.get(h, "")
                    if isinstance(val, (list, dict)):
                        val = json.dumps(val, ensure_ascii=False)
                    val = str(val).replace('"', '""')
                    row.append(f'"{val}"')
                output.append(",".join(row))
            return "\n".join(output)
        return ""
