locals {
  enabled_apis = [
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "iam.googleapis.com",
    "compute.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
  ]
}

# https://docs.cloud.google.com/docs/terraform/understanding-apis-and-terraform#api_enablement_versus_resource_import_in_terraform

resource "google_project_service" "apis" {
  for_each = toset(local.enabled_apis)

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}
