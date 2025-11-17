#!/bin/bash
# =============================================================================
# SCRIPT DE PRUEBAS PARA ENDPOINTS DE SENTINEL PRO
# =============================================================================
# Ejecuta este script después de iniciar el servidor con: python obd_server.py
# =============================================================================

echo "========================================="
echo "PRUEBAS DE ENDPOINTS - SENTINEL PRO"
echo "========================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:5000"

echo "🧪 Probando endpoint: GET /get_vehicles"
echo "Comando: curl -s $API_URL/get_vehicles"
curl -s $API_URL/get_vehicles | python3 -m json.tool
echo ""
echo "========================================="
echo ""

echo "🧪 Probando endpoint: POST /set_active_vehicle (debe devolver JSON, NO HTML)"
echo "Comando: curl -s -X POST $API_URL/set_active_vehicle -H 'Content-Type: application/json' -d '{\"vehicle_id\": 1}'"
RESPONSE=$(curl -s -X POST $API_URL/set_active_vehicle \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id": 1}')

echo "$RESPONSE" | python3 -m json.tool

# Verificar que NO contenga HTML
if echo "$RESPONSE" | grep -q "<!doctype\|<html"; then
    echo ""
    echo -e "${RED}❌ ERROR: El servidor devolvió HTML en lugar de JSON${NC}"
    echo ""
else
    echo ""
    echo -e "${GREEN}✅ ÉXITO: El servidor devolvió JSON correctamente${NC}"
    echo ""
fi

echo "========================================="
echo ""

echo "🧪 Probando endpoint inexistente (debe devolver 404 JSON)"
echo "Comando: curl -s $API_URL/endpoint_que_no_existe"
curl -s $API_URL/endpoint_que_no_existe | python3 -m json.tool
echo ""
echo "========================================="
echo ""

echo "🧪 Probando método incorrecto (debe devolver 405 JSON)"
echo "Comando: curl -s -X POST $API_URL/get_vehicles"
curl -s -X POST $API_URL/get_vehicles | python3 -m json.tool
echo ""
echo "========================================="
echo ""

echo -e "${YELLOW}📋 RESUMEN DE PRUEBAS COMPLETADO${NC}"
echo ""
echo "Si todos los endpoints devolvieron JSON (no HTML), entonces:"
echo "  ✅ El endpoint /set_active_vehicle está funcionando"
echo "  ✅ Los manejadores de errores 404/405/500 están activos"
echo "  ✅ No más errores de 'Unexpected token' en el frontend"
echo ""
