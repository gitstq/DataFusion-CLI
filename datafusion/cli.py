"""
DataFusion-CLI - Terminal User Interface
"""

import sys
import json
import argparse
import os
from typing import List, Optional

from .core import DataFusionEngine, DataSource
from .parsers import parse_file


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║     🔗 DataFusion-CLI v1.0.0                                  ║
║     Lightweight Multi-Source Data Fusion Engine              ║
║     轻量级多源数据融合与智能分析引擎                           ║
╚══════════════════════════════════════════════════════════════╝
{Colors.END}
"""
    print(banner)


def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_table(headers: List[str], rows: List[List[str]], max_width: int = 40):
    """Print a simple table"""
    if not rows:
        print("No data to display")
        return

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], min(len(str(cell)), max_width))

    # Print header
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    print(f"{Colors.BOLD}{header_line}{Colors.END}")
    print("-" * len(header_line))

    # Print rows
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            if i < len(col_widths):
                s = str(cell)
                if len(s) > max_width:
                    s = s[:max_width-3] + "..."
                cells.append(s.ljust(col_widths[i]))
        print(" | ".join(cells))


def cmd_add(args):
    """Add a data source"""
    engine = DataFusionEngine()
    # Load existing sources if any
    _load_session(engine)

    if not os.path.exists(args.file):
        print_error(f"File not found: {args.file}")
        return 1

    try:
        data = parse_file(args.file)
        source = DataSource(
            name=args.name,
            source_type=args.type or _detect_type(args.file),
            data=data,
            metadata={"file": args.file}
        )
        engine.add_source(source)
        _save_session(engine)
        print_success(f"Added source '{args.name}' with {len(data)} records")
        return 0
    except Exception as e:
        print_error(f"Failed to add source: {e}")
        return 1


def cmd_list(args):
    """List all data sources"""
    engine = DataFusionEngine()
    _load_session(engine)

    if not engine.sources:
        print_warning("No data sources. Use 'add' command first.")
        return 0

    headers = ["Name", "Type", "Records", "Schema Keys"]
    rows = []
    for name, source in engine.sources.items():
        schema = source.get_schema()
        rows.append([
            name,
            source.source_type,
            str(source.record_count),
            ", ".join(list(schema.keys())[:5]) + ("..." if len(schema) > 5 else "")
        ])

    print_table(headers, rows)
    return 0


def cmd_schema(args):
    """Show schema for a source"""
    engine = DataFusionEngine()
    _load_session(engine)

    if args.source not in engine.sources:
        print_error(f"Source not found: {args.source}")
        return 1

    source = engine.sources[args.source]
    schema = source.get_schema()

    print_info(f"Schema for '{args.source}':")
    headers = ["Field", "Type"]
    rows = [[k, v] for k, v in schema.items()]
    print_table(headers, rows)
    return 0


def cmd_fuse(args):
    """Fuse all data sources"""
    engine = DataFusionEngine()
    _load_session(engine)

    if len(engine.sources) < 1:
        print_warning("No data sources to fuse.")
        return 0

    print_info(f"Fusing {len(engine.sources)} sources with key='{args.key}'...")

    # Detect conflicts first
    conflicts = engine.detect_conflicts(args.key)
    if conflicts:
        print_warning(f"Detected {len(conflicts)} conflicts")
        if args.verbose:
            for c in conflicts[:5]:
                print(f"  - Key '{c['key']}': {len(c['diff_fields'])} field differences")

    # Fuse
    fused = engine.fuse(args.key, conflict_strategy=args.strategy)
    _save_session(engine)

    print_success(f"Fused into {len(fused)} unified records")

    # Show stats
    stats = engine.compute_statistics()
    print_info("Fusion Statistics:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    return 0


def cmd_export(args):
    """Export fused data"""
    engine = DataFusionEngine()
    _load_session(engine)

    if not engine.fused_data:
        print_warning("No fused data. Run 'fuse' command first.")
        return 0

    output = engine.export_fused(args.format)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print_success(f"Exported to {args.output}")
    else:
        print(output)

    return 0


def cmd_stats(args):
    """Show statistics"""
    engine = DataFusionEngine()
    _load_session(engine)

    print_info("DataFusion Statistics:")
    print(f"  Sources loaded: {len(engine.sources)}")
    print(f"  Fused records: {len(engine.fused_data)}")
    print(f"  Conflicts detected: {len(engine.conflicts)}")

    if engine.sources:
        print("\nSource Details:")
        for name, source in engine.sources.items():
            print(f"  📁 {name}: {source.record_count} records ({source.source_type})")

    if engine.fused_data:
        stats = engine.compute_statistics()
        print("\nFusion Results:")
        for k, v in stats.items():
            print(f"  • {k}: {v}")

    return 0


def cmd_relations(args):
    """Find relationships in fused data"""
    engine = DataFusionEngine()
    _load_session(engine)

    if not engine.fused_data:
        print_warning("No fused data. Run 'fuse' command first.")
        return 0

    fields = args.fields.split(",")
    relations = engine.find_relations(args.key, fields)

    if not relations:
        print_info("No relationships found")
        return 0

    print_info(f"Found {len(relations)} relationship groups:")
    for rel_key, records in list(relations.items())[:20]:
        print(f"  {rel_key}: {len(records)} records")
        if args.verbose:
            for r in records[:5]:
                print(f"    - {r}")

    return 0


def cmd_conflicts(args):
    """Show detected conflicts"""
    engine = DataFusionEngine()
    _load_session(engine)

    if not engine.conflicts:
        print_info("No conflicts detected")
        return 0

    print_info(f"Conflicts ({len(engine.conflicts)}):")
    for c in engine.conflicts[:10]:
        print(f"\n  Key: {c['key']}")
        print(f"  Between: {c['source_a']} ↔ {c['source_b']}")
        for d in c['diff_fields']:
            print(f"    • {d['field']}: {d['value_a']} ≠ {d['value_b']} ({d['severity']})")

    return 0


def cmd_demo(args):
    """Run demo with sample data"""
    engine = DataFusionEngine()

    # Sample data source A
    data_a = [
        {"id": "1", "name": "Alice", "age": 30, "city": "Beijing", "score": 85},
        {"id": "2", "name": "Bob", "age": 25, "city": "Shanghai", "score": 92},
        {"id": "3", "name": "Charlie", "age": 35, "city": "Shenzhen", "score": 78},
    ]

    # Sample data source B (with some overlaps and conflicts)
    data_b = [
        {"id": "1", "name": "Alice", "age": 31, "city": "Beijing", "email": "alice@example.com"},
        {"id": "2", "name": "Bob", "age": 25, "city": "Shanghai", "email": "bob@example.com"},
        {"id": "4", "name": "David", "age": 28, "city": "Guangzhou", "email": "david@example.com"},
    ]

    # Sample data source C
    data_c = [
        {"id": "1", "name": "Alice", "department": "Engineering", "salary": 15000},
        {"id": "3", "name": "Charlie", "department": "Product", "salary": 18000},
        {"id": "5", "name": "Eve", "department": "Design", "salary": 16000},
    ]

    engine.add_source(DataSource("employees_hr", "csv", data_a))
    engine.add_source(DataSource("employees_it", "json", data_b))
    engine.add_source(DataSource("employees_payroll", "csv", data_c))

    print_info("Demo: Employee Data Fusion")
    print("Sources:")
    for name, src in engine.sources.items():
        print(f"  📁 {name}: {src.record_count} records")

    # Detect conflicts
    conflicts = engine.detect_conflicts("id")
    if conflicts:
        print(f"\n⚠ Conflicts detected: {len(conflicts)}")
        for c in conflicts[:3]:
            print(f"  ID {c['key']}: {len(c['diff_fields'])} differences")

    # Fuse
    fused = engine.fuse("id", conflict_strategy="merge")
    print(f"\n✓ Fused into {len(fused)} unified records")

    # Show results
    print("\nFused Records:")
    headers = ["ID", "Name", "Age", "City", "Email", "Department", "Salary", "Sources"]
    rows = []
    for r in fused:
        rows.append([
            r.get("id", ""),
            r.get("name", ""),
            str(r.get("age", "")),
            r.get("city", ""),
            r.get("email", ""),
            r.get("department", ""),
            str(r.get("salary", "")),
            ", ".join(r.get("_sources", []))
        ])
    print_table(headers, rows)

    # Stats
    stats = engine.compute_statistics()
    print(f"\n📊 Statistics:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # Relations
    relations = engine.find_relations("id", ["city", "department"])
    if relations:
        print(f"\n🔗 Relationships found: {len(relations)}")
        for k, v in list(relations.items())[:5]:
            print(f"  {k}: {', '.join(v)}")

    _save_session(engine)
    return 0


def _detect_type(filepath: str) -> str:
    """Detect file type from extension"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.json':
        return 'json'
    elif ext == '.csv':
        return 'csv'
    return 'unknown'


