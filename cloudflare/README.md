## Cloudflare Worker Deployment

This directory contains a Cloudflare Worker that serves the curlpad installation script.

### Prerequisites

- [Cloudflare account](https://dash.cloudflare.com/sign-up)
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/)

Install Wrangler:

```bash
npm install -g wrangler
```

### Authentication

Login to Cloudflare:

```bash
wrangler login
```

### Deployment

From the `cloudflare/` directory:

```bash
cd cloudflare
wrangler deploy
```

This will deploy the worker and give you a URL like:

```
https://curlpad-installer.gossorg.workers.dev
```

### Usage

Once deployed, users can install curlpad with:

```bash
curl -fsSL curlpad-installer.gossorg.in/install.sh | bash
```

Or download and inspect first:

```bash
curl -fsSL curlpad-installer.gossorg.in/install.sh -o install.sh
chmod +x install.sh
./install.sh
```

### Custom Domain (Optional)

To use a custom domain:

1. Add your domain to Cloudflare
2. Update `wrangler.toml` routes section
3. Deploy with `wrangler deploy`

Example for `install.curlpad.dev`:

```toml
[[routes]]
pattern = "install.curlpad.dev/*"
zone_name = "curlpad.dev"
```

### Endpoints

- `GET /` or `GET /install.sh` - Serves the installation script
- `GET /health` - Health check endpoint (returns JSON)

### Local Development

Test locally before deploying:

```bash
wrangler dev
```

Then access at `http://localhost:8787/install.sh`

### Update Worker

After making changes to `worker.js`:

```bash
wrangler deploy
```

### Configuration

Edit `wrangler.toml` to customize:
- Worker name
- Compatibility date
- Routes (for custom domains)
- Environment variables

