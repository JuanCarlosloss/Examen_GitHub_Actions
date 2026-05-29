output "welcome_file_path" {
  value       = local_file.welcome.filename
  description = "The path where the welcome text is generated."
}
