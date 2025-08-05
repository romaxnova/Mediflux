# Database Architecture Analysis for Mediflux V2

## Requirements Analysis

### Data Types to Store:
1. **User Profiles** - JSON data (mutuelle, location, pathology, preferences)
2. **Session History** - Query logs, timestamps, results
3. **API Cache** - BDPM, Annuaire Santé, Odissé responses
4. **Document Analysis** - OCR results, extracted data, analysis metadata
5. **Care Pathways** - Generated pathways, user decisions

### Usage Patterns:
- Primarily single-user development/demo environment
- Read-heavy workload (cached API responses)
- JSON-heavy data structures
- Simple relational needs

## SQLite vs PostgreSQL Comparison

| Factor | SQLite | PostgreSQL (NeonDB) |
|--------|--------|-------------------|
| **Development Ease** | ⭐⭐⭐⭐⭐ Simple, file-based | ⭐⭐⭐ Requires setup/connection |
| **JSON Support** | ⭐⭐⭐⭐ JSON1 extension | ⭐⭐⭐⭐⭐ Native JSONB |
| **Deployment** | ⭐⭐⭐⭐⭐ Zero config | ⭐⭐⭐ Cloud dependency |
| **Concurrent Access** | ⭐⭐ Limited | ⭐⭐⭐⭐⭐ Excellent |
| **Scalability** | ⭐⭐ File-based limits | ⭐⭐⭐⭐⭐ Cloud scalable |
| **Cost** | ⭐⭐⭐⭐⭐ Free | ⭐⭐⭐⭐ Free tier available |

## Decision: SQLite for V2

**Reasoning:**
1. **Development-first approach** - V2 is focused on rapid prototyping
2. **Single-user demo context** - No concurrent access needs currently
3. **Zero deployment complexity** - File-based, portable
4. **JSON support sufficient** - JSON1 extension handles our needs
5. **Easy migration path** - Can migrate to PostgreSQL for production

## Implementation Plan

### Schema Design:
```sql
-- User profiles and preferences
users (id, user_id TEXT, profile JSON, created_at, updated_at)

-- Session history and query logs  
sessions (id, user_id TEXT, query TEXT, intent TEXT, result JSON, timestamp)

-- API response caching
api_cache (id, endpoint TEXT, params_hash TEXT, response JSON, expires_at)

-- Document analysis results
documents (id, user_id TEXT, filename TEXT, analysis JSON, created_at)
```

### Features:
- Automatic schema migrations
- JSON query support with JSON1 extension
- Connection pooling for async operations
- Cache expiration and cleanup
- Data retention policies