SESSION_FILE = ".datafusion_session.json"


def _save_session(engine: DataFusionEngine):
    """Save session to file"""
    session = {
        "sources": {},
        "fused_data": engine.fused_data,
        "conflicts": engine.conflicts
    }
    for name, source in engine.sources.items():
        session["sources"][name] = {
            "type": source.source_type,
            "data": source.data,
            "metadata": source.metadata
        }
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(session, f, ensure_ascii=False)


def _load_session(engine: DataFusionEngine):
    """Load session from file"""
    if not os.path.exists(SESSION_FILE):
        return
    try:
        with open(SESSION_FILE, 'r', encoding='utf-8') as f:
            session = json.load(f)
        for name, info in session.get("sources", {}).items():
            source = DataSource(name, info["type"], info["data"], info.get("metadata"))
            engine.add_source(source)
        engine.fused_data = session.get("fused_data", [])
        engine.conflicts = session.get("conflicts", [])
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="DataFusion-CLI - Multi-Source Data Fusion Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  datafusion demo                    # Run demo
  datafusion add -n users -f users.json --type json
  datafusion list                    # List sources
  datafusion fuse -k id              # Fuse by 'id' key
  datafusion export -f csv -o out.csv
  datafusion stats                   # Show statistics
  datafusion conflicts               # Show conflicts
        """
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # add
    add_parser = subparsers.add_parser('add', help='Add a data source')
    add_parser.add_argument('-n', '--name', required=True, help='Source name')
    add_parser.add_argument('-f', '--file', required=True, help='Data file path')
    add_parser.add_argument('-t', '--type', help='Source type (json/csv)')

    # list
    subparsers.add_parser('list', help='List all sources')

    # schema
    schema_parser = subparsers.add_parser('schema', help='Show source schema')
    schema_parser.add_argument('source', help='Source name')

    # fuse
    fuse_parser = subparsers.add_parser('fuse', help='Fuse all sources')
    fuse_parser.add_argument('-k', '--key', required=True, help='Key field for fusion')
    fuse_parser.add_argument('-s', '--strategy', default='merge',
                             choices=['merge', 'newest', 'oldest', 'source_priority'],
                             help='Conflict resolution strategy')
    fuse_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    # export
    export_parser = subparsers.add_parser('export', help='Export fused data')
    export_parser.add_argument('-f', '--format', default='json', choices=['json', 'csv'])
    export_parser.add_argument('-o', '--output', help='Output file')

    # stats
    subparsers.add_parser('stats', help='Show statistics')

    # relations
    rel_parser = subparsers.add_parser('relations', help='Find relationships')
    rel_parser.add_argument('-k', '--key', required=True, help='Key field')
    rel_parser.add_argument('-f', '--fields', required=True, help='Relation fields (comma-separated)')
    rel_parser.add_argument('-v', '--verbose', action='store_true')

    # conflicts
    subparsers.add_parser('conflicts', help='Show conflicts')

    # demo
    subparsers.add_parser('demo', help='Run demo')

    # Interactive mode
    parser.add_argument('-i', '--interactive', action='store_true', help='Interactive mode')

    args = parser.parse_args()

    if args.interactive or not args.command:
        return interactive_mode()

    commands = {
        'add': cmd_add,
        'list': cmd_list,
        'schema': cmd_schema,
        'fuse': cmd_fuse,
        'export': cmd_export,
        'stats': cmd_stats,
        'relations': cmd_relations,
        'conflicts': cmd_conflicts,
        'demo': cmd_demo,
    }

    if args.command in commands:
        return commands[args.command](args)
    else:
        parser.print_help()
        return 1


def interactive_mode():
    """Interactive TUI mode"""
    print_banner()
    print("Interactive mode. Type 'help' for commands, 'quit' to exit.\n")

    engine = DataFusionEngine()
    _load_session(engine)

    while True:
        try:
            cmd = input(f"{Colors.CYAN}datafusion>{Colors.END} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not cmd:
            continue
        if cmd.lower() in ('quit', 'exit', 'q'):
            print("Goodbye!")
            break
        if cmd.lower() == 'help':
            print("""
