# ⛽ Fuel Price Tracker — Ireland

A community-powered, real-time fuel and EV charging price tracker for Ireland. Built on a 3D interactive globe using CesiumJS, with a FastAPI backend, PostgreSQL database, and Clerk authentication.

> 🚧 **Work in progress** — Analytics, cheapest-station-by-area, and price alerts coming soon.

---

## ✨ Features

- 🌍 Interactive 3D globe (CesiumJS) with satellite, street, and terrain views
- ⛽ Fuel station & ⚡ EV charging station markers with smart clustering
- 💰 Community price submissions (anonymous or verified)
- 📅 Date-observed tracking (up to 30 days back)
- 👍 Upvote / 👎 reject price credibility system
- 🔐 Clerk-based authentication for verified submissions
- 🔍 Station search by name with map fly-to
- 📊 Live submission counter
- 🗂️ Station type filtering (fuel / EV)

---

## 🏗️ Architecture

```mermaid
graph TD
    subgraph Browser["Browser (Vanilla JS)"]
        A[CesiumJS Globe]
        B[Station Search Modal]
        C[Price Submission Form]
        D[Clerk Auth SDK]
    end

    subgraph Frontend["Frontend (Static Files)"]
        E[index.html]
        F[styles.css]
        G[SVG Icons]
    end

    subgraph Backend["Backend (FastAPI)"]
        H["/api/config"]
        I["/api/stations"]
        J["/api/stations/search"]
        K["/api/prices"]
        L["/api/prices/:id/vote"]
        M["/api/stats"]

    end

    subgraph Data["Data Layer"]
        N[(PostgreSQL)]
        O[SQLAlchemy ORM]
    end

    subgraph External["External Services"]
        P[Clerk — Auth]
        Q[Cesium Ion — Imagery]
        R[Nominatim — Geocoding]
        S[OpenStreetMap — Tiles]
    end

    Browser -->|HTTP fetch| Backend
    Backend --> O --> N
    D <-->|JWT tokens| P
    A <-->|Token| Q
    A -->|Tile requests| S
    Browser -->|Search| R
````

---

## 🗂️ Project Structure

```
fuelpricetracker/
├── backend/
│   └── app/
│       ├── main.py            # FastAPI app entrypoint
│       ├── models.py          # SQLAlchemy models (Station, Price, Vote)
│       ├── schemas.py         # Pydantic request/response schemas
│       ├── database.py        # DB session & engine setup
│       └── routers/
│           ├── stations.py    # Station endpoints
│           ├── prices.py      # Price submission & voting
│           └── stats.py       # Aggregate stats
├── frontend/
│   ├── index.html             # Single-page app
│   ├── styles.css             # All UI styles
│   └── assets/
│       ├── icon-fuel.svg
│       └── icon-ev.svg
├── scripts/
│   └── seed_stations.py       # Import stations from OSM/CSV
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- A [Clerk](https://clerk.dev) account (free tier is fine)
- A [Cesium Ion](https://cesium.com/ion) account (free tier is fine)

### 1. Clone the repo

```bash
git clone https://github.com/0xchamin/fuelpricetracker.git
cd fuelpricetracker
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/fuelpricetracker
CLERK_SECRET_KEY=sk_...
CLERK_PUBLISHABLE_KEY=pk_...
CLERK_FRONTEND_API=https://your-clerk-frontend-api.clerk.accounts.dev
CESIUM_ION_TOKEN=your_cesium_token
```

### 3. Build and run

```bash
docker compose up --build
```

The app will be available at `http://localhost:8000`.

### 4. Seed station data

```bash
docker compose exec backend python scripts/seed_stations.py
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/config` | Returns public frontend config (keys, tokens) |
| `GET` | `/api/stations` | Stations within a bounding box |
| `GET` | `/api/stations/search` | Full-text station search with proximity sort |
| `GET` | `/api/prices/station/{id}` | Latest prices for a station |
| `POST` | `/api/prices` | Submit a new price (auth optional) |
| `POST` | `/api/prices/{id}/vote` | Upvote or reject a price (auth required) |
| `GET` | `/api/stats` | Aggregate stats (total prices, stations, etc.) |

---

## 🔐 Authentication & Trust Model

| Submission type | Badge | Criteria |
|-----------------|-------|----------|
| Anonymous | ❓ | No account required |
| Verified | ✅ | Signed-in Clerk user |
| Credible | ⭐ | Verified + community upvotes threshold met |

---

## 🗺️ Roadmap

- [ ] Cheapest stations by county / area
- [ ] Price trend charts per station
- [ ] Price alert subscriptions
- [ ] Mobile-responsive layout
- [ ] Admin moderation dashboard
- [ ] Stale price indicators (>48h)
- [ ] Railway production deployment

---

## 🤝 Contributing

Contributions are welcome! Please open an issue before submitting a PR to discuss what you'd like to change.

1. Fork the repo
2. Create your feature branch: `git checkout -b feat/your-feature`
3. Commit: `git commit -m "feat: describe your change"`
4. Push: `git push origin feat/your-feature`
5. Open a Pull Request

---

## 📄 License

```
MIT License

Copyright (c) 2026 fuelpricetracker contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgements

- [CesiumJS](https://cesium.com) — 3D globe rendering
- [Clerk](https://clerk.dev) — Authentication
- [OpenStreetMap](https://openstreetmap.org) — Map tiles & station data
- [Nominatim](https://nominatim.org) — Geocoding
- [FastAPI](https://fastapi.tiangolo.com) — Backend framework
