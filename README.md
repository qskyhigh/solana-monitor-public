
# Solana Monitor

This project monitors Solana validator metrics using Docker and Docker Compose. It also integrates with Prometheus and Grafana for visualization.

## Prerequisites

- **Docker**: Container management
- **Docker Compose**: Multi-container orchestration
- **Git**: To clone the repository

## Building the Project

### 1. Install Docker and Docker Compose

Set up Docker by adding the official Docker repository and installing the required packages.

#### Install Docker:

Follow the official [Docker installation guide](https://docs.docker.com/engine/install/ubuntu/) for more details.

```bash
# Update packages and install dependencies
sudo apt-get update
sudo apt-get install ca-certificates curl

# Add Docker's official GPG key and set up the repository
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```
```bash
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
#### Install Docker Compose:

```shell
sudo curl -L https://github.com/docker/compose/releases/download/v2.29.7/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Clone the Repository
Download the project source code:
```bash
git clone https://github.com/qskyhigh/solana-monitor-public
cd solana-monitor-public
```

### 3. Build and Start the Application
Use Docker Compose to build the project and run the services in the background:
```bash
docker-compose build --no-cache
docker-compose up -d
```

## Grafana Cloud API Token Configuration
To connect Prometheus and Loki with Grafana Cloud, you need to generate your own API tokens and update the relevant configuration files.
### 1. Prometheus Configuration (`prometheus.yml`)

In the `prometheus.yml` file, replace the `username` and `password` with your own Grafana Cloud Prometheus API credentials.
```yml
remote_write:
- url: https://prometheus-prod-13-prod-us-east-0.grafana.net/api/prom/push
  basic_auth:
    username: YOUR_USERNAME
    password: YOUR_API_TOKEN
```

### 2. Loki Configuration (`promtail.yml`)
In the `promtail.yml` file, replace the `username` and `token` with your own Grafana Cloud Loki credentials.
```yml
clients:
  - url: https://YOUR_USERNAME:YOUR_API_TOKEN@logs-prod-006.grafana.net/loki/api/v1/push
```

#### How to Obtain API Tokens
1. Log in to your Grafana Cloud account.
2. Go to the API Keys section under Settings.
3. Generate API tokens for both Prometheus and Loki.
4. Use the generated tokens to replace the placeholders in `prometheus.yml` and `promtail.yml`.

## Grafana Dashboard Configuration

The dashboard can be imported from the docs/ directory to your Grafana instance<br>
  - Default is to utilize a label applied by the collector `host: solana-monitor-testnet` (can be editted to match your environment)

## Testing
You can check the running Docker containers with:
```bash
docker ps
```
Once the containers are up, access Grafana to visualize Solana metrics. For more details on the dashboard configuration, refer to the provided Grafana screenshot:
<img src="https://i.ibb.co/7kc3L8g/dqskyhigh-grafana.png" alt="dqskyhigh-grafana" border="0" style="width:100%;">

### Node Exporter Metrics

To monitor system-level metrics such as CPU, memory, and disk usage, you can use the **Node Exporter**.

You can download and import the Node Exporter dashboard with **ID 1860** from Grafana's dashboard library:

1. Go to Grafana and navigate to **Dashboards** > **Import**.
2. Enter the **Dashboard ID: `1860`** and click **Load**.
3. Select your Prometheus datasource and click **Import**.

This will provide a comprehensive overview of your system's performance using Node Exporter metrics.

### 
If you found this project helpful, feel free to support by donating SOL to my wallet.

**SOL Wallet Address**: `FNu9BCwCmgSmeCa56LCAErPBNeAdgnQJsBrrLgVbbMKt`

<img src="https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png" alt="Buy Me A Coffee">