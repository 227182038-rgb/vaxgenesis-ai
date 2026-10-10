# Audit 3.5 — IAM Roles for Service Accounts (IRSA)
#
# Creates AWS IAM roles for each Kubernetes service account so pods
# authenticate to AWS services (S3, RDS, Secrets Manager) via short-lived
# STS tokens instead of long-lived access keys.

# ============================================================
# OIDC provider (one per cluster — already created by EKS module)
# ============================================================

data "aws_eks_cluster" "vaxgenesis" {
  name = module.eks.cluster_name
}

data "aws_iam_openid_connect_provider" "eks" {
  url = data.aws_eks_cluster.vaxgenesis.identity[0].oidc[0].issuer
}

# ============================================================
# IAM policy: S3 access for artifacts bucket
# ============================================================

resource "aws_iam_policy" "s3_artifacts" {
  name        = "${var.project_name}-s3-artifacts"
  description = "Allow backend/worker pods to read/write the artifacts bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation",
        ]
        Resource = [aws_s3_bucket.artifacts.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
        ]
        Resource = ["${aws_s3_bucket.artifacts.arn}/*"]
      },
    ]
  })
}

# ============================================================
# IAM role for backend service account
# ============================================================

resource "aws_iam_role" "backend_irsa" {
  name = "${var.project_name}-backend-irsa"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = data.aws_iam_openid_connect_provider.eks.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${replace(data.aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub" = "system:serviceaccount:vaxgenesis:backend"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "backend_s3" {
  role       = aws_iam_role.backend_irsa.name
  policy_arn = aws_iam_policy.s3_artifacts.arn
}

# ============================================================
# IAM role for worker service account
# ============================================================

resource "aws_iam_role" "worker_irsa" {
  name = "${var.project_name}-worker-irsa"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = data.aws_iam_openid_connect_provider.eks.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${replace(data.aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub" = "system:serviceaccount:vaxgenesis:worker"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "worker_s3" {
  role       = aws_iam_role.worker_irsa.name
  policy_arn = aws_iam_policy.s3_artifacts.arn
}

# ============================================================
# IAM role: Secrets Manager read-only (for pulling DB password, API keys)
# ============================================================

resource "aws_iam_policy" "secrets_readonly" {
  name        = "${var.project_name}-secrets-readonly"
  description = "Allow pods to read specific secrets from AWS Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret",
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:*:secret:${var.project_name}/*",
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "backend_secrets" {
  role       = aws_iam_role.backend_irsa.name
  policy_arn = aws_iam_policy.secrets_readonly.arn
}

resource "aws_iam_role_policy_attachment" "worker_secrets" {
  role       = aws_iam_role.worker_irsa.name
  policy_arn = aws_iam_policy.secrets_readonly.arn
}

# ============================================================
# K8s service accounts annotated with IAM role ARN
# ============================================================

resource "kubernetes_service_account" "backend" {
  metadata {
    name      = "backend"
    namespace = "vaxgenesis"
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.backend_irsa.arn
    }
  }
}

resource "kubernetes_service_account" "worker" {
  metadata {
    name      = "worker"
    namespace = "vaxgenesis"
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.worker_irsa.arn
    }
  }
}
