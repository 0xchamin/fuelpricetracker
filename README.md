# ⛽ Fuel Price Tracker — Ireland

A community-powered, real-time fuel and EV charging price tracker for Ireland. Built as a **Progressive Web App (PWA)** with a Leaflet map, FastAPI backend, PostgreSQL/PostGIS database, and Clerk authentication.

> 🚧 **Work in progress** — Analytics, cheapest-station-by-area, and price alerts coming soon.

---

## ✨ Features

- 🗺️ Interactive map (Leaflet.js) with satellite and street views
- ⛽ Fuel station & ⚡ EV charging station markers with smart clustering
- 📱 **Mobile-first PWA** — install on iOS and Android, no App Store required
- 🔔 Push notification reminders to submit fuel prices
- 💰 Community price submissions (anonymous or verified)
- 📅 Date-observed tracking (up to 30 days back)
- 👍 Upvote / 👎 reject price credibility system
- 🔐 Clerk-based Google Sign-In for verified submissions
- 🔍 Dual-mode search — station name + area/location geocoding
- 📊 Live submission counter
- 🗂️ Station type filtering (fuel / EV / recent 72hrs)
- 📍 Locate me — one tap to fly to your current location

---

## 📱 Installing on Mobile (PWA)

No App Store needed! Install directly from your browser.

### iOS (Safari)
1. Open the app URL in **Safari**
2. Tap the **Share button** (box with arrow at the bottom)
3. Scroll down and tap **"Add to Home Screen"**
4. Tap **Add** — the app icon appears on your home screen

### Android (Chrome)
1. Open the app URL in **Chrome**
2. Tap the **three dots menu** (top right)
3. Tap **"Add to Home Screen"**
4. Tap **Add** — the app icon appears on your home screen

> Once installed, the app launches full-screen like a native app, works offline for cached content, and supports push notifications.

---

## 🏗️ Architecture & Technical Decisions

### Why PWA instead of native iOS/Android?

Building separate native apps (Swift + Kotlin) would require two codebases, two App Store accounts ($99/year for Apple alone), and significantly more development time. A PWA delivers:

- **Single codebase** for web, iOS, and Android
- **No App Store fees** — deploy instantly via Railway
- **Instant updates** — users always get the latest version on next load
- **Native-like experience** — full screen, home screen icon, push notifications
- **Lower barrier to entry** — users install in 2 taps, no download friction

The tradeoff is slightly less deep OS integration (e.g. no background sync), which is acceptable for this use case.

### Why Leaflet instead of CesiumJS?

The original prototype used CesiumJS (a 3D globe library). We migrated to Leaflet for the PWA because:

- **CesiumJS is ~10MB** loaded from CDN — too heavy for mobile
- **Leaflet is ~150KB** — loads instantly on mobile networks
- **3D globe is unnecessary** for fuel price discovery — a 2D map is clearer and faster
- **Leaflet.markercluster** handles thousands of station markers efficiently
- **Lower battery usage** — no WebGL 3D rendering on mobile

### Why Vanilla JS instead of React/Vue?

Keeping the frontend as a single `index.html` with vanilla JS means:

- **Zero build step** — no webpack, no bundler, no node_modules
- **Served directly by FastAPI** as a static file
- **Instant deployment** — change HTML, rebuild Docker, done
- **Smaller payload** — no framework overhead
- For the scale and complexity of this app, a framework adds friction without benefit

### Why FastAPI?

- **Async by default** — handles many concurrent map/station requests efficiently
- **Pydantic validation** — input validation on all price submissions is critical for data quality
- **Auto-generated OpenAPI docs** at `/docs` — free API documentation
- **SQLAlchemy async** — non-blocking DB queries keep the API responsive under load

### Why PostgreSQL + PostGIS?

- **PostGIS** enables native geospatial queries — `ST_Within` and `ST_MakeEnvelope` let us efficiently fetch only stations within the current map viewport (bounding box query), which is critical for performance at scale
- Without PostGIS, fetching stations by location would require loading all stations and filtering in Python — unacceptable at thousands of stations
- **Neon.tech** hosts the DB with serverless scaling and built-in PostGIS support

### Why Clerk for Auth?

- **Google Sign-In in minutes** — no custom OAuth implementation
- **JWT tokens** — stateless auth that works seamlessly with FastAPI
- **Supports both cookie and Bearer token** — works in browser and mobile PWA contexts
- **Free tier** is sufficient for early-stage data gathering
- Verified submissions (signed-in users) are flagged with ✅, building community trust in the data

### Why VAPID Push Notifications?

- **Web Push API** is the standard for PWA notifications on both Android and iOS (iOS 16.4+)
- **VAPID** (Voluntary Application Server Identification) provides end-to-end security for push messages without a third-party service
- **APScheduler** runs inside FastAPI to send scheduled reminders — no separate worker process needed at this scale
- User-controlled frequency (daily / 3 days / weekly / 2 weeks) respects user preferences and reduces churn

### Why Railway for Hosting?

