# **Simple Faucet Application**

This project implements a simple **Django REST API** faucet application that allows customers to request free Sepolia ETH. The application includes rate-limiting and transaction statistics features, and it is fully containerized for easy deployment.

---

## **Features**

- **POST `/faucet/fund`:**
  - Transfers **0.0001 Sepolia ETH** to a specified wallet address.
  - Includes rate-limiting:
    - A user cannot request funds more than **once per minute** (default, configurable) from the same source IP or to the same destination wallet.
  - Returns a transaction ID upon success or an error message on failure.

- **GET `/faucet/stats`:**
  - Provides statistics for the last 24 hours:
    - The number of successful transactions.
    - The number of failed transactions.

- **Dockerized Deployment**:
  - Includes a `Dockerfile` and `docker-compose.yml` for building and deploying the application.

---

### **Architecture**
The application follows a distributed architecture:

- A Django app serves API requests and handles rate-limiting logic.
- A worker service processes Sepolia ETH transactions asynchronously using a task queue.
- Redis is utilized for:
    - Caching: To enforce global rate limits.
    - Queueing: To manage tasks for the worker service.
    - This architecture ensures scalability, high performance, and reliable rate-limiting across distributed instances

### **Prerequisites**
- **Python 3.12.1+**
- **Docker** and **Docker Compose**
- A wallet pre-funded with Sepolia ETH.

### **Environment Variables**
Create a `.env` file in the project root with the following variables:
```env
TREASURY_PUBLIC_KEY=<your-preconfigured-wallet-public-key>
TREASURY_PRIVATE_KEY=<your-preconfigured-wallet-private-key>
ETH_RPC=<your-ethereum-rpc-url>
DJANGO_SETTINGS_MODULE=faucet.settings
FAUCET_RATE_LIMIT_SECONDS=60
```

#### **TO START**
- docker compose up