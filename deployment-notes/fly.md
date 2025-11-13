# 🚀 **FLY.IO DEPLOYMENT**

## Why Fly.io?
- 🆓 **3 free VMs** with 256MB RAM each
- 🗄️ **Free PostgreSQL** (1GB storage)
- 🌐 **Global edge deployment**
- 🐋 **True Docker support**

## Deploy Commands:
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Deploy your app
flyctl launch --copy-config --name fulfil-product-importer
flyctl postgres create --name fulfil-db
flyctl postgres attach fulfil-db
flyctl redis create --name fulfil-redis
flyctl deploy

# Your app will be live at: https://fulfil-product-importer.fly.dev
```

## Fly.toml Configuration:
```toml
app = "fulfil-product-importer"
primary_region = "sjc"

[build]

[env]
  CHUNK_SIZE = "500"
  MAX_FILE_SIZE = "104857600"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256

[[statics]]
  guest_path = "/app/frontend"
  url_prefix = "/"
```