#!/usr/bin/env bash
check() { curl -sf "$2" >/dev/null 2>&1 && echo "✓ $1" || echo "✗ $1"; }
check "Backend" "http://localhost:8000/health"
check "Frontend" "http://localhost:3000"
