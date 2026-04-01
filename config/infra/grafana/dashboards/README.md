# Grafana Dashboards

This directory contains version-controlled dashboard JSON files.

## Layout

- `json/` contains importable Grafana dashboard JSON files
- `provisioning/dashboards/dashboards.yaml` points Grafana at the mounted `json/` directory

## Rules

- Commit dashboards as JSON so they are reproducible
- Prefer provisioning over hand-made UI-only dashboards
- Use stable datasource UIDs:
  - Prometheus: `prom`
  - Loki: `loki`
  - Tempo: `tempo`

## Workflow

1. Edit dashboards in Grafana UI or by hand
2. Export JSON
3. Save into `json/`
4. Restart Grafana or let provisioning refresh

## Notes

- Keep one dashboard per JSON file
- Start with a small number of high-signal dashboards
- For app traces, logs should include `trace_id`
- Tempo links are driven by the provisioned datasource config