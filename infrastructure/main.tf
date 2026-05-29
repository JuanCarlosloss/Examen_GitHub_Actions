terraform {
  required_version = ">= 1.0.0"
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

resource "local_file" "welcome" {
  content  = "Welcome to the monorepo infrastructure! Env: ${var.environment}"
  filename = "${path.module}/welcome.txt"
}
