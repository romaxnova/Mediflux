# Mediflux V2 Data Storage Strategy & Deployment Guide

## Current Data Storage Analysis

### 📊 **Storage Overview**
```
Total Raw Data: ~794MB
├── SAE Hospital Data: ~211MB (26MB 7z + 185MB extracted)
├── DREES Demographics: ~102MB (68MB médecins + 17MB pharmaciens + others)
├── OpenMedic: ~24MB (ZIP format)
├── SQLite Databases: ~1MB (processed data)
└── Extracted CSVs: ~550MB+ (from OpenMedic ZIP expansion)
```

### 🗄️ **Current Database Structure**
- **Primary DB**: `mediflux_v2.db` (52KB) - Main application database
- **Data DB**: `data/mediflux.db` (840KB) - SAE processed data  
- **OpenMedic DB**: Various small DBs (16KB-32KB)
- **Memory DB**: `data/user_memory.db` (28KB) - User sessions

## 📈 **Storage Efficiency Analysis**

### ✅ **What's Working Well**
1. **SQLite Processing**: Raw 794MB → ~1MB processed data (99.9% compression)
2. **Structured Data**: Hospital/medication data well-organized in tables
3. **Fast Queries**: SQLite performs excellently for our use case
4. **Single-file Deployment**: Easy to backup/transfer

### ⚠️ **Current Issues**
1. **Raw Data Retention**: We're keeping 794MB of source files unnecessarily
2. **Multiple DB Files**: Scattered across different locations
3. **Redundant Storage**: Same data in raw + processed formats
4. **Large Dev Environment**: 794MB not suitable for web deployment

## 🎯 **Optimized Storage Strategy**

### **Phase 1: Immediate Optimization (Local Development)**

#### Database Consolidation
```python
# Single unified database structure:
mediflux_production.db (estimated: ~2-5MB)
├── sae_hospitals (3,975 records)
├── sae_mco_activity (1,528 records)  
├── sae_urgences (620 records)
├── sae_regional_metrics (101 records)
├── openmedic_medications (1.9M records, optimized)
├── drees_professionals (estimated: 50k records)
├── user_profiles (session data)
└── api_cache (temp storage)
```

#### Data Processing Pipeline
```
Raw Download → Process → Store in SQLite → Delete Raw Files
794MB raw → 2-5MB production database
```

### **Phase 2: Production Deployment Strategy**

#### **Option A: SQLite + File Storage (Recommended for MVP)**
```
Deployment Package:
├── mediflux_app/ (Python app ~50MB)
├── mediflux_production.db (2-5MB)
├── static/ (Frontend assets ~10MB)
└── requirements.txt
Total: ~65MB deployment package
```

**Advantages:**
- ✅ Single-file database (easy backup/restore)
- ✅ No external database dependencies  
- ✅ Fast local queries
- ✅ Perfect for MVP/demo deployment
- ✅ Works on most web hosts (Heroku, Railway, DigitalOcean)

#### **Option B: PostgreSQL/MySQL (Future Scale)**
```
Production Stack:
├── Web App Instance (2-5MB database → Cloud DB)
├── PostgreSQL/MySQL (managed service)
├── Redis (caching layer)
└── File Storage (S3/similar for attachments)
```

**When to migrate:** >100k users or >10GB data

### **Phase 3: Deployment Architecture**

#### **Recommended Hosting Stack (MVP)**
```
Railway.app / Render.com / Fly.io:
├── Python FastAPI app
├── SQLite database (included)  
├── React frontend (static build)
└── Auto-deployment from Git
Cost: $5-20/month
```

#### **Alternative: Serverless**
```
Vercel + PlanetScale:
├── Next.js frontend (Vercel)
├── Python API (Vercel Functions)
├── PlanetScale MySQL (managed)
└── Edge caching
Cost: $0-10/month (with usage limits)
```

## 🔧 **Implementation Plan**

