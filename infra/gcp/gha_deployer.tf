# CI identity #1: the deployer — the build pipeline's badge
# (build-push-image.yaml: push image, deploy it). Narrow on purpose; the
# admin-powered terraform identity is separate (gha_terraformer.tf).

# Deliberately separate from the runtime SA (overkill-be-run):
# - deployer: strong permissions, but alive only for seconds per deploy
# - runtime: weak permissions, but internet-facing and running 24/7
# One shared account would mean an internet-facing service with deploy
# powers — worst of both.
# - Also... when GCP creates a service account it assigns it an email as its canonical identifier
resource "google_service_account" "deployer" {
  project      = var.project_id
  account_id   = local.deployer_sa_id
  display_name = "CI deploy SA, impersonated by GitHub Actions via WIF"
}

# The tie that makes the trust layer (wif.tf) mean something: identities
# from the pool that passed the rules AND whose repository fact matches
# ours may act as the deployer. Until this exists, verified GitHub runs
# can log in but can't be anyone — i.e. can't do anything.
# principalSet:// means "everyone matching this fact" — any branch or
# workflow of the repo qualifies.
resource "google_service_account_iam_member" "deployer_wif" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repository}"
}

# Growing CI's powers only ever adds grants below this line (adding grants to the SA)
# ...the trust pieces in wif.tf stay untouched no matter what the pipeline learns to do.
# (repo doesn't get permissions directly it gets the right to become the deployer, the deployer holds the perms)

resource "google_project_iam_member" "deployer_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

# Lets CI deploy new images (`gcloud run deploy`). developer, not admin:
# admin could also change who may invoke the service — deploys don't need that.
resource "google_project_iam_member" "deployer_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

# Deploying a service that runs AS the runtime SA requires "actAs" on it,
# gated separately by GCP; granted on this one SA only, not project-wide.
resource "google_service_account_iam_member" "deployer_actas_runtime" {
  service_account_id = google_service_account.run_overkill_be.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deployer.email}"
}

output "deployer_sa_email" {
  value = google_service_account.deployer.email
}
