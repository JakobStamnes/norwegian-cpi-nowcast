# Norwegian CPI Nowcast - Deployment Status
**Last Updated**: 2026-06-29  
**Status**: 🔴 **OFFLINE - CRITICAL**

## System Health

| Component | Status | Notes |
|-----------|--------|-------|
| **Streamlit Dashboard** | 🔴 DOWN | Redirecting to auth (missing API_URL secret) |
| **FastAPI Backend** | ⚠️ NOT DEPLOYED | Ready in Docker, needs Render/Railway/Fly |
| **PostgreSQL Database** | ⚠️ NOT CONFIGURED | Needs Neon connection string |
| **GitHub Actions Workflows** | ✅ READY | Configured, waiting for secrets |
| **Code Quality** | ✅ PASSED | All linting checks pass (E, F, I, UP) |
| **Tests** | ✅ PASS | Unit tests configured (pytest) |

---

## Quick Start - 30 Minutes to Live

### 1. Get Required Credentials (10 min)

```bash
# PostgreSQL: Create free tier account
# Visit: https://neon.tech
# Copy your connection string: postgresql://user:pass@host/db

# Kassal API: Get free key
# Visit: https://kassal.app/api
# Copy your API key

# (Optional) OpenRouter: For AI maintenance job
# Visit: https://openrouter.ai
# Copy your API key
```

### 2. Set GitHub Secrets (5 min)

Go to: `https://github.com/Jakobkoding2/norwegian-cpi-nowcast`

**Settings → Secrets and variables → Actions → New repository secret:**

```
Name: DATABASE_URL
Value: postgresql://your:pass@host/db

Name: KASSAL_API_KEY
Value: your_kassal_key_here

Name: OPENROUTER_API_KEY (optional)
Value: your_openrouter_key_here
```

### 3. Deploy API (10 min - Pick One)

#### Option A: Render (Easiest, recommended)
1. Go to https://render.com
2. New → Web Service
3. Connect GitHub repo
4. Select: `norwegian-cpi-nowcast`
5. Settings:
   - Name: `norwegian-cpi-nowcast-api`
   - Root directory: (leave blank)
   - Runtime: `Python 3`
   - Build command: `pip install .`
   - Start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
6. Environment variables:
   - `DATABASE_URL` = (paste your Neon URL)
7. Create Web Service
8. **Copy your Render URL** (looks like: `https://xxx.onrender.com`)

#### Option B: Railway
Similar to Render; see Railway docs

#### Option C: Fly.io
```bash
cd api
fly launch  # select "norwegian-cpi-nowcast-api"
fly secrets set DATABASE_URL="postgresql://..."
fly deploy
```

### 4. Configure Streamlit Cloud (5 min)

1. Go to https://share.streamlit.io
2. Find app: `norwegian-cpi-nowcast`
3. Click **App settings** (top-right)
4. Go to **Secrets** tab
5. Add:
   ```toml
   API_URL = "https://your-api-url.onrender.com"
   ```
6. Click **Save** - app redeploys automatically

### 5. Verify Live

```bash
# Check API health
curl https://your-api-url.onrender.com/health
# Should respond: OK (200)

# Check dashboard
open https://norwegian-c-deugpypcrvpupxaxgybb3l.streamlit.app
# Should show dashboard (not auth page)
```

### 6. Trigger First Run

Go to: `https://github.com/Jakobkoding2/norwegian-cpi-nowcast/actions`

- Click `Daily Price Scraper`
- Click `Run workflow`
- Wait ~2 minutes

This populates the database with today's prices.

---

## What Happens Next

### Daily (02:00 UTC)
- `scrape.yml` runs → fetches prices from Kassal/Oda
- Computes Laspeyres index → stores in `daily_index` table
- Dashboard auto-refreshes

### Monthly (12th, 06:00 UTC)
- `retrain.yml` runs → fetches SSB print
- Trains XGBoost model → stores in `nowcast` table
- Predictions available via API + dashboard

### Daily (03:00 UTC - optional)
- `daily-light.yml` runs → AI maintenance
- Fixes code style, updates comments, finds minor bugs
- Requires `OPENROUTER_API_KEY` (can skip)

---

## Troubleshooting

### Dashboard shows "Server error"
```bash
# Check API is deployed and running
curl https://your-api.onrender.com/health

# Check Streamlit Cloud logs
# Settings → Logs tab

# Verify API_URL secret in Streamlit
# Settings → Secrets (should see API_URL)
```

