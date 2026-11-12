terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# ---------- things that already exist (data sources) ----------
data "aws_caller_identity" "me" {}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

# ---------- firewalls ----------
resource "aws_security_group" "alb" {
  name   = "${var.project}-alb"
  vpc_id = data.aws_vpc.default.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "app" {
  name   = "${var.project}-app"
  vpc_id = data.aws_vpc.default.id

  ingress {
    from_port       = 8501
    to_port         = 8501
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id] # only the load balancer may connect
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"] # servers call NVIDIA, Qdrant, the web
  }
}

# ---------- permissions for the servers ----------
resource "aws_iam_role" "app" {
  name = "${var.project}-ec2-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.app.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore" # enables Session Manager
}

resource "aws_iam_role_policy" "read_params" {
  name = "read-app-params"
  role = aws_iam_role.app.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"]
      Resource = [
        "arn:aws:ssm:${var.region}:${data.aws_caller_identity.me.account_id}:parameter/${var.project}",
        "arn:aws:ssm:${var.region}:${data.aws_caller_identity.me.account_id}:parameter/${var.project}/*",
      ]
    }]
  })
}

resource "aws_iam_instance_profile" "app" {
  name = "${var.project}-profile"
  role = aws_iam_role.app.name
}

# ---------- the server recipe ----------
resource "aws_launch_template" "app" {
  name_prefix            = "${var.project}-"
  image_id               = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.app.id]
  update_default_version = true

  iam_instance_profile {
    name = aws_iam_instance_profile.app.name
  }

  metadata_options {
    http_tokens = "required" # IMDSv2 only, more secure
  }

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size = 20
      volume_type = "gp3"
    }
  }   

  user_data = base64encode(templatefile("${path.module}/user_data.sh.tftpl", {
    project       = var.project
    region        = var.region
    repo_url      = var.repo_url
    repo_branch   = var.repo_branch
    backend_app   = var.backend_app
    python_path   = var.python_path
    frontend_file = var.frontend_file
  }))

  tag_specifications {
    resource_type = "instance"
    tags          = { Name = var.project }
  }
}

# ---------- load balancer ----------
resource "aws_lb" "app" {
  name               = "${var.project}-alb"
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.default.ids
  idle_timeout       = var.alb_idle_timeout
}

resource "aws_lb_target_group" "app" {
  name     = "${var.project}-tg"
  port     = 8501
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id

  health_check {
    path                = "/_stcore/health"
    matcher             = "200"
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 5
  }

  stickiness {
    type            = "lb_cookie"
    enabled         = true
    cookie_duration = 86400
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# ---------- the group that keeps N servers alive ----------
resource "aws_autoscaling_group" "app" {
  name                      = "${var.project}-asg"
  min_size                  = var.instance_count
  max_size                  = var.instance_count
  desired_capacity          = var.instance_count
  vpc_zone_identifier       = data.aws_subnets.default.ids
  target_group_arns         = [aws_lb_target_group.app.arn]
  health_check_type         = "ELB"
  health_check_grace_period = 600 # first boot installs packages, so give it time

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = var.project
    propagate_at_launch = true
  }
}