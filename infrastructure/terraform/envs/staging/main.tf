terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.20"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Landing Zone Bucket for staging
resource "google_storage_bucket" "landing_zone" {
  name          = "${var.project_id}-staging-landing"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
}
