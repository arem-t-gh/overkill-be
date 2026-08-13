# Dedicated runtime identity for this service (least privilege):
# - the alternative is Cloud Run's project-wide default service account,
#   which comes with broad Editor-ish permissions shared by everything
# - a dedicated SA starts with zero permissions; the two grants below are
#   its entire capability surface
resource "google_service_account" "run_overkill_be" {
  project      = var.project_id
  account_id   = "overkill-be-run"
  display_name = "Runtime SA for overkill-be-api Cloud Run service"
}

# Same attached-IAM pattern as public_invoker, but targeting the secret:
# only this SA may read the payload, and only this one secret is readable.
resource "google_secret_manager_secret_iam_member" "run_db_uri" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.db_uri.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_overkill_be.email}"
}

# Per-secret IAM means per-secret grants: each new secret the service reads
# needs its own accessor binding — access never comes along for free.
resource "google_secret_manager_secret_iam_member" "run_supabase_key" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.supabase_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_overkill_be.email}"
}

# Lets the SA open connections through the Cloud SQL connector. Granted
# project-wide because Cloud SQL has no per-instance IAM (unlike secrets) —
# this is as narrow as this particular permission gets.
resource "google_project_iam_member" "run_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.run_overkill_be.email}"
}

resource "google_cloud_run_v2_service" "overkill_be" {
  name     = "overkill-be-api"
  location = var.region
  project  = var.project_id

  # The provider defaults this to true as a prod safety rail (blocks
  # `terraform destroy` from removing the service). We're iterating fast
  # while learning, so we want destroy to actually work.
  deletion_protection = false

  template {
    service_account = google_service_account.run_overkill_be.email

    containers {
      # Referencing the repository's own attribute (rather than hardcoding
      # "overkill-be" again) means Terraform infers this resource depends on
      # the repository existing first — no explicit depends_on needed here,
      # unlike the API dependency below.
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.overkill_be.repository_id}/api:manual-test"

      ports {
        container_port = 8000
      }

      env {
        name  = "ENV"
        value = "dev"
      }

      env {
        name  = "SUPABASE_URL"
        value = var.supabase_url
      }

      env {
        name = "SUPABASE_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.supabase_key.secret_id
            version = "latest"
          }
        }
      }

      # Resolved by Cloud Run at deploy time using the runtime SA's
      # credentials — the payload never appears in Terraform config or in
      # the service's visible env var definition, only inside the running
      # container. "latest" = whatever the newest enabled version is.
      env {
        name = "DB_URI"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_uri.secret_id
            version = "latest"
          }
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }

    # The Cloud SQL connector: mounts a Unix socket per listed instance
    # under /cloudsql/<connection_name>, matching the ?host=... in DB_URI.
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.overkill_be.connection_name]
      }
    }
  }

  # Everything here is a real dependency that carries no attribute reference,
  # so Terraform can't infer the ordering on its own:
  # - apis: same reason as artifact_registry.tf — run.googleapis.com must be
  #   enabled before the service can be created
  # - secret_version: the env block references the *secret* (its secret_id),
  #   which orders the secret itself — but not its payload; deploying before
  #   a version exists fails with "secret has no versions"
  # - secret_iam_member: the runtime SA must already be allowed to read the
  #   secret when Cloud Run resolves it at deploy time, or the revision
  #   fails with a permission error
  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_version.db_uri,
    google_secret_manager_secret_iam_member.run_db_uri,
    google_secret_manager_secret_version.supabase_key,
    google_secret_manager_secret_iam_member.run_supabase_key,
  ]
}

# Cloud Run services are private by default. This config makes it publicly
# invokable over the internet, same posture as the existing Railway
# deployment — access control happens at the app layer (Supabase auth),
# not at the network/IAM layer.
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.overkill_be.name

  role   = "roles/run.invoker"
  member = "allUsers"
}

# Does public_invoker get bound to overkill_be through the name? 
# Yes — project + location + name together are the identifying triple that 
# tells GCP's IAM system which specific Cloud Run service this roles/run.invoker grant targets.

# Think of it this way: It is an iam resource, a policy granting service so it has to be attached to something and not standalone

# But for most resources, Terraform would always just create the resource as is (Unless it's like an IAM that has to bind to something)