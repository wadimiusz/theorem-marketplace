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
- An Ethereum RPC provider (Infura, Alchemy, etc.)
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

Edit `chainlink/secrets.toml`:
- Set `Keystore` to a password of your choice
- Set the Database `URL` password to match `CL_POSTGRES_PASSWORD` from `.env`
- **Important**: the DB host must be `cl-postgres` (the Docker service name), not `localhost`

Example:
```toml
[Password]
Keystore = 'your-keystore-password'

[Database]
URL = 'postgresql://postgres:YOUR_CL_POSTGRES_PASSWORD@cl-postgres:5432/postgres?sslmode=disable'
```

Update `chainlink/config.toml` — replace `YOUR_INFURA_PROJECT_ID` with your actual Infura project ID.

Create the API credentials file for the Chainlink web UI:
```bash
echo -e "your-email@example.com\nyour-password" > chainlink/api-credentials
chmod 644 chainlink/api-credentials
```

**Important**: Both `secrets.toml` and `api-credentials` must be readable by the `chainlink` user inside the container (not `chmod 600` as root).

### 4. Start the services

```bash
docker compose up -d
```

### 5. Initialize the database

On first run, the app database tables don't exist yet:

```bash
docker compose exec theorem-marketplace uv run flask db init
docker compose exec theorem-marketplace uv run flask db migrate -m "initial"
docker compose exec theorem-marketplace uv run flask db upgrade
```

Then sync existing bounties from the blockchain:

```bash
docker compose exec theorem-marketplace uv run python sync_bounties.py
```

### 6. Build SafeVerify dependencies

The safe-verify-adapter clones SafeVerify and runs `lake update` on startup, but does **not** run `lake build`. Without this, all proof verifications will fail silently (returning `success: false` with empty stderr). You must build manually after first startup:

```bash
docker exec safe-verify-adapter bash -c "cd /tmp/safeverify/SafeVerify && lake build Cli && lake build"
```

This compiles SafeVerify and its dependencies (especially `Cli`, which is needed by the verification runner). This step takes a few minutes and requires ~4GB RAM (swap is fine).

To verify it works:
```bash
curl -s -X POST http://localhost:8080/verify-proof \
  -H "Content-Type: application/json" \
  -d '{"theorem": "theorem test (n : Nat) : n+2 = n+2 :=\n  sorry", "proof": "theorem test (n : Nat) : n+2 = n+2 :=\n  rfl"}' | python3 -m json.tool
```

Should return `"success": true`.

### 7. Set up the Chainlink job

Access the Chainlink UI (via SSH tunnel for security):

```bash
ssh your-server -L 6688:localhost:6688
```

Then open http://localhost:6688, log in, go to **Jobs > New Job**, and paste the contents of `chainlink/job-verify-proof.toml`.

The job spec includes `externalJobID = "3a4fba02-995a-447c-88b7-3cd17c1527a8"` which must match the `jobId` passed to the TheoremMarketplace contract constructor. If you deploy a new contract with a different job ID, update this field.

### 8. Authorize the Chainlink node wallet

The Chainlink node's EVM wallet must be authorized on the Oracle contract to send fulfillment transactions. Find the wallet address in the Chainlink UI under **Keys > EVM**, then run:

```bash
PRIVATE_KEY=0xYOUR_ORACLE_OWNER_KEY uv run --with web3 python scripts/authorize_node.py
```

Edit `scripts/authorize_node.py` first if the node wallet address has changed.

### 9. Fund the node wallet

Send Sepolia ETH to the Chainlink node's EVM wallet address (found in the Chainlink UI under **Keys > EVM**). The node needs ETH to pay gas for `fulfill` transactions.

## Production Deployment (Vultr)

### 1. Provision a VPS

A 4 vCPU / 8GB RAM instance with swap is sufficient. The boot script should install Docker, Nginx, and Certbot. Vultr's Ubuntu 24.04 image works well.

Ensure the firewall allows ports 22 (SSH), 80 (HTTP), and 443 (HTTPS). Do **not** expose port 6688 (Chainlink UI) — access it via SSH tunnel instead.

### 2. Clone and configure

```bash
cd /opt
git clone --recurse-submodules https://github.com/wadimiusz/theorem-marketplace.git
cd theorem-marketplace
```

Follow steps 2-9 from Quick Start above.

### 3. Nginx + SSL

```bash
cp nginx/theorem-marketplace.conf /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/theorem-marketplace.conf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
certbot --nginx -d theorem-marketplace.com -d www.theorem-marketplace.com
```

### 4. DNS

Point your domain's A record to the server IP. If using email services (AWS SES, Proton Mail), ensure SPF records include all senders:

```
v=spf1 include:alias.proton.me include:amazonses.com mx ~all
```

### Container restart policy

