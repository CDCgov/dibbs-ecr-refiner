#!/bin/bash
set -euo pipefail

# run from this script's own directory so the relative --out path works
# regardless of where the caller invoked it from.
cd "$(dirname "$0")"

python generate_template_oids.py \
  --ig-md CDAR2_IG_PHCASERPT_R2_STU3.1.1_Vol2_2022JUL_2024OCT.md \
  --out ../../app/services/ecr/specification/template_oids.py

# format the generated file with ruff
ruff format ../../app/services/ecr/specification/template_oids.py
ruff check --fix ../../app/services/ecr/specification/template_oids.py

echo "Template OIDs generated and formatted successfully"