### API returns 503 "Database not ready"
```bash
# Check DATABASE_URL is set in Render
# Render dashboard → Environment → DATABASE_URL

# Test PostgreSQL connection
psql "postgresql://user:pass@host/db" -c "SELECT 1"
```

### Scraper fails with "KASSAL_API_KEY not found"
```bash
# Check secret is set in GitHub
# Settings → Secrets and variables → Actions

# Re-run workflow after setting secret
# Actions → Daily Price Scraper → Run workflow
```

### Model predictions are old
```bash
# Check retrain.yml ran on 12th
# Actions → Retrain workflow

# Manual retrain (if needed)
python -m model.train
python -m model.predict
```

---

## Architecture

```
┌─────────────────────┐
│  GitHub Actions     │
│  • scrape.yml (02:00 UTC)
│  • retrain.yml (12th @06:00)
│  • daily-light.yml (03:00 UTC)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Data Pipeline                      │
│  1. Kassal.app + Oda.com APIs       │
│  2. Promo filter (30-day modal)     │
│  3. Laspeyres index (weighted avg)  │
│  4. XGBoost nowcaster (predictions) │
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Neon PostgreSQL (free tier)         │
│  • raw_prices (daily observations)   │
│  • daily_index (computed indices)    │
│  • nowcast (predictions)             │
│  • ssb_official (SSB monthly prints) │
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  FastAPI Backend (Render/Railway/Fly)│
│  GET /index → daily prices           │
│  GET /nowcast/latest → predictions   │
│  GET /ssb → official SSB             │
│  GET /breakdown/{date} → COICOP      │
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Streamlit Dashboard (Streamlit Cloud)
│  • Live Laspeyres index chart        │
│  • Nowcast predictions + CI band     │
│  • COICOP category breakdown         │
│  • Accuracy metrics                  │
└──────────────────────────────────────┘
```

---

## Model Performance

Backtested on 551 months (1979–2025):

| Model | MAE (pp) | vs Naive |
|-------|----------|----------|
| Naive (persist) | 1.20 | — |
| **XGBoost** | **0.72** | **−40%** |
| XGBoost + live data | *~0.30–0.40* | *−65–75%* (expected) |

**Feature Importances:**
- lag-12 (40%) — last year's MoM
- July window (20%) — mid-year hike
- Feb window (16%) — winter hike
- lag-1 (14%) — last month
- lag-2 (10%) — two months ago

---

## Product Coverage

72 SKUs across 9 COICOP categories (SSB Table 14700, Jan 2026 weights):

| Category | Weight | Examples |
|----------|--------|----------|
| Bread & Cereals | 18% | Oatmeal, flour, knackar |
| Meat | 24% | Bacon, ground beef, chicken |
| Fish & Seafood | 10% | Salmon, mackerel, sardines |
| Milk, Cheese, Eggs | 16% | Whole milk, Norvegia, eggs |
| Oils & Fats | 3% | Sunflower oil, margarine |
| Fruit | 6% | Pink Lady apples, oranges |
| Vegetables | 7% | Carrots, lettuce, broccoli |
| Sugar & Confectionery | 8% | Chocolate, candy, sugar |
| Coffee, Tea, Condiments | 8% | Coffee, mayo, mustard |

---

## Data Sources

- **Prices**: Kassal.app API + Oda.com (daily, free)
- **Basket weights**: SSB Table 14700 (official)
- **SSB prints**: SSB StatBank Table 03013 (monthly)
- **FX rates**: Norges Bank API (EUR/NOK)

---

## Support & Documentation

- **GitHub**: https://github.com/Jakobkoding2/norwegian-cpi-nowcast
- **Dashboard**: https://norwegian-c-deugpypcrvpupxaxgybb3l.streamlit.app
- **Model**: XGBoost Regressor, `max_depth=2`, L2 regularization
- **Stack**: Python 3.11, FastAPI, Streamlit, PostgreSQL, XGBoost

---

## Next Steps

1. ✅ **DONE**: Code quality fixed (all linting passes)
2. ⏭️ **TODO**: Set GitHub secrets (DATABASE_URL, KASSAL_API_KEY)
3. ⏭️ **TODO**: Deploy API (Render/Railway/Fly)
4. ⏭️ **TODO**: Add API_URL to Streamlit Cloud
5. ⏭️ **TODO**: Trigger first scrape via GitHub Actions
6. ⏭️ **TODO**: Verify dashboard is live

---

**Questions?** Check the GitHub repo issues or contact the maintainer.
