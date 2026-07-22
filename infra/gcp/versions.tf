terraform {
  required_version = ">= 1.15.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0, < 7.0"
    }
  }

  # https://developer.hashicorp.com/terraform/language/backend#overview
  # Backend config can't reference variables — Terraform needs to know which
  # backend to connect to before it has loaded any .tf/.tfvars files or
  # resolved any variables, so these values must be literals.
  backend "gcs" {
    bucket = "overkill-be-dev-1-tfstate"
    prefix = "gcp"
  }
}
