# FewKnow API Backend

FastAPI backend that provides REST API endpoints for post-earnings analysis.

## Architecture

The API is built with a clean, modular structure:

```
api/
├── server.py       # FastAPI application and endpoints
├── core.py         # Core analysis logic (data collection, LLM calls)
├── models.py       # Pydantic models for structured data
├── __init__.py     # Package initialization
└── requirements.txt
```

### Key Design Decisions

**Separation of Concerns:**
- `models.py`: Data structures and schemas
- `core.py`: Business logic with proper logging
- `server.py`: API routes and request handling

**Clean Error Handling:**
- No `sys.exit()` calls (raises exceptions instead)
- Structured logging instead of print statements
- Proper exception propagation for API error responses

**Production-Ready:**
- Background job processing
- Status tracking for long-running tasks
- CORS enabled for web frontend
- Auto-generated API documentation

## Features

- **Async Analysis**: Run long-running analysis jobs in the background
- **Progress Tracking**: Real-time status updates via polling
- **CORS Enabled**: Ready for Next.js frontend integration
- **Auto Documentation**: Swagger UI at `/docs`

## Setup

### 1. Install Dependencies

```bash
cd api
pip install -r requirements.txt
```

This will install FastAPI, Uvicorn, and all dependencies from the main script.

### 2. Environment Variables

The API uses the same `.env` file as the main script (in project root):

```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=FewKnow/1.0
```

### 3. Run the Server

```bash
python server.py
```

Or using uvicorn directly:

```bash
uvicorn server:app --reload --port 8000
```

The server will start on `http://localhost:8000`

## API Endpoints

### Health Check

```
GET /
```

Returns server status.

### Validate Ticker

```
GET /api/validate/{ticker}
```

Quick check if a ticker exists.

**Example:**
```bash
curl http://localhost:8000/api/validate/NVDA
```

**Response:**
```json
{
  "valid": true,
  "ticker": "NVDA",
  "company_info": {
    "ticker": "NVDA",
    "name": "NVIDIA Corporation",
    "sector": "Technology",
    "industry": "Semiconductors"
  }
}
```

### Start Analysis

```
POST /api/analyze
```

Starts a new analysis job.

**Request Body:**
```json
{
  "ticker": "NVDA"
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "progress": "0%",
  "message": "Analysis started"
}
```

### Check Status

```
GET /api/status/{job_id}
```

Get current status of an analysis job.

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": "55%",
  "message": "Collecting Reddit discussions...",
  "updated_at": "2025-10-05T12:34:56.789"
}
```

**Status Values:**
- `pending`: Job queued
- `processing`: Analysis in progress
- `completed`: Analysis finished
- `failed`: Error occurred

### Get Results

```
GET /api/result/{job_id}
```

Retrieve full analysis results (only available when status is `completed`).

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "ticker": "NVDA",
  "company_info": { ... },
  "earnings_metadata": { ... },
  "price_performance": { ... },
  "reddit_analysis": { ... },
  "insight_report": {
    "headline": "NVDA: Strong Beat Masked Underlying Weakness",
    "story": "...",
    "retail_perspective": "...",
    "the_gap": "...",
    "whats_next": "...",
    "key_dates": [...],
    "sources": [...]
  }
}
```

## API Documentation

Interactive API documentation is automatically generated:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Usage Flow

1. **Validate ticker** (optional but recommended):
   ```
   GET /api/validate/NVDA
   ```

2. **Start analysis**:
   ```
   POST /api/analyze
   Body: {"ticker": "NVDA"}
   ```
   Save the returned `job_id`

3. **Poll for status** (every 2-3 seconds):
   ```
   GET /api/status/{job_id}
   ```
   Check `progress` and `status` fields

4. **Get results** when status is `completed`:
   ```
   GET /api/result/{job_id}
   ```

## Example Client Code

### JavaScript/TypeScript

```typescript
async function analyzeStock(ticker: string) {
  // Start analysis
  const startResponse = await fetch('http://localhost:8000/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker })
  });
  
  const { job_id } = await startResponse.json();
  
  // Poll for status
  while (true) {
    const statusResponse = await fetch(`http://localhost:8000/api/status/${job_id}`);
    const status = await statusResponse.json();
    
    console.log(`${status.progress} - ${status.message}`);
    
    if (status.status === 'completed') {
      // Get results
      const resultResponse = await fetch(`http://localhost:8000/api/result/${job_id}`);
      const result = await resultResponse.json();
      return result;
    }
    
    if (status.status === 'failed') {
      throw new Error(status.message);
    }
    
    // Wait 2 seconds before next poll
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
}

// Usage
analyzeStock('NVDA').then(result => {
  console.log(result.insight_report);
});
```

### Python

```python
import requests
import time

def analyze_stock(ticker: str):
    # Start analysis
    response = requests.post('http://localhost:8000/api/analyze', 
                            json={'ticker': ticker})
    job_id = response.json()['job_id']
    
    # Poll for status
    while True:
        response = requests.get(f'http://localhost:8000/api/status/{job_id}')
        status = response.json()
        
        print(f"{status['progress']} - {status['message']}")
        
        if status['status'] == 'completed':
            # Get results
            response = requests.get(f'http://localhost:8000/api/result/{job_id}')
            return response.json()
        
        if status['status'] == 'failed':
            raise Exception(status['message'])
        
        time.sleep(2)

# Usage
result = analyze_stock('NVDA')
print(result['insight_report']['headline'])
```

## Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Next.js   │  HTTP   │  FastAPI    │ Calls   │  script.py  │
│   Frontend  │ ──────> │   Backend   │ ──────> │  Functions  │
│             │         │             │         │             │
└─────────────┘         └─────────────┘         └─────────────┘
                              │
                              │ Uses
                              ▼
                        ┌─────────────┐
                        │  External   │
                        │   APIs      │
                        │ - Yahoo     │
                        │ - Reddit    │
                        │ - Anthropic │
                        └─────────────┘
```

## Production Considerations

For production deployment:

1. **Use Redis or Database**: Replace in-memory storage with persistent storage
2. **Add Authentication**: Implement API key or JWT authentication
3. **Rate Limiting**: Add rate limiting to prevent abuse
4. **Caching**: Cache ticker validation and earnings data
5. **Error Handling**: Add comprehensive error tracking (Sentry, etc.)
6. **Logging**: Implement structured logging
7. **WebSocket**: Consider WebSocket for real-time progress updates instead of polling
8. **Environment**: Set `reload=False` in production
9. **CORS**: Restrict allowed origins to production domains

## Troubleshooting

### Server won't start

- Check if port 8000 is already in use
- Verify all dependencies are installed
- Check `.env` file exists in parent directory

### Analysis fails

- Verify API keys in `.env` file
- Check script.py works standalone: `python script.py NVDA`
- Review error message in status endpoint

### CORS errors

- Ensure frontend is running on allowed origin (localhost:3000 or localhost:3001)
- Check browser console for specific CORS error

## License

MIT
