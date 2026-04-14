#!/bin/bash

# Start backend
cd ~/projects/disc-golf-scorecard/backend
poetry run uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
cd ~/projects/disc-golf-scorecard/frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ Backend running on http://localhost:8000"
echo "✅ Frontend running on http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"

# Stop both on Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait