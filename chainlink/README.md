# Chainlink Node Configuration

This directory contains the configuration files for the Chainlink oracle node.

## Files

- `config.toml` - Node configuration (EVM chain, web server settings, etc.)
- `secrets.toml.example` - Template for secrets (copy to `secrets.toml`)
- `job-verify-proof.toml` - The oracle job specification for proof verification

## Setup

### 1. Create secrets.toml

```bash
cp secrets.toml.example secrets.toml
```

Edit `secrets.toml` and fill in:
- `Keystore` password (used to encrypt the node's Ethereum wallet)
- `Database.URL` with your PostgreSQL password

### 2. Update config.toml

Replace `YOUR_ALCHEMY_API_KEY` with your actual Alchemy API key for Sepolia.

Alternatively, you can use other providers:
- Infura: `https://sepolia.infura.io/v3/YOUR_PROJECT_ID`
- QuickNode, Ankr, etc.

### 3. Start the Chainlink node

```bash
docker-compose up -d chainlink
```

### 4. Initialize the node

On first run, you'll need to create an admin user:

```bash
docker exec -it chainlink chainlink admin login
```

Follow the prompts to create your admin credentials.

### 5. Fund the node wallet

Get the node's Ethereum address:

```bash
docker exec chainlink chainlink keys eth list
```

Fund this address with:
- Sepolia ETH (for gas) - Get from a faucet
- LINK tokens (for oracle rewards) - Get from Chainlink faucet

### 6. Add the verification job

1. Access the Chainlink UI at http://localhost:6688
2. Log in with your admin credentials
3. Go to **Jobs** → **New Job**
4. Paste the contents of `job-verify-proof.toml`
5. Click **Create Job**

## Important Notes

- The `secrets.toml` file is gitignored - never commit it
- The node wallet private key is stored encrypted with your keystore password
- Back up your keystore password securely - losing it means losing access to the wallet
