.PHONY: bootstrap verify-sources test apr edm resource smoke live decision continuity product evidence provenance release all

bootstrap:
	python scripts/download_apr.py

verify-sources:
	PYTHONPATH=src python -c "from yw_decisioning.source_pins import load_source_pins, validate_file_against_pin; p=load_source_pins('config/source_pins.json'); r={k:validate_file_against_pin(v['path'], v) for k,v in p['sources'].items()}; print(r); assert all(x['ok'] for x in r.values())"

test:
	pytest -q

apr:
	python scripts/run_apr_analysis.py

edm:
	python scripts/run_edm_reconciliation.py

resource:
	python scripts/run_resource_watch.py

smoke:
	python scripts/run_synthetic_smoke.py

decision:
	python scripts/run_decision_value.py

continuity:
	python scripts/run_continuity_sensitivity.py

provenance:
	python scripts/build_live_provenance.py

live:
	python scripts/download_arcgis.py night_flow_2023 night_flow_2024 night_flow_2025 night_flow_2026 reservoir_2026 dwq_2026
	python scripts/run_nightflow_model.py --splits 4 --capacity 20
	python scripts/run_decision_value.py
	python scripts/run_continuity_sensitivity.py
	python scripts/build_live_provenance.py
	python scripts/build_operational_store.py
	python scripts/build_evidence_register.py
	python scripts/build_release_manifest.py

product:
	python scripts/build_operational_store.py

evidence:
	python scripts/build_evidence_register.py

release:
	python scripts/build_release_manifest.py

all: verify-sources test apr edm resource smoke product evidence release
