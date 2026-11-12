output "app_url" {
  value = "http://${aws_lb.app.dns_name}"
}

output "asg_name" {
  value = aws_autoscaling_group.app.name
}