# EC2 Instance for Self-Hosted Qdrant Vector Database
resource "aws_instance" "qdrant_ec2" {
  ami                         = "ami-0c7217cdde317cfec" # Ubuntu 22.04 LTS
  instance_type               = var.qdrant_instance_type
  subnet_id                   = aws_subnet.public_a.id
  vpc_security_group_ids      = [aws_security_group.qdrant_sg.id]
  associate_public_ip_address = true

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }

  user_data = <<-EOF
              #!/bin/bash
              set -e
              
              # Update package lists and install Docker
              apt-get update -y
              apt-get install -y docker.io
              systemctl start docker
              systemctl enable docker

              # Create persistent storage directory for Qdrant
              mkdir -p /qdrant/storage

              # Launch Qdrant container with persistent volume
              docker run -d \
                --name qdrant \
                --restart always \
                -p 6333:6333 \
                -p 6334:6334 \
                -v /qdrant/storage:/qdrant/storage \
                qdrant/qdrant:latest
              EOF

  tags = {
    Name        = "qdrant-vector-db"
    Environment = var.environment
    Service     = "VectorDB"
  }
}
