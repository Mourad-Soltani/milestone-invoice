# Milestone Invoice CLI

**Signature: Mourad.Soltani**

A tiny, zero-bloat CLI that turns a simple YAML or JSON milestone plan into clean progress-billing invoices (Markdown, HTML, or JSON). Built for freelancers and contractors who bill by milestone instead of pure time-and-materials.

## Why this exists

Most invoicing tools are either heavy SaaS or generic hour trackers. Contractors who work in fixed-price phases need something that:

- Shows which milestones are already paid / completed
- Calculates remaining balance and progress %
- Produces a professional document they can email or paste into Notion/Docs

This tool does exactly that and nothing more.

## Features

- Load plans from YAML or JSON
- Validate structure before rendering
- Compute totals, paid, remaining, progress percentage
- Output Markdown (default), HTML, or JSON
- Pure Python + optional PyYAML – runs anywhere
- Health tests included

## Quick start

```bash
# optional – only needed for YAML plans
pip install pyyaml

# validate a plan
python main.py examples/sample_plan.json --validate-only

# render Markdown invoice to stdout
python main.py examples/sample_plan.json

# render HTML
python main.py examples/sample_plan.json -f html -o invoice.html

# render machine-readable JSON
python main.py examples/sample_plan.json -f json
```

## Plan format

Minimal example (`examples/sample_plan.json`):

```json
{
  "issuer": { "name": "Your Name", "email": "you@example.com" },
  "client": { "name": "Client Name", "email": "billing@client.com" },
  "project": "Project Title",
  "currency": "USD",
  "milestones": [
    { "name": "Discovery", "amount": 1200, "status": "paid" },
    { "name": "Build", "amount": 3500, "status": "pending" }
  ]
}
```

`status` values that count as paid/completed: `paid`, `completed`, `done` (case-insensitive).

## Tests

```bash
pip install pytest pyyaml
pytest tests/ -v
```

All health tests must pass.

## License

MIT – see [LICENSE](LICENSE)

---

Built and signed by **Mourad.Soltani**
