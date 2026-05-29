# Monorepo Documentation

Welcome to the central repository documentation.

## Directories
- `frontend/`: Web frontend app (Node.js/React).
- `backend/`: Server API (Node.js/Express).
- `infraestructura/`: Infrastructure-as-code files (Terraform).
- `documentacion/`: Central manuals, markdown notes, and architecture diagrams.

## Pipeline Policy
Only code-related changes trigger the code linting, tests, and build pipelines. Changes to this folder (`documentacion/`) will be ignored by CI to optimize runner usage and execution times.
