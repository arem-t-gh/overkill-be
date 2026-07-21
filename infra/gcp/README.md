## State backend (GCS)

- Terraform state for this config lives remotely in a GCS bucket, not locally, and not committed to git
- Why: shared source of truth across machines/devs, locking (a second `apply` fails/waits instead of racing), durability (not tied to one laptop's disk)

## Bootstrap (one-time, manual, outside Terraform)

- The bucket can't be created by this Terraform config, since Terraform needs the bucket to exist before it has anywhere to store the state describing it (chicken-and-egg)
- Created once, by hand:
    ```
    gcloud storage buckets create gs://overkill-be-dev-1-tfstate --location=asia-southeast1 --uniform-bucket-level-access
    gcloud storage buckets update gs://overkill-be-dev-1-tfstate --versioning
    ```
- Should never need to be re-created. A fresh clone points at the existing bucket via the `backend "gcs" {}` block in `versions.tf` — it doesn't create anything

## Fresh clone / new machine

- `terraform init` — connects to the existing GCS backend, pulls down the existing state
- `tenv` auto-installs the pinned Terraform version from `.terraform-version` the first time `terraform` runs here
- New collaborators additionally need IAM read/write access granted on the state bucket itself (separate from repo access)

# Checks
- `terraform state list` shows the expected resources after `init`
- `gcloud services list --enabled --project=overkill-be-dev-1` matches what `apis.tf` declares (plus GCP's default-enabled baseline APIs)
