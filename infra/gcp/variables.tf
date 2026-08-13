variable "project_id" {
  description = "GCP project ID to deploy into"
  type        = string
}

variable "region" {
  description = "Default GCP region for regional resources"
  type        = string
  default     = "asia-southeast1"
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
