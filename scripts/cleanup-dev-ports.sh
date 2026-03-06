#!/usr/bin/env sh
# Tax God - Free dev ports and kill heavy dev processes (uvicorn, vite, etc.)
# Same as: npm run cleanup:ports:aggressive

set -e
PORTS="8000 8001 5000 5050 5001 3000 8080 5173"
for p in $PORTS; do
  pid=$(lsof -ti:$p 2>/dev/null) || true
  if [ -n "$pid" ]; then
    kill -9 $pid 2>/dev/null || true
    echo "Killed port $p: $pid"
  fi
done
pkill -9 -f uvicorn 2>/dev/null && echo "Killed uvicorn" || true
pkill -9 -f vite 2>/dev/null && echo "Killed vite" || true
echo "Done."
