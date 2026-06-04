# Avatario Self-Hosting Deployment Guide

## Overview

This guide covers complete self-hosting of Avatario on your own infrastructure. Two deployment options are available:

1. **Docker Compose** (Recommended for production)
2. **Manual Setup** (For development/custom needs)

---

## System Requirements

### **Minimum Requirements**
- **CPU**: 4 cores (8 cores recommended)
- **RAM**: 8GB (16GB recommended)
- **Storage**: 50GB SSD (100GB recommended)
- **OS**: Ubuntu 20.04+ / CentOS 8+ / macOS 10.15+

### **Network Requirements**
- **Public IP**: Required for webhook callbacks
- **Ports**: 80, 443 (web), 8001 (API), optional SIP ports
- **SSL Certificate**: Required for production

---

## Option 1: Docker Compose Deployment

### **1.1 Clone Repository**
```bash
git clone https://github.com/your-org/avatario.git
cd avatario
```

### **1.2 Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
nano .env
```

### **1.3 Docker Compose Setup**
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8001:8001"
    environment:
      - SARVAM_API_KEY=${SARVAM_API_KEY}
      - LIVEKIT_URL=${LIVEKIT_URL}
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
      - VLLM_API_BASE=${VLLM_API_BASE}
      - VLLM_API_KEY=${VLLM_API_KEY}
      - VLLM_MODEL=${VLLM_MODEL}
      - PRIMARY_PROVIDER=${PRIMARY_PROVIDER}
      - EXOTEL_API_KEY=${EXOTEL_API_KEY}
      - EXOTEL_API_TOKEN=${EXOTEL_API_TOKEN}
      - BASE_URL=${BASE_URL}
    volumes:
      - ./data:/app/data
      - ./backend/config:/app/config
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend-web
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8001
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=avatario
      - POSTGRES_USER=avatario
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

### **1.4 Nginx Configuration**
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8001;
    }

    upstream frontend {
        server frontend:3000;
    }

    # HTTP redirect to HTTPS
    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS configuration
    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        # WebSocket support for LiveKit
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

### **1.5 Deploy**
```bash
# Build and start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

---

## Option 2: Manual Setup

### **2.1 Backend Setup**

#### Install Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv nodejs npm nginx postgresql redis-server

# CentOS/RHEL
sudo yum install python3 python3-pip nodejs npm nginx postgresql redis
```

#### Backend Installation
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env

# Start backend
uvicorn main:app --host 0.0.0.0 --port 8001
```

#### Systemd Service
```ini
# /etc/systemd/system/avatario-backend.service
[Unit]
Description=Avatario Backend
After=network.target

[Service]
Type=simple
User=avatario
WorkingDirectory=/opt/avatario/backend
Environment=PATH=/opt/avatario/backend/.venv/bin
ExecStart=/opt/avatario/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable avatario-backend
sudo systemctl start avatario-backend
```

### **2.2 Frontend Setup**

#### Install and Build
```bash
cd frontend-web
npm install
npm run build

# Production server
npm start
```

#### PM2 Process Manager
```bash
npm install -g pm2
pm2 start npm --name "avatario-frontend" -- start
pm2 save
pm2 startup
```

### **2.3 Database Setup**

#### PostgreSQL
```bash
sudo -u postgres createdb avatario
sudo -u postgres createuser avatario
sudo -u postgres psql -c "ALTER USER avatario PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE avatario TO avatario;"
```

#### Migration Scripts
```bash
cd backend
python migrate.py
```

---

## SSL Certificate Setup

### **Let's Encrypt (Free)**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### **Self-Signed (Development)**
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem
```

---

## Monitoring & Logging

### **Health Checks**
```bash
# Backend health
curl http://localhost:8001/health

# Service status
sudo systemctl status avatario-backend
pm2 status
```

### **Log Management**
```bash
# Backend logs
sudo journalctl -u avatario-backend -f

# Frontend logs
pm2 logs avatario-frontend

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### **Monitoring Stack (Optional)**
```yaml
# monitoring/docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  node-exporter:
    image: prom/node-exporter
    ports:
      - "9100:9100"
```

---

## Backup Strategy

### **Database Backup**
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U avatario avatario > backup_$DATE.sql
gzip backup_$DATE.sql

# Upload to cloud storage (optional)
# aws s3 cp backup_$DATE.sql.gz s3://your-backup-bucket/
```

### **Automated Backup**
```bash
# Add to crontab
0 2 * * * /opt/avatario/scripts/backup.sh
```

---

## Security Hardening

### **Firewall Configuration**
```bash
# UFW (Ubuntu)
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8001  # API access restricted to internal

# iptables (CentOS)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8001 -s 127.0.0.1 -j ACCEPT
```

### **Application Security**
```bash
# File permissions
sudo chown -R avatario:avatario /opt/avatario
sudo chmod 600 /opt/avatario/.env

# Fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

---

## Performance Optimization

### **Database Optimization**
```sql
-- PostgreSQL tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

### **Application Caching**
```bash
# Redis configuration
echo "maxmemory 256mb" >> /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf
sudo systemctl restart redis
```

---

## Scaling Considerations

### **Horizontal Scaling**
- Load balancer (HAProxy/Nginx)
- Multiple backend instances
- Database read replicas
- Redis cluster

### **Vertical Scaling**
- Increase CPU/RAM allocation
- SSD storage upgrade
- GPU for lip-sync processing

---

## Troubleshooting

### **Common Issues**

#### Backend Won't Start
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check dependencies
source .venv/bin/activate
pip list

# Check environment variables
env | grep AVATARIO
```

#### Frontend Build Fails
```bash
# Clear node modules
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+
```

#### Database Connection Issues
```bash
# Test connection
psql -h localhost -U avatario -d avatario

# Check PostgreSQL status
sudo systemctl status postgresql
```

#### SSL Certificate Issues
```bash
# Test certificate
openssl s_client -connect your-domain.com:443

# Check Nginx configuration
sudo nginx -t
```

### **Performance Issues**
```bash
# Check system resources
htop
df -h
free -h

# Monitor network
netstat -tulpn
ss -tulpn
```

---

## Maintenance Tasks

### **Weekly**
- Update system packages
- Check log files for errors
- Monitor disk usage
- Review API usage

### **Monthly**
- Update application dependencies
- Test backup restoration
- Review security updates
- Performance tuning

### **Quarterly**
- SSL certificate renewal check
- Security audit
- Capacity planning
- Disaster recovery testing

---

## Support & Documentation

- **Documentation**: `/docs` directory
- **API Reference**: `http://your-domain.com/docs`
- **Health Check**: `http://your-domain.com/health`
- **Logs**: `/var/log/avatario/`
- **Community**: GitHub Issues & Discussions

---

## Quick Deployment Checklist

- [ ] Server provisioned with minimum requirements
- [ ] Domain name pointed to server IP
- [ ] SSL certificate obtained
- [ ] All API keys configured in `.env`
- [ ] Database created and migrated
- [ ] Services running and healthy
- [ ] Firewall configured
- [ ] Backup strategy implemented
- [ ] Monitoring set up
- [ ] Load testing completed
