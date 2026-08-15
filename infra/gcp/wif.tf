# TLDR:
# - dedicated service ACCOUNTS exist in GCP holding the permissions CI
#   needs (gha_deployer.tf, gha_terraformer.tf)
# - our repo's GitHub Actions workflows ACT AS those accounts — GHA do the
#   work, the service account is the identity they borrow while doing it
# - WIF (this file) is the layer that makes the borrowing possible without
#   any stored key: GCP verifies "this run is really from our repo" per job
# ####################################################################################
# Workload Identity Federation (WIF): lets GitHub Actions log in to GCP
# with no password or key stored anywhere. Instead of GitHub holding a GCP
# credential, GCP is taught to recognize GitHub's own signed proof of
# "this is a workflow run from your repo" and trade it for short-lived
# (~1 hour) GCP access that dies with the job.

# This file is the trust layer — it changes for new PROOF rules, never for
# new powers; those grow grant-by-grant in the gha_* files.

# The pieces, across files:
#   1. pool     (here)              — the container GCP keeps outside identities in
#   2. provider (here)              — the rules for recognizing GitHub's proof
#   3. the identities CI acts as    — one SA per pipeline, narrowest possible powers:
#        gha_X.tf    — does X
#   4. bindings (in those files)    — tie each SA to who may become it via membership


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
  # - repository: the fact filtered on below and matched in the SA bindings
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

# Consumed by the GitHub workflows' login step; a name, not a credential.
# Outputs exist precisely so values Terraform computed during apply can be
# read back out and fed to whatever needs them:
output "wif_provider_name" {
  value = google_iam_workload_identity_pool_provider.github.name
}
