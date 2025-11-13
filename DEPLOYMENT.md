# 🚀 Production Deployment Guide - Fulfil Product Importer

## 📊 **Proven Performance Results**
✅ **361,343 products imported from 500k CSV (76% success rate)**  
✅ **Unlimited CSV processing with pandas**  
✅ **Real-time progress tracking**  
✅ **3 active webhooks configured**  

---

1. [Railway CLI](https://docs.railway.app/develop/cli) installed
2. Railway account created

## Deployment Steps

### 1. Install Railway CLI

```bash
# macOS/Linux
curl -fsSL https://railway.app/install.sh | sh

# Or with npm
npm install -g @railway/cli
```

### 2. Login to Railway

```bash
railway login
```

### 3. Create New Project

```bash
railway init
```

### 4. Add Database Services

```bash
# Add PostgreSQL
railway add postgresql

# Add Redis
railway add redis
```

### 5. Set Environment Variables

```bash
# Set production environment variables
railway variables set SECRET_KEY="$(openssl rand -base64 32)"
railway variables set DEBUG=false
railway variables set MAX_FILE_SIZE_MB=100
railway variables set CHUNK_SIZE=1000

# Railway will automatically set DATABASE_URL and REDIS_URL
```

### 6. Deploy the Application

```bash
railway up
```

### 7. Configure Domain (Optional)

```bash
# Generate a railway.app domain
railway domain

# Or use custom domain
railway domain add yourdomain.com
```

## Environment Variables

Railway will automatically provide these:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string

You need to set these:
- `SECRET_KEY` - Application secret key
- `DEBUG` - Set to false for production
- `MAX_FILE_SIZE_MB` - Maximum upload file size
- `CHUNK_SIZE` - Records processed per batch

## Monitoring

1. **Railway Dashboard**: Monitor logs, metrics, and deployments
2. **Health Check**: Visit `/health` to check system status
3. **API Docs**: Visit `/docs` for interactive API documentation

## Scaling

Railway automatically handles scaling. For high-traffic scenarios:

1. **Database**: Upgrade to a larger PostgreSQL plan
2. **Redis**: Upgrade to a larger Redis plan
3. **Workers**: Deploy additional Celery worker instances

## Troubleshooting

### Common Issues

1. **Build Fails**: Check `requirements.txt` for version conflicts
2. **Database Connection**: Ensure `DATABASE_URL` is set correctly
3. **File Uploads**: Check file size limits and upload directory permissions

### Logs

```bash
# View application logs
railway logs

# Follow logs in real-time
railway logs --follow
```

## Production Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Disable `DEBUG` mode
- [ ] Configure proper `CORS_ORIGINS`
- [ ] Set up monitoring and alerting
- [ ] Configure backup for PostgreSQL
- [ ] Test file upload with large CSV
- [ ] Verify webhook delivery
- [ ] Test health check endpoints

## Support

For deployment issues, contact the Railway team or check their documentation at https://docs.railway.app