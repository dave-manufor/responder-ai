# Respondr.ai Backend - Setup Guide

## Prerequisites

- Python 3.11 or higher
- MongoDB Atlas account (already configured in `.env`)
- Virtual environment activated

## Step 1: Install Dependencies

```bash
cd /Users/MAC/Dev/code/responder-ai/backend

# Activate virtual environment (if not already active)
source ../venv/bin/activate  # or source ../.venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

## Step 2: Verify Environment Variables

The `.env` file should already contain:
```
MONGODB_URI=mongodb+srv://...
MONGODB_DB_NAME=respondr_hospitals
WATSON_STT_APIKEY=...
WATSON_STT_URL=...
WATSONX_API_KEY=...
WATSONX_PROJECT_ID=...
```

✅ All credentials are already configured!

## Step 3: Seed Database

Populate MongoDB with Nairobi hospital data:

```bash
python seed_data.py
```

Expected output:
```
🏥 Seeding hospital data...
📄 Loaded 8 hospitals from hospitals.json
🗑️  Deleted 0 existing records
✅ Inserted 8 hospitals
🌍 Created 2dsphere geospatial index on 'geometry' field
✅ Verification: 8 hospitals in database
🎉 Seeding completed successfully!
```

## Step 4: Run the Server

Start the FastAPI development server:

```bash
uvicorn main:app --reload --port 8000
```

Server will be available at: **http://localhost:8000**

## Step 5: Verify API is Working

### Health Check
```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-11-22T09:00:00.000000"
}
```

### List Hospitals
```bash
curl http://localhost:8000/hospitals
```

Should return 8 hospitals.

### Geospatial Query
```bash
curl "http://localhost:8000/hospitals?lat=-1.2921&lon=36.8219&max_km=5"
```

Should return hospitals within 5km of coordinates.

## Step 6: Run Tests

Execute the test suite:

```bash
pytest test_api.py -v
```

Expected: All tests should pass ✅

Run with coverage:
```bash
pytest test_api.py -v --cov=. --cov-report=term-missing
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/hospitals` | List all hospitals |
| GET | `/hospitals?lat=X&lon=Y` | Geospatial proximity search |
| POST | `/reserve_bed` | Reserve bed(s) at specific hospital |
| POST | `/api/allocate` | Bulk allocation across hospitals |
| POST | `/api/reset` | Reset all allocations (demo) |

## Example API Calls

### Reserve 2 RED beds
```bash
curl -X POST http://localhost:8000/reserve_bed \
  -H "Content-Type: application/json" \
  -d '{
    "hospital_id": "hosp_001",
    "severity": "RED",
    "patient_count": 2
  }'
```

### Allocate 15 patients
```bash
curl -X POST http://localhost:8000/api/allocate \
  -H "Content-Type: application/json" \
  -d '{
    "lat": -1.2921,
    "lon": 36.8219,
    "patient_count": 15,
    "triage_color": "RED"
  }'
```

### Reset for demo
```bash
curl -X POST http://localhost:8000/api/reset
```

## MongoDB Atlas Verification

To verify the 2dsphere index exists:

1. Go to MongoDB Atlas dashboard
2. Browse Collections → `respondr_hospitals` → `hospitals`
3. Click on "Indexes" tab
4. Should see: `geometry_2dsphere`

If index doesn't exist, run:
```bash
python -c "from database import get_hospitals_collection; c = get_hospitals_collection(); print('Index created')"
```

## Troubleshooting

### MongoDB Connection Issues
- Verify `MONGODB_URI` in `.env`
- Check MongoDB Atlas network access (whitelist your IP)
- Ensure internet connection

### Import Errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

### Tests Failing
- Ensure MongoDB is connected (`python -c "from database import check_connection; print(check_connection())"`)
- Run `python seed_data.py` to reset data
- Check for typos in environment variables

## External Setup Requirements

✅ **MongoDB Atlas**: Already configured (connection string in `.env`)
✅ **Watson STT**: Already configured (API key in `.env`)
✅ **watsonx.ai**: Already configured (API key + project ID in `.env`)

**No additional external setup needed!** Just run the seed script and start coding.

## Next Steps (Phase 2)

Once Phase 1 is verified:
1. Implement Watson STT WebSocket integration
2. Integrate watsonx.ai for triage classification
3. Build watsonx Orchestrate ADK agent
4. Add session state management
5. Test end-to-end flow

---

**Need help?** Check the project overview at `/Users/MAC/Dev/code/responder-ai/docs/project-overview.md`
