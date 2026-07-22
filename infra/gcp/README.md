# Setup
- `cd infra/gcp && terraform init`
    - What happens:
        - `terraform init` — connects to the existing GCS backend, pulls down the existing state
        - `tenv` auto-installs the pinned Terraform version from `.terraform-version` the first time `terraform` runs here
        - New collaborators additionally need IAM read/write access granted on the state bucket itself (separate from repo access)
            - Contact admin/lead
- On fresh pull:
    - `terraform plan` should report "No changes. Your infrastructure matches the configuration."

# State backend (GCS)

- Terraform state for this config lives remotely in a GCS bucket, not locally, and not committed to git (so no local `terraform.tfstate`)
- Why: shared source of truth across machines/devs, locking (a second `apply` fails/waits instead of racing), durability (not tied to one laptop's disk)

## Bootstrap (one-time, manual, outside Terraform)

- The bucket can't be created by this Terraform config, since Terraform needs the bucket to exist before it has anywhere to store the state describing it (chicken-and-egg)
- Created once, by hand:
    ```
    gcloud storage buckets create gs://overkill-be-dev-1-tfstate --location=asia-southeast1 --uniform-bucket-level-access
    gcloud storage buckets update gs://overkill-be-dev-1-tfstate --versioning
    ```
- Should never need to be re-created. A fresh clone points at the existing bucket via the `backend "gcs" {}` block in `versions.tf` — it doesn't create anything

## TLDR
- Terraform state is kept remotely and versioned for better dev collaboration and tracking
- On the very first setup of the project (inception, not fresh pull), the remote store for the state should be created once

## Fresh clone / new machine



# Checks
- `terraform state list` shows the expected resources after `init`
- `gcloud services list --enabled --project=overkill-be-dev-1` matches what `apis.tf` declares (plus GCP's default-enabled baseline APIs)

# Files
- _Terraform reads every `.tf` files and combines them as one big config_
- `.terraform/` holds the downloaded provider plugin binaries, disposable build output (like `node_modules/` or `.venv/`).
- `terraform.lock.hcl` records the exact resolved provider version plus checksums, reproducibility like uv.lock.