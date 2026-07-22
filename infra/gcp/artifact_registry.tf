resource "google_artifact_registry_repository" "overkill_be" {
  project       = var.project_id
  location      = var.region
  repository_id = "overkill-be"
  format        = "DOCKER"
  description   = "Container images for the overkill-be API"

  # this resource technically waits for all the APIs to finish
  # that should appear in the terraform logs when creating resources
  depends_on = [google_project_service.apis]
}