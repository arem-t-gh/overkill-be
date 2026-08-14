# TLDR:
# - a dedicated service ACCOUNT (deployer) exists in GCP holding the
#   permissions CI needs
# - our repo's GitHub Actions workflows ACT AS that account — GHA do the
#   work, the service account is the identity they borrow while doing it
# - WIF is the layer that makes the borrowing possible without any stored
#   key: GCP verifies "this run is really from our repo" per job
# #################################################################################### 
# Workload Identity Federation (WIF): lets GitHub Actions log in to GCP
# with no password or key stored anywhere. Instead of GitHub holding a GCP
# credential, GCP is taught to recognize GitHub's own signed proof of
# "this is a workflow run from your repo" and trade it for short-lived
# (~1 hour) GCP access that dies with the job.
#
# Four pieces, in order below:
#   1. pool     — the container GCP keeps outside identities in
#   2. provider — the rules for recognizing GitHub's proof
#   3. deployer — the GCP service account CI acts as
#   4. binding  — ties it together: "verified runs from our repo may act
#                 as the deployer"
# After that: IAM grants deciding what the deployer can actually DO.

# (1) The container. GCP requires all outside (non-Google) identities to
# live in a "pool"; this one holds identities coming from GitHub.
# Teardown/rebuild gotcha: deleting a pool only moves it to a 30-day trash
# can, and its ID stays taken meanwhile. Rebuilding within that window
# fails with "already exists" — recover the trashed one with
# `gcloud iam workload-identity-pools undelete github --location=global`.
resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions"

  depends_on = [google_project_service.apis]
}

# (2) The recognition rules. Every workflow run carries a signed note from
# GitHub stating which repo/branch/workflow it is. This resource tells GCP:
# - who issues the notes (issuer_uri), so signatures can be verified
# - which facts from the note to keep (attribute_mapping)
# - which notes to accept at all (attribute_condition)
resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-oidc"
  display_name                       = "GitHub OIDC"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  # The facts we keep from GitHub's note:
  # - subject: required by GCP; names the exact run in audit logs
  # - repository: the fact filtered on below and matched in the binding (4)
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }

  # The security-critical line. GitHub signs notes for EVERY repo on
  # github.com — without this filter, a stranger's workflow would pass
  # verification too. GCP knows it, and refuses to create a GitHub
  # provider that has no condition.
  attribute_condition = "assertion.repository == \"${var.github_repository}\""
}

# (3) The GCP account CI acts as. Deliberately separate from the runtime SA
# (overkill-be-run):
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

# (4) The tie that makes 1–3 mean something: identities from the pool (1)
# that passed the rules (2) AND whose repository fact matches ours may act
# as the deployer (3). Until this exists, verified GitHub runs can log in
# but can't be anyone — i.e. can't do anything.
# principalSet:// means "everyone matching this fact" — any branch or
# workflow of the repo qualifies; restricting deploys to main happens
# later, in the workflow file's trigger.
resource "google_service_account_iam_member" "deployer_wif" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repository}"
}

# Growing CI's powers only ever adds grants below this line (adding grants to the SA)
# ...the trust pieces (1-4) above stay untouched no matter what the pipeline learns to do.
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

# The two values the GitHub workflow's login step needs. Neither is a
# secret — they're names, not credentials; they go in the workflow file
# as plain text.
# Outputs exist precisely so values Terraform computed during apply can be read back out and fed to whatever needs them:
output "wif_provider_name" {
  value = google_iam_workload_identity_pool_provider.github.name
}

output "deployer_sa_email" {
  value = google_service_account.deployer.email
}
