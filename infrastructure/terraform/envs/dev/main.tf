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

# Landing Zone Bucket for raw dataset ingestion
resource "google_storage_bucket" "landing_zone" {
  name          = "${var.project_id}-landing-zone"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "databricks-lakehouse-repo"
  description   = "Docker repository for Lakehouse pipelines"
  format        = "DOCKER"
}
