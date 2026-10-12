<#
.SYNOPSIS
    OVERCLOCK Cross-Platform Task Runner for Windows PowerShell
.DESCRIPTION
    Provides make-equivalent tasks on Windows without requiring make.exe.
#>
param (
    [Parameter(Position=0)]
    [string]$Task = "help"
)

switch ($Task.ToLower()) {
    "up" {
        docker compose -f infra/docker-compose.yml up -d
    }
    "down" {
        docker compose -f infra/docker-compose.yml down
    }
    "test-backend" {
        Set-Location apps/api
        uv run pytest --cov=app --cov-report=term-missing tests/
        Set-Location ../..
    }
    "test-frontend" {
        Set-Location apps/web
        npm test -- --run
        Set-Location ../..
    }
    "test" {
        Write-Host "Running backend tests..." -ForegroundColor Cyan
        Set-Location apps/api
        uv run pytest --cov=app --cov-report=term-missing tests/
        Set-Location ../..
        Write-Host "Running frontend tests..." -ForegroundColor Cyan
        Set-Location apps/web
        npm test -- --run
        Set-Location ../..
    }
    "lint" {
        Write-Host "Checking backend..." -ForegroundColor Cyan
        Set-Location apps/api
        uv run ruff check app tests
        uv run mypy app
        Set-Location ../..
        Write-Host "Checking frontend..." -ForegroundColor Cyan
        Set-Location apps/web
        npm run lint
        Set-Location ../..
    }
    "format" {
        Set-Location apps/api
        uv run ruff format app tests
        Set-Location ../..
        Set-Location apps/web
        npm run format
        Set-Location ../..
    }
    "dev-api" {
        Set-Location apps/api
        uv run uvicorn app.main:app --reload --port 8000
    }
    "dev-web" {
        Set-Location apps/web
        npm run dev
    }
    default {
        Write-Host "OVERCLOCK Task Runner (Windows)" -ForegroundColor Green
        Write-Host "Usage: .\run.ps1 [task]"
        Write-Host "Tasks: up, down, test, test-backend, test-frontend, lint, format, dev-api, dev-web"
    }
}
