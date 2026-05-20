# AI Trend Radar

Nền tảng theo dõi và đánh giá xu hướng AI — tổng hợp từ GitHub, Product Hunt, Reddit, YouTube. Chấm điểm độ hot, tăng trưởng và độ phù hợp theo nhu cầu người dùng.

## Quick Start

### Yêu cầu

- Node.js 20+
- pnpm 9+
- PostgreSQL 15+

### Setup

```bash
# 1. Install tất cả packages
pnpm install

# 2. Tạo database
createdb aitrendradar

# 3. Copy env và điền DATABASE_URL
cp .env.example .env
# Chỉnh DATABASE_URL=postgresql://user:password@localhost:5432/aitrendradar

# 4. Copy env cho frontend
cp apps/web/.env.local.example apps/web/.env.local

# 5. Push DB schema
pnpm --filter @ai-trend-radar/api db:push

# 6. Seed demo data (15 AI tools)
pnpm --filter @ai-trend-radar/crawler import:trends
```

### Chạy dev

Mở 3 terminal riêng:

```bash
# Terminal 1 — Scoring service (port 3001)
pnpm --filter @ai-trend-radar/scoring dev

# Terminal 2 — Backend API (port 3000)
pnpm --filter @ai-trend-radar/api dev

# Terminal 3 — Frontend (port 3002)
pnpm --filter @ai-trend-radar/web dev
```

Mở: http://localhost:3002

## Cấu trúc

```
apps/
  web/                    # Next.js frontend (User 1)
services/
  api/                    # Express + Prisma REST API (User 2)
  crawler/                # GitHub crawler + manual import (User 3)
  scoring/                # Scoring engine — 7 scores + Fit Score (User 5)
packages/
  shared/                 # TypeScript types dùng chung
tests/
  e2e/                    # Playwright E2E + API contract tests (User 4)
```

## Tính năng MVP

| Trang | Mô tả |
|-------|-------|
| `/` | Dashboard "Hot This Week" — RadarViz + hero cards + trend feed |
| `/tools` | Danh sách tất cả tool với filter/sort/search |
| `/trends/[id]` | Tool detail — score breakdown, pros/cons, similar tools |
| `/compare` | So sánh 2–5 tool side by side |
| `/for-you` | Need Matcher — nhập nhu cầu → nhận Fit Score |
| `/github` | GitHub repo trending |

## API Endpoints

Base URL: `http://localhost:3000/api`

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/trends` | List + filter + paginate |
| GET | `/trends/:id` | Chi tiết + similar |
| POST | `/compare` | So sánh 2–5 trends |
| POST | `/match` | Need Matcher |
| POST | `/ingest` | Nhận raw items từ crawler |
| POST | `/admin/trends` | Nhập tay |

## Commands

```bash
# Import demo data
pnpm --filter @ai-trend-radar/crawler import:trends

# Crawl GitHub (cần GITHUB_TOKEN)
pnpm --filter @ai-trend-radar/crawler github:crawl

# Chạy API contract tests
API_URL=http://localhost:3000/api pnpm --filter @ai-trend-radar/e2e test:api

# Chạy E2E tests
BASE_URL=http://localhost:3002 pnpm --filter @ai-trend-radar/e2e test:e2e

# Mở Prisma Studio
pnpm --filter @ai-trend-radar/api db:studio
```
