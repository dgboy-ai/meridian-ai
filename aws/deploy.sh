#!/usr/bin/env bash
set -euo pipefail

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID}"
ECR_REPOSITORY="meridian-ai"
ECS_CLUSTER="meridian-ai-production"
ECS_SERVICE="meridian-ai-backend"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "=== Building Docker image ==="
docker build -t "${ECR_REPOSITORY}:${IMAGE_TAG}" .

echo "=== Logging in to ECR ==="
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "=== Tagging image ==="
docker tag "${ECR_REPOSITORY}:${IMAGE_TAG}" \
  "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"

echo "=== Pushing image to ECR ==="
docker push "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"

echo "=== Registering new task definition ==="
TASK_DEF_ARN=$(aws ecs register-task-definition \
  --cli-input-json file://aws/ecs-task-definition.json \
  --region "${AWS_REGION}" \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)

echo "Task definition registered: ${TASK_DEF_ARN}"

echo "=== Updating ECS service ==="
aws ecs update-service \
  --cluster "${ECS_CLUSTER}" \
  --service "${ECS_SERVICE}" \
  --task-definition "${TASK_DEF_ARN}" \
  --force-new-deployment \
  --region "${AWS_REGION}" \
  --query 'service.serviceName' \
  --output text

echo "=== Waiting for service to stabilize ==="
aws ecs wait services-stable \
  --cluster "${ECS_CLUSTER}" \
  --services "${ECS_SERVICE}" \
  --region "${AWS_REGION}" && \
  echo "Service is stable and running." || \
  echo "Warning: Wait timed out. Check AWS console for status."

echo "=== Deploy complete ==="
