# Travel Agent

A premium, AI-powered travel assistant specialized in planning trips across China. This agent leverages the Model Context Protocol (MCP) to access real-time data for maps, railways, and local discovery, providing a high-density, real-time planning experience.

## Key Features

- **Real-Time Streaming**: Live agent status updates via Server-Sent Events (SSE) as the AI calls various tools.
- **Smart Railway Integration**: Search for bullet trains and "pin" specific transits directly into your visual itinerary.
- **High-Density UI**: A "cockpit-mode" interface using the "Taste-Skill" aesthetic, emphasizing data density and micro-interactions.
- **Intelligent Synthesis**: Consolidate pinned places and trains into a logical, day-by-day schedule optimized for local travel.

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, OpenAI SDK (OpenRouter), Pydantic v2.
- **Frontend**: React 18, Vite, TypeScript, Vanilla CSS.
- **Architecture**: Model Context Protocol (MCP) for tool-calling resiliency.
- **Icons & UI**: Lucide React, Glassmorphism design system.
- **Date Management**: `date-fns`, `react-datepicker`.

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- [OpenRouter API Key](https://openrouter.ai/)
- Access to MCP servers (Tavily, Amap, Railway)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/travel-mcp.git
cd travel-mcp
```

### 2. Backend Setup

```bash
cd backend
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Then edit .env with your LLM_API_KEY and MCP URLs
```

### 3. Frontend Setup

```bash
cd ../frontend
npm install
```

### 4. Running the Application

**Terminal 1: Backend**
```bash
cd backend
uvicorn main:app --reload
```

**Terminal 2: Frontend**
```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) to start planning your trip.

## Architecture

### Directory Structure

```
├── backend/
│   ├── services/       # Core logic: Chat, Synthesis, LLM, Trip
│   ├── models.py       # Pydantic data schemas
│   ├── mcp_client.py   # SSE-based MCP connectivity
│   ├── mcp_manager.py  # Tool aggregation & calling
│   └── main.py         # FastAPI entry point
├── frontend/
│   ├── src/
│   │   ├── components/ # UI Components (POICard, TrainList, etc.)
│   │   ├── services/   # API & Streaming logic
│   │   └── types/      # TypeScript interfaces
│   └── index.css       # Core design system
└── .gitignore          # Root exclusion rules
```

### Data Flow

1. **Initialization**: User selects cities → Backend initializes trip state.
2. **Discovery**: User chats → LLM calls MCP tools → Results stream to Frontend as Widgets.
3. **Pinning**: User clicks "Add" → Local state tracks "Placeholder" places and transits.
4. **Synthesis**: User clicks "Synthesize" → Backend LLM builds chronological schedule respecting pinned transits.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LLM_API_KEY` | OpenRouter or OpenAI API Key |
| `LLM_MODEL` | The model to use (default: `anthropic/claude-3.5-sonnet`) |
| `TAVILY_SSE_URL` | Tavily Search MCP endpoint |
| `AMAP_SSE_URL` | Amap Maps MCP endpoint |
| `RAILWAY_SSE_URL` | Railway Search MCP endpoint |

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start frontend development server |
| `uvicorn main:app --reload` | Start backend with hot reload |
| `npm run build` | Build frontend for production |
| `pytest` | Run backend tests (requires pytest) |