- **Git-based deployment** — push to `pwa` branch, Railway auto-deploys
- **Free tier** sufficient for early stage
- **Environment variables** managed via Railway dashboard
- **No DevOps overhead** — no Kubernetes, no nginx config

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph Mobile["Mobile / Browser (PWA)"]
        A[Leaflet.js Map]
        B[Service Worker]
        C[Push Notifications]
        D[Clerk Auth SDK]
    end

    subgraph Frontend["Frontend (Static Files - served by FastAPI)"]
        E[index.html]
        F[styles.css]
        G[sw.js]
        H[manifest.json]
    end

    subgraph Backend["Backend (FastAPI - async)"]
        I["/api/config"]
        J["/api/stations (PostGIS bbox)"]
        K["/api/stations/search"]
        L["/api/prices"]
        M["/api/prices/:id/vote"]
        N["/api/stats"]
        O["/api/push/subscribe"]
        P["/api/push/vapid-public-key"]
        Q[APScheduler - push reminders]
    end

    subgraph Data["Data Layer"]
        R[(PostgreSQL + PostGIS - Neon.tech)]
        S[SQLAlchemy Async ORM]
    end

    subgraph External["External Services"]
        T[Clerk - Google Auth]
        U[Nominatim - Geocoding]
        V[OpenStreetMap - Map Tiles]
        W[Web Push API]
    end

    Mobile -->|HTTP fetch| Backend
    Backend --> S --> R
    D <-->|JWT tokens| T
    A -->|Tile requests| V
    Mobile -->|Location search| U
    Q -->|VAPID push| W -->|Notification| C
```

---

## 🗂️ Project Structure

```
fuelpricetracker/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI entrypoint, lifespan, scheduler
│       ├── models.py            # SQLAlchemy models (Station, Price, Vote, PushSubscription, User)
│       ├── schemas.py           # Pydantic request/response schemas
│       ├── database.py          # Async DB session, settings
│       ├── auth.py              # Clerk JWT verification
│       └── routers/
│           ├── stations.py      # Station endpoints (PostGIS bbox + search)
│           ├── prices.py        # Price submission & rate limiting
│           ├── votes.py         # Upvote/reject prices
│           └── push.py          # Push notification subscribe/unsubscribe
├── frontend/
│   ├── index.html               # Single-page PWA app
│   ├── styles.css               # All UI styles (mobile-first)
│   ├── sw.js                    # Service worker (caching + push)
│   ├── manifest.json            # PWA manifest
│   ├── icon-192.png             # PWA icon
│   ├── icon-512.png             # PWA icon
│   └── assets/
│       ├── icon-fuel.svg
│       └── icon-ev.svg
├── scripts/
│   └── seed_stations.py         # Seed stations from OpenStreetMap via Overpass API
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- A [Clerk](https://clerk.dev) account (free tier)
- A [Neon.tech](https://neon.tech) PostgreSQL database with PostGIS enabled

### 1. Clone the repo

```bash
git clone https://github.com/0xchamin/fuelpricetracker.git
cd fuelpricetracker
git checkout pwa
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql://user:password@host/fuelpricetracker?sslmode=require
CLERK_PUBLISHABLE_KEY=pk_...
CLERK_FRONTEND_API=https://your-clerk-frontend-api.clerk.accounts.dev
VAPID_PRIVATE_KEY=your_vapid_private_key
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_CLAIMS_EMAIL=mailto:your@email.com
```

### 3. Generate VAPID keys

```python
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption
import base64

key = ec.generate_private_key(ec.SECP256R1())
priv = base64.urlsafe_b64encode(key.private_bytes(Encoding.DER, PrivateFormat.PKCS8, NoEncryption())).decode()
pub = base64.urlsafe_b64encode(key.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)).decode()
print("VAPID_PRIVATE_KEY=", priv)
print("VAPID_PUBLIC_KEY=", pub)
```

### 4. Build and run

```bash
docker compose up --build
```

App available at `http://localhost:9098`

### 5. Seed station data

```bash
docker compose exec backend python -m app.scripts.seed_stations
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/config` | Public frontend config |
| `GET` | `/api/stations` | Stations within bounding box (PostGIS) |
| `GET` | `/api/stations/search` | Full-text search with proximity sort |
| `GET` | `/api/prices/station/{id}` | Latest prices for a station |
| `POST` | `/api/prices` | Submit a price (auth optional) |
| `POST` | `/api/prices/{id}/vote` | Upvote or reject a price (auth required) |
| `GET` | `/api/stats` | Aggregate stats |
| `GET` | `/api/prices/recent` | Recent price submissions |
| `GET` | `/api/push/vapid-public-key` | VAPID public key for push subscription |
| `POST` | `/api/push/subscribe` | Save push subscription (auth required) |
| `DELETE` | `/api/push/unsubscribe` | Remove push subscription (auth required) |

---

## 🔐 Authentication & Trust Model

| Submission type | Badge | Criteria |
|-----------------|-------|----------|
| Anonymous | ❓ | No account required, rate limited by IP |
| Verified | ✅ | Signed-in via Google (Clerk) |
| Credible | ⭐ | Verified + 5+ community upvotes |

---

## 🗺️ Roadmap

- [x] PWA with mobile install support
- [x] Push notification reminders
- [x] Leaflet map (replaced CesiumJS)
- [x] Dual-mode search (station + geocoding)
- [x] 72-hour recent submissions filter
- [x] Locate me button
- [x] Railway deployment
- [ ] Cheapest stations by county / area
- [ ] Price trend charts per station
- [ ] Stats & analytics page
- [ ] Admin moderation dashboard
- [ ] Stale price indicators (>48h)

---

## 🤝 Contributing

Contributions are very welcome! This is a community project — every contribution helps Irish drivers save money.

1. Fork the repo
2. Create your feature branch: `git checkout -b feat/your-feature`
3. Commit using conventional commits: `git commit -m "feat: describe your change"`
4. Push: `git push origin feat/your-feature`
5. Open a Pull Request

Please open an issue first to discuss significant changes.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

This project is open source and free to use, modify and distribute. We chose MIT because we believe open, frictionless collaboration is the best way to build tools that benefit everyone.