### **Step 1: Database Consolidation Script**
Create `scripts/consolidate_database.py`:
- Merge all SQLite files into single production DB
- Optimize indexes for common queries
- Add data validation/cleanup
- Remove redundant columns

### **Step 2: Data Pipeline Automation**
Create `scripts/update_data_sources.py`:
- Download → Process → Update → Cleanup cycle
- Scheduled updates (monthly for SAE, annually for DREES)
- Incremental updates where possible
- Rollback capability

### **Step 3: Deployment Configuration**
```yaml
# railway.json / render.yaml
services:
  - name: mediflux-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - DATABASE_URL=sqlite:///./mediflux_production.db
      - ENVIRONMENT=production
```

### **Step 4: Environment-Specific Configs**
```python
# config/database.py
class DatabaseConfig:
    def __init__(self):
        if ENV == "development":
            self.db_path = "data/mediflux.db" 
            self.keep_raw_files = True
        elif ENV == "production":
            self.db_path = "mediflux_production.db"
            self.keep_raw_files = False  # Clean up after processing
        elif ENV == "staging":
            self.db_path = "mediflux_staging.db"
            self.keep_raw_files = False
```

## 📋 **Migration Checklist**

### **Before Web Deployment:**
- [ ] Create database consolidation script
- [ ] Test with production-sized dataset
- [ ] Implement automatic cleanup of raw files
- [ ] Add database backup/restore functionality  
- [ ] Create deployment documentation
- [ ] Test on staging environment
- [ ] Monitor database size growth

### **Deployment Day:**
- [ ] Run database consolidation
- [ ] Upload production database (~2-5MB)
- [ ] Configure environment variables
- [ ] Test all data endpoints
- [ ] Verify query performance
- [ ] Set up monitoring/logging

## 🚀 **Deployment Commands (Railway Example)**

```bash
# 1. Prepare production database
python scripts/consolidate_database.py

# 2. Test locally with production config  
ENV=production python main.py

# 3. Deploy to Railway
railway login
railway init
railway add --service mediflux-api
railway deploy

# 4. Verify deployment
curl https://your-app.railway.app/health
curl https://your-app.railway.app/api/hospitals/search?city=Paris
```

## 💡 **Key Recommendations**

1. **Start with SQLite**: Perfect for MVP, handles millions of records efficiently
2. **Automate Data Processing**: Never store raw files in production  
3. **Single Database File**: Easier deployment, backup, and scaling decisions
4. **Environment Configs**: Different storage strategies per environment
5. **Monitor Growth**: Plan PostgreSQL migration when SQLite becomes limiting

## 📊 **Expected Production Metrics**
- **Database Size**: 2-5MB (vs current 794MB raw)
- **Query Performance**: <100ms for hospital searches
- **Deployment Size**: ~65MB total package
- **Memory Usage**: ~128MB RAM for API
- **Startup Time**: <5 seconds cold start

## 🚀 **DEPLOYMENT CHECKLIST**

### Phase 1: Pre-Deployment (COMPLETED ✅)
- [x] Database consolidation script created and tested
- [x] Production database generated (1052KB) 
- [x] Environment configurations implemented
- [x] Query performance validated (2.59ms avg)
- [x] Production database health check passing

### Phase 2: Web Hosting Setup
1. **Choose hosting platform** (Recommended: Railway/Render)
2. **Upload production database** (`mediflux_production.db`)
3. **Deploy application** with environment variable `DATABASE_ENV=production`
4. **Test API endpoints** with production data
5. **Monitor performance** (should handle 100+ concurrent users)

### Phase 3: Production Monitoring
- Database size monitoring (starts at 1MB)
- Query performance tracking (< 5ms target)
- User data growth tracking
- Backup strategy implementation

### Phase 4: Scale-Up Path (Future)
- PostgreSQL migration when > 10GB data
- CDN integration for static assets
- Redis caching for frequent queries
- Load balancer for > 1000 concurrent users

This strategy will take us from 794MB development environment to ~65MB production deployment while maintaining all functionality.
