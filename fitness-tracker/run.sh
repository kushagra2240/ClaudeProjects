#!/bin/bash
IP=$(hostname -I | awk '{print $1}')
echo ""
echo " Fitness Tracker"
echo " ---------------"
echo " Local access:  http://localhost:8000"
echo " Phone access:  http://$IP:8000"
echo ""
echo " Starting server..."
echo ""
cd "$(dirname "$0")"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
