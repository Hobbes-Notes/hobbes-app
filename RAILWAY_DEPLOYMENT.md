# Railway Deployment Guide for Hobbes App 🚀

This guide will help you deploy the Hobbes app to Railway in just a few minutes!

## Quick Start (2 minutes!)

### 1. Connect to Railway
1. Go to [railway.app](https://railway.app)
2. Sign up/login with GitHub
3. Click "Deploy from GitHub repo"
4. Select this repository
5. Choose the `railway-deployment` branch

### 2. Configure Environment Variables
In Railway dashboard, add these environment variables:

**Required:**
```
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
OPENAI_API_KEY=your_openai_api_key
```

**Optional (for advanced features):**
```
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
```

### 3. Add PostgreSQL Database
1. In Railway dashboard, click "New Service" 
2. Select "PostgreSQL"
3. Railway automatically connects it to your app!

### 4. Deploy!
Railway automatically deploys when you push to the branch. That's it! 🎉

## What Railway Provides Automatically

✅ **PostgreSQL Database** - Replaces DynamoDB for cloud hosting  
✅ **HTTPS Domain** - Secure `https://yourapp.up.railway.app`  
✅ **Environment Variables** - Easy configuration management  
✅ **Auto-scaling** - Handles traffic spikes  
✅ **Zero-downtime Deployments** - Seamless updates  

## Cost Estimate

- **Free Tier**: $0/month for 500 hours (enough for learning/testing)
- **Small Production**: ~$5-15/month 
- **Active Use**: ~$20-40/month

## Updating Your App

1. Make changes to the `railway-deployment` branch
2. Push to GitHub
3. Railway automatically redeploys!

```bash
git checkout railway-deployment
# Make your changes...
git add .
git commit -m "Update app"
git push origin railway-deployment
```

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_CLIENT_ID` | ✅ | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | ✅ | Google OAuth client secret |
| `OPENAI_API_KEY` | ✅ | OpenAI API key for AI features |
| `AWS_ACCESS_KEY_ID` | ❌ | AWS credentials (for S3 features) |
| `AWS_SECRET_ACCESS_KEY` | ❌ | AWS credentials (for S3 features) |
| `AWS_REGION` | ❌ | AWS region (default: us-east-1) |

## Differences from Local Development

| Feature | Local Development | Railway Production |
|---------|------------------|-------------------|
| **Database** | DynamoDB Local | PostgreSQL |
| **Frontend** | React Dev Server (port 3000) | Built & served by backend |
| **Backend** | FastAPI (port 8888) | FastAPI (auto port) |
| **HTTPS** | HTTP only | HTTPS automatically |
| **Domain** | localhost | yourapp.up.railway.app |

## Troubleshooting

### ❌ "Database connection failed"
- Check that PostgreSQL service is running in Railway
- Verify `DATABASE_URL` is automatically set

### ❌ "Google OAuth not working"
- Update Google OAuth redirect URLs to include your Railway domain
- Add `https://yourapp.up.railway.app` to authorized origins

### ❌ "Build failed" 
- Check the Railway build logs
- Ensure all environment variables are set
- Try redeploying

### ❌ "App not loading"
- Check Railway service logs
- Verify the `/health` endpoint works
- Test database connectivity

## Need Help?

1. Check Railway service logs in the dashboard
2. Test the health endpoint: `https://yourapp.up.railway.app/health`
3. Review environment variables are all set correctly

## Back to Local Development

To go back to local development:
```bash
git checkout main
make dev-start
```

Your local DynamoDB data is preserved separately! 