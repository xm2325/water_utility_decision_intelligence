# Release checklist

This repository separates code quality, source verification and evidence claims.

Before merging a release branch:

- [ ] `pytest -q` passes in a clean Python 3.11 environment.
- [ ] `make bootstrap` downloads all pinned APR files and verifies SHA-256, row count and file size.
- [ ] `make all` rebuilds the committed aggregate analyses from the pinned sources.
- [ ] The real-data workflow downloads the current public ArcGIS night-flow layers and completes rolling-origin validation.
- [ ] The promotion decision is generated from the configured champion/challenger and data-contract gates.
- [ ] The operational investigation queue uses the selected champion rather than always using the ML challenger.
- [ ] `results/EVIDENCE_REGISTER.csv` marks only executed real-data outputs as application-ready evidence.
- [ ] Synthetic smoke-test metrics remain labelled as development validation and are not copied into CV claims.
- [ ] Source reconciliation differences are reviewed rather than silently overwritten.
- [ ] `VERSION`, package `__version__`, README and CHANGELOG agree.

A failed real-data workflow is a release blocker when the failure affects source retrieval, schema compatibility, evaluation correctness or evidence status. A model that fails the promotion gate is not itself a release failure: retaining the baseline is a valid governed outcome.
