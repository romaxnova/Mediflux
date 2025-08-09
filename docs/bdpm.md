# BDPM (Base de Données Publique des Médicaments) API

## Overview
The BDPM API provides access to the French public database of medications maintained by ANSM, HAS, and UNCAM. This API contains comprehensive data about French medications including CIS codes, denominations, substances, prices, and reimbursement information.

## Deployed API
- **URL**: https://mediflux-bdpm-api.onrender.com/graphql
- **Type**: GraphQL API
- **Source**: Self-deployed fork of [api-bdpm-graphql](https://github.com/romaxnova/api-bdpm-graphql)

## Integration Issue & Resolution

### Problem
The original external API at `https://api-bdpm-graphql.axel-op.fr/graphql` was experiencing downtime, blocking medication data integration in Mediflux.

### Root Cause
The French government changed their medication database download URL structure:
- **Old URL**: `https://base-donnees-publique.medicaments.gouv.fr/telechargement.php?fichier=CIS_bdpm.txt`
- **New URL**: `https://base-donnees-publique.medicaments.gouv.fr/download/file/CIS_bdpm.txt`

This caused 404 errors during API initialization when trying to download medication data files.

### Fix Applied
Updated the default URL path in the BDPM client:

**File**: `src/bdpm_client.js` (line ~9)
```js
// Before
path = process.env.BDPM_URL_PATH || "/telechargement.php"

// After  
path = process.env.BDPM_URL_PATH || "/download/file"
```

### Deployment Configuration
**File**: `render.yaml`
```yaml
services:
  - type: web
    name: bdpm-graphql-api
    env: node
    plan: free
    buildCommand: npm install
    startCommand: node src/server.js
    envVars:
      - key: BDPM_URL_PATH
        value: /download/file
    healthCheckPath: /graphql
    autoDeploy: true
```

## Usage Examples

### Basic Medication Query
```graphql
{
  medicaments(limit: 5) {
    CIS
    denomination
    substances {
      denominations
    }
  }
}
```

### Search by CIS Code
```graphql
{
  medicaments(CIS: ["68572075"]) {
    denomination
    presentations {
      libelle
      prix_sans_honoraires
      taux_remboursement
    }
  }
}
```

### cURL Example
```bash
curl -X POST https://mediflux-bdpm-api.onrender.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ medicaments(limit: 2) { denomination CIS } }"}'
```

## Data Integration in Mediflux

The BDPM API is integrated into Mediflux through:
- **Module**: `modules/data_hub/bdpm.py`
- **Usage**: Medication lookup, pricing information, substance data
- **Fallback**: Self-deployed API ensures continuous availability

## Maintenance Notes

- **Auto-deploy**: Enabled on Render for seamless updates
- **Free tier**: Current deployment uses Render's free plan
- **Health check**: API status monitored via `/graphql` endpoint
- **Data refresh**: API automatically downloads latest French government medication data

## Future Considerations

1. **Monitoring**: Consider implementing API health monitoring
2. **Caching**: Add response caching for frequently accessed medication data
3. **Rate limiting**: Monitor usage and implement rate limiting if needed
4. **Backup**: Consider additional deployment locations for redundancy

---
*Last updated: August 2025*
*Status: ✅ Active and functional*
