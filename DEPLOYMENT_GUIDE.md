# Hobbes App Deployment Guide

## 🚀 **Deployed Applications**

### **Frontend**: https://hobbes-frontend.fly.dev
- **Status**: ✅ Live and operational
- **Technology**: React + Nginx
- **Build**: Production-optimized with environment variables

### **Backend**: https://hobbes-backend.fly.dev  
- **Status**: ✅ Live and operational
- **Technology**: FastAPI + Python
- **Database**: AWS DynamoDB (us-east-1)
- **Storage**: AWS S3 + SQS

## 🧪 **Testing the Deployment**

### **What Works**
✅ **Frontend Application**
- React app loads and displays correctly
- Environment variables properly configured
- Google OAuth Client ID embedded
- Backend API URL configured

✅ **Backend API**
- Health check: https://hobbes-backend.fly.dev/health
- AWS services connected (DynamoDB, S3, SQS)
- All API endpoints functional
- Database tables created

✅ **Google OAuth**
- Client ID: `775683774120-77a9d7tbo6s0n87op8cserkps28e6lq0.apps.googleusercontent.com`
- Environment variables properly embedded
- **Authorized domains configured** in Google Cloud Console

### **Testing Checklist**
1. **Visit**: https://hobbes-frontend.fly.dev
2. **Login**: Click "Sign in with Google"
3. **Test Features**: Projects, Notes, Action Items
4. **Test API**: Backend should respond at https://hobbes-backend.fly.dev/health

## ⚡ **Fast Iteration Workflow**

### **Frontend Changes**
```bash
# Navigate to frontend directory
cd frontend

# Deploy with cache (fast - ~30 seconds)
~/.fly/bin/fly deploy -a hobbes-frontend

# Deploy without cache (slower but ensures fresh build)
~/.fly/bin/fly deploy --no-cache -a hobbes-frontend
```

### **Backend Changes**
```bash
# Navigate to backend directory  
cd backend

# Deploy (fast - ~45 seconds)
~/.fly/bin/fly deploy -a hobbes-backend
```

### **Environment Variables**

#### **Frontend Environment Variables**
Set in `frontend/fly.toml` as build arguments:
```toml
[build.args]
REACT_APP_API_URL = "https://hobbes-backend.fly.dev"
REACT_APP_GOOGLE_CLIENT_ID = "775683774120-77a9d7tbo6s0n87op8cserkps28e6lq0.apps.googleusercontent.com"
```

#### **Backend Environment Variables**
Set as Fly.io secrets:
```bash
# View current secrets
~/.fly/bin/fly secrets list -a hobbes-backend

# Set new secrets
~/.fly/bin/fly secrets set VAR_NAME=value -a hobbes-backend
```

## 🛠️ **Deployment Commands**

### **Status & Monitoring**
```bash
# Check app status
~/.fly/bin/fly status -a hobbes-frontend
~/.fly/bin/fly status -a hobbes-backend

# View logs
~/.fly/bin/fly logs -a hobbes-frontend
~/.fly/bin/fly logs -a hobbes-backend

# Monitor deployment
~/.fly/bin/fly logs -a hobbes-frontend -f
```

### **Troubleshooting**
```bash
# Restart app
~/.fly/bin/fly machine restart MACHINE_ID -a APP_NAME

# Scale down/up
~/.fly/bin/fly scale count 0 -a APP_NAME
~/.fly/bin/fly scale count 1 -a APP_NAME

# SSH into machine
~/.fly/bin/fly ssh console -a APP_NAME
```

## 🔧 **Configuration Files**

### **Key Files**
- `frontend/fly.toml` - Frontend app configuration
- `frontend/Dockerfile.production` - Frontend build process
- `backend/fly.toml` - Backend app configuration  
- `backend/Dockerfile.production` - Backend build process
- `.env.production` - Backend environment variables (local)

### **Important Notes**
1. **Frontend env vars**: Must be set as build args in `fly.toml`
2. **Backend env vars**: Set as Fly.io secrets for security
3. **Caching**: Use `--no-cache` for environment variable changes
4. **Health checks**: Frontend uses `/`, Backend uses `/health`

## 💰 **Cost Optimization**

### **Current Configuration**
- **Frontend**: 256MB RAM, shared CPU, auto-stop enabled
- **Backend**: 256MB RAM, shared CPU, auto-stop enabled  
- **Expected cost**: ~$5-10/month total
- **AWS costs**: Minimal (DynamoDB on-demand, S3 storage)

### **Auto-scaling**
Both apps are configured with:
- `auto_stop_machines = 'stop'`
- `auto_start_machines = true`
- `min_machines_running = 0`

This means apps stop when idle and start on first request.

## 🚀 **Next Steps**

### **Production Readiness**
1. **SSL/TLS**: ✅ Automatically handled by Fly.io
2. **Custom Domain**: Optional - can add custom domain
3. **Database Backups**: Configure DynamoDB backups
4. **Monitoring**: Add application monitoring
5. **CI/CD**: Set up GitHub Actions for automatic deploys

### **Development Workflow**
1. **Local Development**: Use `make dev-start` for local testing
2. **Deploy Testing**: Use Fly.io for sharing with developers
3. **Production**: Same Fly.io setup, different environment

---

## 📝 **Quick Reference**

```bash
# Deploy frontend
cd frontend && ~/.fly/bin/fly deploy -a hobbes-frontend

# Deploy backend  
cd backend && ~/.fly/bin/fly deploy -a hobbes-backend

# Check status
~/.fly/bin/fly status -a hobbes-frontend
~/.fly/bin/fly status -a hobbes-backend

# View logs
~/.fly/bin/fly logs -a hobbes-frontend
~/.fly/bin/fly logs -a hobbes-backend
```

**Total deployment time**: ~30-60 seconds per service
**Cost**: ~$5-10/month
**Uptime**: High availability with auto-scaling 