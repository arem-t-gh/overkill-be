resource "google_sql_database_instance" "overkill_be" {
  project          = var.project_id
  region           = var.region
  name             = "overkill-be-db"
  database_version = "POSTGRES_16"

  # Cheapest available combination — no free tier exists for Cloud SQL at all:
  # - shared-core tiers like db-f1-micro only exist in the ENTERPRISE edition;
  #   without stating it, the API defaults to ENTERPRISE_PLUS and rejects the tier
  settings {
    # only ENTERPRISE and ENTERPRISE_PLUS
    edition = "ENTERPRISE"
    tier    = "db-f1-micro"
  }

  # Prevents `terraform destroy` from being blocked, same reasoning as
  # deletion_protection on the Cloud Run service — we're iterating while
  # learning, not running this in front of real users yet.
  deletion_protection = false

  depends_on = [google_project_service.apis]
}

# The instance is the server; the app connects to a named database on it —
# same split as POSTGRES_DB vs the postgres container in docker-compose.
resource "google_sql_database" "app" {
  project  = var.project_id
  instance = google_sql_database_instance.overkill_be.name
  name     = "overkill"
}

# Generated at apply time, never written in config:
# - lives only in Terraform state (private GCS bucket, not git) and Secret Manager
# - special = false because the password gets embedded in a connection URI;
#   URL-reserved characters (@ : / ?) would break parsing, and 32 alphanumeric
#   chars is already plenty of entropy
resource "random_password" "db_user" {
  length  = 32
  special = false
}

resource "google_sql_user" "app" {
  project  = var.project_id
  instance = google_sql_database_instance.overkill_be.name
  name     = "overkill_app"
  password = random_password.db_user.result
}
