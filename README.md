# Uptime Monitor

FastAPI service for checking HTTP and HTTPS endpoints on demand. Each check records the target's HTTP status, time to response headers, and any error in SQLite. The API returns `200` when it records a check, even if the target returned an error or could not be reached.

## Run locally

```bash
docker compose up --build -d
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/checks \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/"}'
curl -fsS 'http://127.0.0.1:8000/checks?limit=5'
```

Swagger UI: <http://127.0.0.1:8000/docs>. The Compose volume keeps the check history across container recreation. `docker compose down` stops the service; adding `-v` also deletes the history.

## Tests and CI

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The API tests use temporary SQLite files and stub external requests. GitHub Actions runs them on Python 3.12 and builds the Docker image after they pass.

## Deploy to AWS

The `infra/` configuration provisions an Ubuntu 24.04 EC2 instance, an encrypted root disk, and a VPC with internet access. Inbound traffic is limited to SSH from a single IPv4 address. Docker and Compose are installed on first boot.

You need Terraform, AWS credentials with permissions for the resources in `infra/main.tf` and the public SSM AMI parameter, and an SSH key pair. From the repository root:

```bash
cp infra/terraform.tfvars.example infra/terraform.tfvars
```

Set `ssh_cidr` to your public IPv4 address followed by `/32`, and update `ssh_public_key_path` if needed. Then review the plan before provisioning. EC2, EBS, and the public IPv4 address can incur charges.

```bash
terraform -chdir=infra init
terraform -chdir=infra plan -out=deploy.tfplan
terraform -chdir=infra apply deploy.tfplan
host=$(terraform -chdir=infra output -raw public_ip)
```

Use the private key that matches `ssh_public_key_path`. Transfer the committed application files over SSH so the VM does not need access to the private GitHub repository:

```bash
key="$HOME/.ssh/id_ed25519"
git archive HEAD Dockerfile .dockerignore docker-compose.yml requirements.txt main.py check.py database.py \
  | ssh -i "$key" "ubuntu@$host" 'mkdir -p uptime-monitor && tar -xf - -C uptime-monitor'
ssh -i "$key" "ubuntu@$host" \
  'sudo cloud-init status --wait && cd uptime-monitor && sudo docker compose up --build -d'
```

Keep the API on loopback. It makes requests to URLs supplied by the caller and is intended for trusted users. Open an SSH tunnel:

```bash
ssh -i "$key" -N -L 127.0.0.1:8080:127.0.0.1:8000 "ubuntu@$host"
```

From another terminal, run `curl -fsS http://127.0.0.1:8080/health` or open <http://127.0.0.1:8080/docs>.

Review later plans for instance replacement: a new Ubuntu AMI or a change to the bootstrap script can trigger it. Replacing the instance deletes the SQLite history on its root disk. When finished, run `terraform -chdir=infra destroy`. Keep Terraform state and your local variables outside Git.