The docker-compose.yml uses `restart: unless-stopped` for all services. Ensure Docker starts on boot:

```bash
systemctl enable docker
```

## Chainlink RPC Configuration

The Chainlink node (`chainlink/config.toml`) is configured to minimize RPC usage on free tiers:

- **FixedPrice gas estimator** — avoids batch RPC calls for gas estimation (free-tier RPC providers like DRPC limit batch sizes)
- **HistoryDepth = 15** — tracks ~3 minutes of block history instead of the default 50 (~10 minutes)
- **PollInterval = 60s** — polls every 60s instead of the default 30s
- **Infura as primary** with DRPC and PublicNode as SendOnly fallbacks for transaction broadcasting

DRPC's free tier is not suitable as a primary node (batch requests limited to 3, WebSocket connections drop after ~8 minutes).

## Key Addresses

| What | Address |
|------|---------|
| TheoremMarketplace contract | `0x95F6Adaa8bC4848D203bE0e5FAC2F2A2bAF29bA2` |
| Oracle contract | `0xc3e350a4Bc67c8e20e031121fF8fCc680809A9a3` |
| Chainlink job ID | `3a4fba02-995a-447c-88b7-3cd17c1527a8` |
| Network | Sepolia testnet (chain ID 11155111) |
| LINK token | `0x779877A7B0D9E8603169DdbD7836e478b4624789` |

## Project Structure

```
theorem-marketplace/
├── app.py                 # Flask application
├── sync_bounties.py       # Hourly blockchain sync job
├── TheoremMarketplace.sol # Smart contract source
├── ABI.json               # Contract ABI
├── docker-compose.yml     # Container orchestration
├── Dockerfile             # App container (uses uv)
├── pyproject.toml         # Python dependencies
├── uv.lock                # Locked dependency versions
├── .env.example           # Environment template
├── chainlink/             # Chainlink node config
│   ├── config.toml        # Node settings, EVM chain config, RPC providers
│   ├── secrets.toml.example
│   ├── job-verify-proof.toml  # DirectRequest job spec
│   └── README.md
├── safe-verify-adapter/   # Git submodule — Lean proof verifier
├── nginx/                 # Nginx reverse proxy config
├── scripts/
│   ├── authorize_node.py  # Authorize Chainlink wallet on oracle contract
│   ├── store-secrets.sh   # Store secrets in GCP Secret Manager (legacy)
│   └── vm-startup.sh      # GCP VM boot script (legacy)
├── templates/             # Jinja2 HTML templates
└── static/                # CSS, JS, images
```

## How It Works

1. **Declare a bounty**: A user submits a theorem (Lean code with `sorry` placeholders) and sends ETH to the smart contract
2. **Sync**: The `sync_bounties.py` cron job detects new bounties from blockchain events
3. **Submit proof**: A solver submits a proof (Lean code with all `sorry`s replaced) via the web interface
4. **Verification request**: The smart contract emits an oracle request via Chainlink
5. **Chainlink picks it up**: The Chainlink node calls `safe-verify-adapter`
6. **Lean verification**: The adapter compiles both files and runs SafeVerify to check the proof against the theorem
7. **Callback**: Chainlink calls back the contract with success/failure
8. **Payout**: If successful, the bounty ETH is transferred to the solver

## Troubleshooting

### Proof verification always returns `success: false`
SafeVerify dependencies are not built. Run:
```bash
docker exec safe-verify-adapter bash -c "cd /tmp/safeverify/SafeVerify && lake build Cli && lake build"
```

### Chainlink node prints help text and exits
The CLI syntax for Chainlink v2.20.0 is:
```
chainlink node -c /chainlink/config.toml -s /chainlink/secrets.toml start -a /chainlink/api-credentials
```
Note: `-c`/`-s` are flags on the `node` command (not `start`), and `start` is a subcommand that takes `-a`.

### Chainlink: "API credentials must be supplied"
Create `chainlink/api-credentials` with email on line 1 and password on line 2.

### Chainlink: "failed to read secrets file: permission denied"
The Chainlink container runs as user `chainlink`, not root. Ensure config files are readable:
```bash
chmod 644 chainlink/secrets.toml chainlink/config.toml chainlink/api-credentials
```

### Chainlink: "Batch of more than 3 requests" errors
Your RPC provider's free tier limits batch requests. Use `Mode = 'FixedPrice'` in `[EVM.GasEstimator]` to avoid batch calls.

### Database: "relation bounty does not exist"
Run Flask-Migrate to create tables (see step 5 in Quick Start).

## Development

### Running locally (without Docker)

```bash
uv sync
uv run flask db upgrade
uv run python app.py
```

### Pre-commit hooks

```bash
uv run pre-commit install
```

## License

MIT

## Contact

For questions or issues, use the contact form on the website or open a GitHub issue.
