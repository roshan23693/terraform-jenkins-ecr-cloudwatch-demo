pipeline {
  agent any
  options {\n    timestamps()\n    disableConcurrentBuilds()\n  }
  environment {
    AWS_REGION = 'ap-south-1'
    ECR_REPOSITORY = 'jenkins-ecr-demo'
    APP_INSTANCE_ID = 'REPLACE_WITH_APP_INSTANCE_ID'
    IMAGE_TAG = "${BUILD_NUMBER}"
  }
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Validate') {
      steps {
        sh 'git --version && docker --version && aws --version && aws sts get-caller-identity'
      }
    }
    stage('Build image') {
      steps {
        script {
          env.ACCOUNT_ID = sh(script: "aws sts get-caller-identity --query Account --output text", returnStdout: true).trim()
          env.ECR_REGISTRY = "${env.ACCOUNT_ID}.dkr.ecr.${env.AWS_REGION}.amazonaws.com"
          env.IMAGE_URI = "${env.ECR_REGISTRY}/${env.ECR_REPOSITORY}:${env.IMAGE_TAG}"
        }
        sh 'docker build -t "$IMAGE_URI" .'
      }
    }
    stage('Push to ECR') {
      steps {
        sh '''
          set -e
          aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"
          docker push "$IMAGE_URI"
          docker logout "$ECR_REGISTRY"
        '''
      }
    }
    stage('Deploy to app EC2 via SSM') {
      steps {
        sh '''
          set -e
          if [ "$APP_INSTANCE_ID" = "REPLACE_WITH_APP_INSTANCE_ID" ]; then
            echo "Replace APP_INSTANCE_ID with Terraform output app_instance_id."
            exit 1
          fi
          python3 scripts/deploy_ssm.py "$AWS_REGION" "$APP_INSTANCE_ID" "$IMAGE_URI"
        '''
      }
    }
  }
  post {
    always { sh 'docker image prune -f || true' }
    success { echo 'Docker image pushed to ECR and deployed successfully.' }
    failure { echo 'Pipeline failed. Check the failed stage and console output.' }
  }
}
