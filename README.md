# Theorem Marketplace

A blockchain-based platform for declaring, discovering, and solving mathematical theorems with crypto bounties. Users can declare bounties on unproven theorems in Lean, while others can submit proofs to claim the bounties.

**Live site:** https://theorem-marketplace.com

## Architecture

The system consists of 5 Docker containers:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         theorem-marketplace network                      │
│                                                                         │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐   │
│  │ theorem-        │     │ safe-verify-    │     │ chainlink       │   │
│  │ marketplace     │────▶│ adapter         │◀────│ (oracle)        │   │
│  │ (Flask app)     │     │ (Lean verifier) │     │                 │   │
│  │ :5000           │     │ :8080           │     │ :6688           │   │
│  └────────┬────────┘     └─────────────────┘     └────────┬────────┘   │
│           │                                               │            │
│           ▼                                               ▼            │
│  ┌─────────────────┐                            ┌─────────────────┐   │
│  │ theorem_postgres│                            │ cl-postgres     │   │
│  │ :5433           │                            │ :5432           │   │
│  └─────────────────┘                            └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                          ┌─────────────────┐
                          │ Ethereum        │
                          │ (Sepolia)       │
                          └─────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- An Ethereum RPC provider (Alchemy, Infura, etc.)
- AWS account with SES configured (for email notifications)
- Domain name with DNS configured (for production)

### 1. Clone the repository

```bash
git clone --recurse-submodules https://github.com/wadimiusz/theorem-marketplace.git
cd theorem-marketplace
```

If you already cloned without submodules:
```bash
git submodule update --init --recursive
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in all required values:

| Variable | Description |
|----------|-------------|
| `CL_POSTGRES_PASSWORD` | Password for Chainlink's PostgreSQL |
| `THEOREM_POSTGRES_PASSWORD` | Password for app's PostgreSQL |
| `CONTRACT_ADDRESS` | Deployed TheoremMarketplace contract |
| `HTTP_PROVIDER` | Ethereum RPC URL (e.g., Infura/Alchemy) |
| `ADMIN_EMAIL` | Email for contact form submissions |
| `SENDER_EMAIL` | Verified AWS SES sender email |
| `AWS_REGION` | AWS region for SES |
| `AWS_ACCESS_KEY_ID` | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials |

### 3. Configure Chainlink node

```bash
cp chainlink/secrets.toml.example chainlink/secrets.toml
```

Edit `chainlink/secrets.toml` with your passwords, and update `chainlink/config.toml` with your Alchemy/Infura API key.

See [chainlink/README.md](chainlink/README.md) for detailed setup instructions.

### 4. Start the services

```bash
docker-compose up -d
```

### 5. Initialize Chainlink node

On first run, create an admin user:

```bash
docker exec -it chainlink chainlink admin login
```

Then add the verification job via the Chainlink UI at http://localhost:6688 using the spec in `chainlink/job-verify-proof.toml`.

### 6. Deploy the smart contract (if needed)

If you need to deploy a new instance of the TheoremMarketplace contract, use your preferred method (Remix, Hardhat, Foundry) with `TheoremMarketplace.sol`.

After deployment, update `CONTRACT_ADDRESS` in `.env`.

## Production Deployment (Google Cloud)

### Option A: Automated with Secret Manager (Recommended)

This approach stores all secrets in Google Cloud Secret Manager and automatically configures the VM on boot.

#### 1. Enable Secret Manager and store secrets

```bash
# Enable the API
gcloud services enable secretmanager.googleapis.com --project=lean-proof-checker

# Store all secrets (interactive prompts)
./scripts/store-secrets.sh
```

#### 2. Grant VM access to secrets

```bash
# Get your VM's service account
SA=$(gcloud compute instances describe theorem-marketplace \
  --zone=us-central1-b --format='get(serviceAccounts[0].email)')

# Grant access to all theorem-* secrets
for secret in theorem-cl-postgres-password theorem-postgres-password \
  theorem-contract-address theorem-http-provider theorem-admin-email \
  theorem-sender-email theorem-aws-region theorem-aws-access-key-id \
  theorem-aws-secret-access-key theorem-chainlink-keystore-password \
  theorem-infura-project-id; do
    gcloud secrets add-iam-policy-binding $secret \
      --member="serviceAccount:$SA" \
      --role="roles/secretmanager.secretAccessor" \
      --project=lean-proof-checker
done
```

#### 3. Set the startup script

```bash
gcloud compute instances add-metadata theorem-marketplace \
  --zone=us-central1-b \
  --metadata-from-file startup-script=scripts/vm-startup.sh
```

Now when the VM boots (or when you create a new VM from an image), it will automatically:
- Fetch secrets from Secret Manager
- Generate `.env` and `chainlink/secrets.toml`
- Start all Docker containers

### Option B: Manual Configuration

If not using Secret Manager, manually create `.env` and `chainlink/secrets.toml` as described in Quick Start.

### Nginx + SSL

Copy the nginx config and set up SSL with Certbot:

```bash
sudo cp nginx/theorem-marketplace.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/theorem-marketplace.conf /etc/nginx/sites-enabled/
sudo certbot --nginx -d theorem-marketplace.com -d www.theorem-marketplace.com
sudo systemctl reload nginx
```

### Container restart policy

The docker-compose.yml uses `restart: unless-stopped` for all services. For production, ensure Docker starts on boot:

```bash
sudo systemctl enable docker
```

## Project Structure

```
theorem-marketplace/
├── app.py                 # Flask application
├── sync_bounties.py       # Hourly blockchain sync job
├── TheoremMarketplace.sol # Smart contract
├── ABI.json               # Contract ABI
├── docker-compose.yml     # Container orchestration
├── Dockerfile             # App container definition
├── .env.example           # Environment template
├── chainlink/             # Chainlink node config
│   ├── config.toml
│   ├── secrets.toml.example
│   ├── job-verify-proof.toml
│   └── README.md
├── safe-verify-adapter/   # Git submodule - Lean proof verifier
├── nginx/                 # Nginx configuration
├── scripts/               # Deployment scripts
│   ├── store-secrets.sh   # Store secrets in GCP Secret Manager
│   └── vm-startup.sh      # VM boot script (fetches secrets, starts containers)
├── templates/             # Jinja2 HTML templates
├── static/                # CSS, JS, images
└── requirements.txt       # Python dependencies
```

## How It Works

1. **Declare a bounty**: A user submits a theorem (Lean code) and sends ETH to the smart contract
2. **Sync**: The `sync_bounties.py` cron job detects new bounties from blockchain events
3. **Submit proof**: A solver submits a proof via the web interface
4. **Verification request**: The smart contract emits an oracle request
5. **Chainlink picks it up**: The Chainlink node calls `safe-verify-adapter`
6. **Lean verification**: The adapter compiles and verifies the proof using SafeVerify
7. **Callback**: Chainlink calls back the contract with success/failure
8. **Payout**: If successful, the bounty is transferred to the solver

## Development

### Running locally (without Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_PASSWORD=...
export HTTP_PROVIDER=...
# ... etc

python app.py
```

### Pre-commit hooks

```bash
pip install pre-commit
pre-commit install
```

## License

MIT

## Contact

For questions or issues, use the contact form on the website or open a GitHub issue.
