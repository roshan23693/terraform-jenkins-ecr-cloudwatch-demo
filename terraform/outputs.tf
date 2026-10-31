output "jenkins_public_ip" { value = aws_instance.jenkins.public_ip }
output "jenkins_url" { value = "http://${aws_instance.jenkins.public_ip}:8080" }
output "app_public_ip" { value = aws_instance.app.public_ip }
output "app_url" { value = "http://${aws_instance.app.public_ip}" }
output "app_instance_id" { value = aws_instance.app.id }
output "ecr_repository_url" { value = aws_ecr_repository.app.repository_url }