Commands:
  add <name> <file> [type]  - Add data source
  list                      - List sources
  schema <source>           - Show schema
  fuse <key> [strategy]     - Fuse data
  export [format] [file]    - Export data
  stats                     - Show statistics
  conflicts                 - Show conflicts
  relations <key> <fields>  - Find relationships
  demo                      - Run demo
  clear                     - Clear screen
  help                      - Show this help
  quit                      - Exit
            """)
            continue
        if cmd.lower() == 'clear':
            os.system('clear' if os.name != 'nt' else 'cls')
            print_banner()
            continue
        if cmd.lower() == 'demo':
            cmd_demo(argparse.Namespace())
            continue

        parts = cmd.split()
        if not parts:
            continue

        try:
            if parts[0] == 'add' and len(parts) >= 3:
                source = DataSource(
                    parts[1],
                    parts[3] if len(parts) > 3 else _detect_type(parts[2]),
                    parse_file(parts[2])
                )
                engine.add_source(source)
                _save_session(engine)
                print_success(f"Added '{parts[1]}' with {source.record_count} records")
            elif parts[0] == 'list':
                if not engine.sources:
                    print_warning("No sources")
                else:
                    for name, src in engine.sources.items():
                        print(f"  {name}: {src.record_count} records ({src.source_type})")
            elif parts[0] == 'schema' and len(parts) > 1:
                if parts[1] in engine.sources:
                    schema = engine.sources[parts[1]].get_schema()
                    for k, v in schema.items():
                        print(f"  {k}: {v}")
            elif parts[0] == 'fuse' and len(parts) > 1:
                strategy = parts[2] if len(parts) > 2 else 'merge'
                conflicts = engine.detect_conflicts(parts[1])
                if conflicts:
                    print_warning(f"{len(conflicts)} conflicts detected")
                fused = engine.fuse(parts[1], strategy)
                _save_session(engine)
                print_success(f"Fused into {len(fused)} records")
            elif parts[0] == 'export':
                fmt = parts[1] if len(parts) > 1 else 'json'
                output = engine.export_fused(fmt)
                if len(parts) > 2:
                    with open(parts[2], 'w') as f:
                        f.write(output)
                    print_success(f"Saved to {parts[2]}")
                else:
                    print(output[:2000])
            elif parts[0] == 'stats':
                cmd_stats(argparse.Namespace())
            elif parts[0] == 'conflicts':
                cmd_conflicts(argparse.Namespace())
            else:
                print_error(f"Unknown command: {parts[0]}")
        except Exception as e:
            print_error(f"Error: {e}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
