# Archive source code for Lambda deployment
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = var.output_zip_path

  # Exclude cache and other unnecessary files
  excludes = [
    "__pycache__",
    "**/__pycache__/**",
    "*.pyc",
    "**/*.pyc",
    ".pytest_cache",
    "**/.pytest_cache/**",
  ]
}
