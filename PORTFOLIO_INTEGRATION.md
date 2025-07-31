# Portfolio Integration Guide

This document explains the changes made to integrate the class-scheduler with your portfolio.

## Changes Made

### 1. Added Portfolio Authentication (`portfolio_auth.py`)
- Secure authentication system using SHA-256 hashing with salt
- Time-based validation (5-minute expiry)
- No sensitive data transmission

### 2. Updated `app.py`
- Added portfolio authentication import
- Updated CORS to include portfolio domains
- Added three new portfolio-specific endpoints:
  - `POST /api/generate-schedule` - Generate a basic schedule
  - `POST /api/optimal-schedules` - Generate optimal schedules
  - `POST /api/validate-schedule` - Validate schedule for conflicts

### 3. Updated CORS Configuration
- Added `http://localhost:4321` for portfolio development
- Added `http://127.0.0.1:4321` for alternative local access
- Set `allow_credentials=False` for portfolio auth

## New API Endpoints

### POST `/api/generate-schedule`
**Headers Required:**
- `X-Portfolio-Auth`: Base64 encoded auth token
- `X-Portfolio-Hash`: SHA-256 hash with salt
- `X-Portfolio-Timestamp`: Request timestamp

**Input:**
```json
{
  "courses": [...],
  "preferences": {
    "exclude_weekend": true
  }
}
```

**Output:**
```json
{
  "schedule": [...],
  "message": "Schedule generated successfully",
  "score": [0, 1]
}
```

### POST `/api/optimal-schedules`
**Input:**
```json
{
  "courses": [...],
  "count": 5
}
```

**Output:**
```json
{
  "schedules": [
    {
      "selections": [...],
      "conflictScore": 0,
      "score": 85.5
    }
  ],
  "message": "Generated 1 optimal schedule(s)"
}
```

### POST `/api/validate-schedule`
**Input:**
```json
{
  "schedule": [
    {
      "course": "CPRG 213 Web Development 1",
      "professor": "Aaron Warsylewicz",
      "section": {...}
    }
  ]
}
```

**Output:**
```json
{
  "valid": true,
  "conflicts": [],
  "message": "Validation complete. 0 conflicts found."
}
```

## Deployment Steps

### 1. Commit and Push Changes
```bash
cd /Users/ksimons/repos/class-scheduler
git add .
git commit -m "Add portfolio authentication and API endpoints"
git push origin main
```

### 2. Deploy to GCP
Your existing deployment pipeline should automatically deploy the changes.

### 3. Portfolio Domain Configuration
The CORS origins are already configured for your domain:
```python
allow_origins=[
    "http://localhost:4321",  # Local development
    "http://127.0.0.1:4321",  # Alternative local
    "https://kylesimons.ca",  # Production domain
    "https://www.kylesimons.ca"  # WWW subdomain
]
```

## Security Features

- **Time-based Authentication**: Requests expire after 5 minutes
- **Hash Verification**: SHA-256 with salt prevents tampering
- **No Credentials**: No user data or sensitive information transmitted
- **Domain Restriction**: CORS limits access to your portfolio domain only

## Testing

1. **Local Testing**: Portfolio at `http://localhost:4321/scheduler`
2. **API Testing**: Backend at `http://35.197.99.197:8000`
3. **Authentication**: All requests from portfolio are automatically authenticated

## Debugging

The backend will log authenticated requests:
```
📱 Portfolio request authenticated with key: 12345678...
```

Check your GCP logs to verify authentication is working correctly.

## Next Steps

1. Deploy these changes to your GCP instance
2. Test the integration from your portfolio
3. Update the portfolio domain in CORS settings when deployed
4. Monitor logs for any authentication issues