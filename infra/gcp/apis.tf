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

  # since they arent destroyed, recreating them shouldnt take long compared to the first run
  # For comparison, on your 1st run, it took 90sec for the APIs to be created
  # On 2nd run, only 4sec
  disable_on_destroy = false
}
