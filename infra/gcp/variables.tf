variable "project_id" {
  description = "GCP project ID to deploy into"
  type        = string
}

# The single source of naming: every app-scoped resource name derives from
# this (see locals below), so pointing this template at a different app is a
# one-variable change, not a find-and-replace.
variable "app_name" {
  description = "Base name all app-scoped GCP resource names derive from"
  type        = string
  default     = "overkill-be"
}

# Matches the app's ENV convention (local/dev/stage/prod — see
# logging_config.py): anything non-"local" is a cloud stage.
variable "app_env" {
  description = "Value for the container's ENV variable"
  type        = string
  default     = "dev"
}

variable "container_port" {
  description = "Port the container listens on (uvicorn's port)"
  type        = number
  default     = 8000
}

variable "image_name" {
  description = "Image name within the Artifact Registry repository"
  type        = string
  default     = "api"
}

# "manual-test" is the manually-pushed bootstrap image; the CI/CD phase
# replaces this with a CI-supplied value (git SHA) per deploy.
variable "image_tag" {
  description = "Tag of the image Cloud Run deploys"
  type        = string
  default     = "manual-test"
}

# db_name / db_user_name predate the app_name-derived naming scheme, so they
# are standalone values rather than derived — deriving them now would rename
# (destroy + recreate) the live database and user.
variable "db_name" {
  description = "Name of the application database on the Cloud SQL instance"
  type        = string
  default     = "overkill"
}

variable "db_user_name" {
  description = "Name of the application's database user"
  type        = string
  default     = "overkill_app"
}

variable "db_version" {
  description = "Cloud SQL database engine version"
  type        = string
  default     = "POSTGRES_16"
}

variable "db_tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-f1-micro"
}

locals {
  service_name     = "${var.app_name}-api"
  db_instance_name = "${var.app_name}-db"
  runtime_sa_id    = "${var.app_name}-run"
  deployer_sa_id   = "${var.app_name}-deployer"
}

variable "region" {
  description = "Default GCP region for regional resources"
  type        = string
  default     = "asia-southeast1"
}

# owner/name, exactly as it appears on github.com — this string is the WIF
# trust boundary (see wif.tf), so a repo rename silently breaks CI auth
# until this value is updated to match.
variable "github_repository" {
  description = "GitHub repository allowed to authenticate via WIF"
  type        = string
  default     = "arem-t-gh/overkill-be"
}

# Public by nature (ships in frontend apps) — plain variable, plain env var.
variable "supabase_url" {
  description = "Supabase project URL (https://<project>.supabase.co)"
  type        = string
}

# The service role key (the app calls auth.admin.* which requires it):
# - sensitive = true redacts it from plan/apply CLI output
# - it still lands in state — which is fine, state lives in the private
#   GCS bucket, and this is one of the reasons state is never committed
variable "supabase_key" {
  description = "Supabase service role key"
  type        = string
  sensitive   = true
}
