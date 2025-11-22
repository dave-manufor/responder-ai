# Frontend Setup Guide - Respondr.ai

## Prerequisites
- Node.js (v18+)
- Python 3.9+ (for backend)
- MongoDB (running locally or Atlas URI)

## 1. Backend Setup
Before developing the frontend, ensure the backend is running.

1. Navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment:
   - Copy `.env.example` to `.env` (if available) or ensure `MONGO_URI` is set.
   - Default `MONGO_URI=mongodb://localhost:27017`.
4. Start the server:
   ```bash
   uvicorn main:app --reload
   ```
   - Server should be running at `http://localhost:8000`.
   - API Docs available at `http://localhost:8000/docs`.

## 2. Frontend Configuration
(Assuming a React/Vite setup)

1. Create a `.env` file in your frontend root:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```

2. Proxy Setup (Optional but Recommended):
   In `vite.config.ts`:
   ```typescript
   export default defineConfig({
     server: {
       proxy: {
         '/api': {
           target: 'http://localhost:8000',
           changeOrigin: true,
         },
       },
     },
   })
   ```

## 3. Verifying Connection
1. Start your frontend dev server.
2. Check the browser console/network tab.
3. Ensure requests to `/health` or `/hospitals` return 200 OK.

## Troubleshooting
- **CORS Errors**: The backend is configured to allow all origins (`*`) for development. If you see CORS errors, check if the backend is actually running.
- **Connection Refused**: Ensure MongoDB is running.
