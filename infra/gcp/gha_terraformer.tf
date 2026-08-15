# CI identity #2: the terraformer — the badge the infra pipeline wears to
# run `terraform plan/apply`. Separate from the deployer so the ungated
# build pipeline never holds admin power; impersonation is context-locked below.

resource "google_service_account" "terraformer" {
  project      = var.project_id
  account_id   = local.tf_sa_id
  display_name = "CI terraform SA, impersonated by GitHub Actions via WIF"
}

# principal:// (exact identity) instead of principalSet:// (any repo run):
# only jobs whose subject matches one of these contexts may become this SA.
# Every terraform job declares a GitHub `environment:` (see _terraform.yml);
# "plan" has no protection rules (read-only, runs unattended), var.app_env
# ("dev" today, stage/prod later) requires approval — same reviewer setup
# as manage_superuser_cli.yaml already uses.
locals {
  terraformer_wif_subjects = [
    # for `:environment`, it acts on the jobs>terraform>environment (see _tf.yaml)
    "repo:${var.github_repository}:environment:plan",
    "repo:${var.github_repository}:environment:${var.app_env}",
  ]
}

resource "google_service_account_iam_member" "terraformer_wif" {
  for_each = toset(local.terraformer_wif_subjects)

  service_account_id = google_service_account.terraformer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principal://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/subject/${each.value}"
}

# Roles CI needs to run terraform itself: one admin role per service
# terraform manages here — deliberately enumerated instead of roles/editor.
locals {
  terraformer_roles = [
    "roles/serviceusage.serviceUsageAdmin",  # enable/disable project APIs
    "roles/artifactregistry.admin",          # manage the image repo itself
    "roles/cloudsql.admin",                  # instance, database, db user
    "roles/secretmanager.admin",             # secrets, versions, their IAM
    "roles/iam.serviceAccountAdmin",         # create/manage service accounts
    "roles/iam.workloadIdentityPoolAdmin",   # manage the WIF pool/provider
    "roles/run.admin",                       # full Cloud Run incl. invoker IAM
    "roles/resourcemanager.projectIamAdmin", # manage project-level IAM grants
  ]
}

resource "google_project_iam_member" "terraformer" {
  for_each = toset(local.terraformer_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.terraformer.email}"
}

# objectAdmin (data only) isn't enough — this resource itself IS a
# bucket-level IAM grant, so managing/planning it needs bucket IAM
# read/write too, which only storage.admin covers. Still scoped to this
# one bucket, not project-wide.
resource "google_storage_bucket_iam_member" "terraformer_tfstate" {
  bucket = var.tfstate_bucket
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.terraformer.email}"
}

output "terraformer_sa_email" {
  value = google_service_account.terraformer.email
}
