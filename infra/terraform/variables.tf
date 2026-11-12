variable "project" {
  type    = string
  default = "rag-doc-chat"
}

variable "region" {
  type    = string
  default = "ap-south-1"
}

variable "instance_count" {
  type        = number
  default     = 1
  description = "How many servers to run"
  validation {
    condition     = var.instance_count >= 0 && var.instance_count <= 4
    error_message = "Keep instance_count between 0 and 4 to avoid surprise bills."
  }
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "repo_url" {
  type = string
}

variable "repo_branch" {
  type    = string
  default = "main"
}

variable "allowed_cidr" {
  type        = string
  description = "Who may open the app, like 203.0.113.7/32 (your IP)"
}

variable "backend_app" {
  type        = string
  description = "uvicorn target, like your_package.main:app"
}

variable "python_path" {
  type        = string
  default     = "."
  description = "Folder added to PYTHONPATH, like src"
}

variable "frontend_file" {
  type    = string
  default = "app.py"
}

variable "alb_idle_timeout" {
  type    = number
  default = 300
}