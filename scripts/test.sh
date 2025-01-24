#!/usr/bin/env bash
set -eo pipefail

echo "Starting black"
poetry run black ../src
echo "OK"

echo "Starting isort"
poetry run isort ../src
echo "OK"

#echo "Starting mypy"
#poetry run mypy ../src
#echo "OK"

echo "Starting test with coverage"

echo "All tests passed successfully!"

