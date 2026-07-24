# A secret is a named container plus versioned payloads (like a tiny git repo
# for one value) — the secret itself holds no data, each added version does.
resource "google_secret_manager_secret" "db_uri" {
  project   = var.project_id
  secret_id = "db-uri"

  # Where GCP stores the secret's payload replicas. auto = let Google pick;
  # fine here, only matters under data-residency requirements.
  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# The actual payload. Cloud Run connects through the Cloud SQL connector,
# which exposes a Unix socket inside the container instead of a host:port —
# hence the @/dbname?host=/cloudsql/... form rather than @host:5432/dbname.
# connection_name resolves to "<project>:<region>:<instance>".
resource "google_secret_manager_secret_version" "db_uri" {
  secret = google_secret_manager_secret.db_uri.id
  secret_data = format(
    "postgresql+asyncpg://%s:%s@/%s?host=/cloudsql/%s",
    google_sql_user.app.name,
    random_password.db_user.result,
    google_sql_database.app.name,
    google_sql_database_instance.overkill_be.connection_name,
  )
}
