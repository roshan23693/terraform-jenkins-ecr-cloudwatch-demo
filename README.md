# Terraform + Jenkins + Docker + ECR + EC2 + CloudWatch demo

This project uses Terraform to create two Ubuntu 24.04 EC2 instances in **ap-south-1**:
- Jenkins EC2: Jenkins, Java 21, Docker, Git and AWS CLI.
- Application EC2: Docker, Systems Manager Agent and CloudWatch Agent.

Terraform also creates an ECR repository, IAM roles and instance profiles, security groups, a CloudWatch log group and a CPU alarm. Jenkins uses its EC2 instance role (no saved AWS access keys) to push images to ECR and send deployment commands to the app EC2 through Systems Manager.

## Architecture

Developer -> GitHub -> webhook -> Jenkins EC2 -> Docker build -> ECR -> SSM Run Command -> Application EC2 -> Docker container.

CloudWatch Agent on the application host reports memory and disk metrics and forwards its bootstrap log. EC2 CPU is monitored with a CloudWatch alarm.

## Before you start: costs and security

This creates two running EC2 instances and EBS volumes, plus ECR and CloudWatch resources. AWS charges may apply. Check current pricing for ap-south-1. Destroy the project when finished.

The Jenkins UI (8080) is restricted to your IP. The demo app HTTP port (80) is public by default; set `app_http_cidr` to your own IP/32 to restrict it. SSH is disabled by default. Do not open Jenkins or SSH to the whole internet. This is a learning setup, not a production design.

## 1. Prerequisites

Install Terraform 1.6+, AWS CLI v2 and Git on your computer, or use AWS CloudShell. This starter configuration expects the AWS account to have its default VPC and at least one default subnet in ap-south-1. If you deleted the default VPC, recreate it or adapt the networking resources before applying.\n\nConfigure an AWS identity with permission to create EC2, IAM, ECR, SSM, CloudWatch and security groups:

```bash
aws configure
aws sts get-caller-identity
```

## 2. Configure Terraform

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`. Replace `my_ip_cidr` with your current public IPv4 address plus `/32`, e.g. `198.51.100.25/32` is only an example and must not be copied as your real address.

Optional: set `app_http_cidr` to your IP/32 if the demo website should not be public. Keep `aws_region = "ap-south-1"`.

## 3. Create infrastructure

Run from the `terraform` directory:

```bash
terraform init
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
```

Review the plan and type `yes`. Terraform creates both EC2 instances and supporting AWS resources. Software installation continues through EC2 user data after Terraform finishes.

Get outputs:

```bash
terraform output
terraform output -raw jenkins_url
terraform output -raw app_instance_id
terraform output -raw ecr_repository_url
```

## 4. Finish Jenkins first-time setup

Open the `jenkins_url` output in your browser. Wait a few minutes if it is not ready yet.

Retrieve the initial password by connecting to the Jenkins EC2 using Systems Manager Session Manager (recommended) and running:

```bash
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

If the instance is not yet listed as a managed node, wait for SSM Agent startup. You can also inspect the EC2 system log or `/var/log/jenkins-bootstrap.log`. Complete the Jenkins wizard, install suggested plugins and create an admin user.

## 5. Push the project to GitHub

Create a GitHub repository. From the project root (one level above `terraform/`):

```bash
git init
git add .
git commit -m "Add Terraform Jenkins ECR demo"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/jenkins-ecr-cloudwatch-demo.git
git push -u origin main
```

Do not commit `terraform.tfvars`, state files or credentials. `.gitignore` excludes them.

## 6. Set the application EC2 ID in Jenkinsfile

From the Terraform directory:

```bash
terraform output -raw app_instance_id
```

Copy the returned instance ID. In the root `Jenkinsfile`, replace:

```groovy
APP_INSTANCE_ID = 'REPLACE_WITH_APP_INSTANCE_ID'
```

with the actual ID, e.g. `i-0123456789abcdef0`. Commit and push the changed Jenkinsfile.

## 7. Create the Jenkins pipeline job

In Jenkins:
1. Click **New Item**, enter `jenkins-ecr-cloudwatch-demo`, select **Pipeline**.
2. Under Pipeline, choose **Pipeline script from SCM**.
3. Select Git and enter your GitHub repository URL.
4. Set branch to `*/main`, Script Path to `Jenkinsfile`.
5. Save.

For a private GitHub repository, configure a GitHub credential in Jenkins and select it for SCM checkout. For a public repository, credentials are not required.

Click **Build Now** once to test. Jenkins builds the image, authenticates to ECR using its EC2 role, pushes the image, then calls SSM to deploy it to the application EC2.

## 8. Configure GitHub webhook

In GitHub repository **Settings -> Webhooks -> Add webhook**:
- Payload URL: `http://JENKINS_PUBLIC_IP:8080/github-webhook/`
- Content type: `application/json`
- Choose **Just the push event**.

Install the Jenkins GitHub integration plugin if needed. In the pipeline job, enable **GitHub hook trigger for GITScm polling**.

The HTTP webhook is only for a temporary lab. For internet-facing use, put Jenkins behind HTTPS, authenticate it and restrict access.

## 9. Test end-to-end automation

Edit `app/index.html`, commit and push:

```bash
git add app/index.html
git commit -m "Change demo page"
git push
```

GitHub webhook triggers Jenkins. Jenkins checks out the code, builds a new Docker image, pushes it to ECR and deploys it on the application EC2. Refresh the `app_url` output in your browser.

## 10. CloudWatch checks

In AWS Console, select ap-south-1:
- CloudWatch -> Metrics -> namespace `JenkinsECRDemo/EC2`: memory and disk metrics from the app EC2 agent.
- CloudWatch -> Log groups -> `/jenkins-ecr-demo/application`: app bootstrap log.
- CloudWatch -> Alarms: app EC2 CPU alarm.

The CPU alarm is created without an email action. To get email notifications, create an SNS topic, subscribe and confirm your email, then add that topic as an alarm action.

## Troubleshooting

- **Jenkins UI not loading:** verify port 8080, your current public IP CIDR, and `/var/log/jenkins-bootstrap.log`. If your ISP changes your IP, update `my_ip_cidr` and run `terraform apply`.
- **Docker permission error in Jenkins:** user data adds Jenkins to the Docker group; restart Jenkins or reboot the instance after bootstrap.
- **ECR push denied:** verify `aws sts get-caller-identity` from a Jenkins build and confirm the Jenkins instance profile is attached.
- **SSM deployment fails:** confirm the app EC2 is online in Systems Manager managed nodes, its IAM profile is attached, and it has outbound access to AWS endpoints.
- **Website not loading:** confirm pipeline succeeded, port 80 is allowed, and `sudo docker ps` on the app instance shows `demo-app`.

## Clean up

From `terraform/`:

```bash
terraform destroy
```

Review and type `yes`. ECR is configured for force deletion in this demo, so its images are also deleted.

## Notes / production improvements

This lab uses the default VPC and public EC2 instances for simplicity. Production should use private subnets, an ALB with HTTPS, remote Terraform state in S3 with locking, tighter IAM permissions, a secure Jenkins endpoint, and separate environments.
