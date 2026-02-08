#!/bin/bash

# Manual API Tests with curl
# Usage: bash manual_tests.sh

BASE_URL="http://localhost:8000"
API_URL="$BASE_URL/api"

echo "========================================================================"
echo "MY JURIDIC ASSISTANT - MANUAL API TESTS"
echo "========================================================================"
echo ""

# Test 1: Health Check
echo "TEST 1: Health Check"
echo "--------------------"
curl -s "$BASE_URL/health" | python -m json.tool
echo ""
echo ""

# Test 2: Get Domains
echo "TEST 2: Get Domains"
echo "-------------------"
curl -s "$API_URL/domains" | python -m json.tool
echo ""
echo ""

# Test 3: Simple Question (No Pre-Questioning)
echo "TEST 3: Simple Question - Charges Recuperables"
echo "-----------------------------------------------"
curl -s -X POST "$API_URL/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quelles sont les charges recuperables en location ?",
    "domaine": "location",
    "enable_prequestioning": false
  }' | python -m json.tool
echo ""
echo ""

# Test 4: Question with Pre-Questioning
echo "TEST 4: Question with Pre-Questioning - Augmentation Loyer"
echo "-----------------------------------------------------------"
curl -s -X POST "$API_URL/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Mon proprietaire peut-il augmenter le loyer ?",
    "enable_prequestioning": true
  }' | python -m json.tool
echo ""
echo ""

# Test 5: Copropriete Question
echo "TEST 5: Copropriete - Charges Travaux"
echo "--------------------------------------"
curl -s -X POST "$API_URL/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Qui paie les travaux de toiture en copropriete ?",
    "domaine": "copropriete",
    "enable_prequestioning": false
  }' | python -m json.tool
echo ""
echo ""

# Test 6: Transaction Question
echo "TEST 6: Transaction - Diagnostics Obligatoires"
echo "-----------------------------------------------"
curl -s -X POST "$API_URL/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quels sont les diagnostics obligatoires pour une vente ?",
    "domaine": "transaction",
    "enable_prequestioning": false
  }' | python -m json.tool
echo ""
echo ""

echo "========================================================================"
echo "ALL MANUAL TESTS COMPLETED"
echo "========================================================================"
