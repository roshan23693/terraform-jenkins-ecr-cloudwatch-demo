#!/bin/bash
set -euxo pipefail
exec > >(tee -a /var/log/jenkins-bootstrap.log) 2>&1
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y fontconfig openjdk-21-jre git docker.io awscli curl python3
systemctl enable --now docker
install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key -o /etc/apt/keyrings/jenkins-keyring.asc
echo "deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" > /etc/apt/sources.list.d/jenkins.list
apt-get update
apt-get install -y jenkins
usermod -aG docker jenkins
systemctl enable jenkins
systemctl restart jenkins
snap install amazon-ssm-agent --classic || true
systemctl enable --now snap.amazon-ssm-agent.amazon-ssm-agent.service || true
echo "Jenkins bootstrap completed at $(date -Is)" >> /var/log/jenkins-bootstrap.log
