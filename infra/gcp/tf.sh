#!/bin/sh
set -e

# Wraps terraform so local runs pick up TF_VAR_* values from the repo's
# root .env — same values CI reads from GitHub secrets/variables.
# Usage: ./tf.sh plan | ./tf.sh apply | ./tf.sh output ...

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
ENV_FILE="$SCRIPT_DIR/../../.env"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

# Terraform only recognizes TF_VAR_<name>, never the app's own key names —
# bridge the ones this config reuses from .env.
export TF_VAR_supabase_url="$SUPABASE_URL"
export TF_VAR_supabase_key="$SUPABASE_KEY"

cd "$SCRIPT_DIR"
terraform "$@"
