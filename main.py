#!/usr/bin/env python3
# Signature: Mourad.Soltani
"""
Milestone Invoice CLI
Generate professional progress-billing invoices from a simple YAML/JSON plan.
Perfect for freelancers and contractors who bill by milestone.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore


__version__ = "0.1.0"
__author__ = "Mourad.Soltani"


def load_plan(path: Path) -> dict[str, Any]:
    """Load a milestone plan from YAML or JSON."""
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError(
                "PyYAML is required for YAML plans. Install with: pip install pyyaml"
            )
        data = yaml.safe_load(text)
    elif suffix == ".json":
        data = json.loads(text)
    else:
        # try JSON first, then YAML
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            if yaml is None:
                raise RuntimeError("Cannot parse file; install pyyaml or use JSON")
            data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Plan must be a mapping/object at the top level")
    return data


def validate_plan(plan: dict[str, Any]) -> list[str]:
    """Return list of validation errors (empty = ok)."""
    errors: list[str] = []
    required = ["client", "project", "milestones"]
    for key in required:
        if key not in plan:
            errors.append(f"Missing required key: {key}")
    if "milestones" in plan:
        if not isinstance(plan["milestones"], list) or not plan["milestones"]:
            errors.append("milestones must be a non-empty list")
        else:
            for i, m in enumerate(plan["milestones"]):
                if not isinstance(m, dict):
                    errors.append(f"milestone[{i}] must be an object")
                    continue
                for k in ("name", "amount"):
                    if k not in m:
                        errors.append(f"milestone[{i}] missing '{k}'")
                if "amount" in m:
                    try:
                        float(m["amount"])
                    except (TypeError, ValueError):
                        errors.append(f"milestone[{i}].amount must be a number")
    return errors


def compute_totals(plan: dict[str, Any]) -> dict[str, Any]:
    """Add computed fields: total, paid, remaining, progress %."""
    milestones = plan.get("milestones", [])
    total = sum(float(m.get("amount", 0)) for m in milestones)
    paid = sum(
        float(m.get("amount", 0))
        for m in milestones
        if m.get("status", "").lower() in {"paid", "completed", "done"}
    )
    remaining = total - paid
    progress = (paid / total * 100) if total else 0.0
    plan = dict(plan)  # shallow copy
    plan["_computed"] = {
        "total": round(total, 2),
        "paid": round(paid, 2),
        "remaining": round(remaining, 2),
        "progress_pct": round(progress, 1),
        "invoice_date": date.today().isoformat(),
    }
    return plan


def render_markdown(plan: dict[str, Any]) -> str:
    """Render a clean Markdown invoice."""
    c = plan.get("_computed", {})
    client = plan.get("client", {})
    if isinstance(client, str):
        client = {"name": client}
    project = plan.get("project", "Project")
    currency = plan.get("currency", "USD")
    issuer = plan.get("issuer", {"name": "Freelancer"})

    lines = [
        f"# Invoice – {project}",
        "",
        f"**Invoice date:** {c.get('invoice_date', date.today().isoformat())}",
        f"**Currency:** {currency}",
        "",
        "## From",
        f"- {issuer.get('name', 'Freelancer')}",
    ]
    if issuer.get("email"):
        lines.append(f"- {issuer['email']}")
    if issuer.get("address"):
        lines.append(f"- {issuer['address']}")
    lines += ["", "## Bill To", f"- {client.get('name', 'Client')}"]
    if client.get("email"):
        lines.append(f"- {client['email']}")
    if client.get("company"):
        lines.append(f"- {client['company']}")

    lines += [
        "",
        "## Milestones",
        "",
        "| # | Milestone | Amount | Status |",
        "|---|-----------|--------|--------|",
    ]
    for i, m in enumerate(plan.get("milestones", []), 1):
        status = m.get("status", "pending")
        amount = float(m.get("amount", 0))
        lines.append(f"| {i} | {m.get('name', '')} | {amount:.2f} {currency} | {status} |")

    lines += [
        "",
        "## Summary",
        f"- **Total contract value:** {c.get('total', 0):.2f} {currency}",
        f"- **Already paid / completed:** {c.get('paid', 0):.2f} {currency}",
        f"- **Remaining:** {c.get('remaining', 0):.2f} {currency}",
        f"- **Progress:** {c.get('progress_pct', 0)}%",
        "",
        "---",
        f"*Generated by Milestone Invoice CLI v{__version__} – Mourad.Soltani*",
    ]
    return "\n".join(lines)


def render_html(plan: dict[str, Any]) -> str:
    """Render a simple self-contained HTML invoice."""
    md = render_markdown(plan)
    # very light conversion for readability
    body = md.replace("\n", "<br>\n").replace("|", " | ")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Invoice – {plan.get('project', 'Project')}</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; color: #222; }}
  h1 {{ border-bottom: 2px solid #333; padding-bottom: .4rem; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
  th, td {{ border: 1px solid #ccc; padding: .5rem .75rem; text-align: left; }}
  th {{ background: #f5f5f5; }}
  .footer {{ margin-top: 2rem; font-size: .85rem; color: #666; }}
</style>
</head>
<body>
<pre style="white-space: pre-wrap; font-family: inherit;">{md}</pre>
<div class="footer">Generated by Milestone Invoice CLI v{__version__} – Mourad.Soltani</div>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="milestone-invoice",
        description="Generate progress-billing invoices from a milestone plan (YAML/JSON).",
    )
    parser.add_argument(
        "plan",
        type=Path,
        help="Path to plan file (.yaml / .yml / .json)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["md", "markdown", "html", "json"],
        default="md",
        help="Output format (default: md)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write to file instead of stdout",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the plan and exit",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__} (Mourad.Soltani)",
    )
    args = parser.parse_args(argv)

    if not args.plan.exists():
        print(f"Error: plan file not found: {args.plan}", file=sys.stderr)
        return 1

    try:
        plan = load_plan(args.plan)
    except Exception as e:
        print(f"Error loading plan: {e}", file=sys.stderr)
        return 1

    errors = validate_plan(plan)
    if errors:
        print("Validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if args.validate_only:
        print("Plan is valid.")
        return 0

    plan = compute_totals(plan)

    fmt = args.format.lower()
    if fmt in {"md", "markdown"}:
        content = render_markdown(plan)
    elif fmt == "html":
        content = render_html(plan)
    elif fmt == "json":
        content = json.dumps(plan, indent=2, default=str)
    else:
        print(f"Unsupported format: {fmt}", file=sys.stderr)
        return 1

    if args.output:
        args.output.write_text(content, encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
