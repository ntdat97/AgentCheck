# AgentCheck React Frontend

Modern React UI for the AgentCheck certificate verification system.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **Lucide React** - Icons

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Development

The development server runs on `http://localhost:3000` and proxies API requests to `http://localhost:8000`.

Make sure the Python backend is running:
```bash
# From project root
python -m api.main server
```

## Project Structure

```
ui/
├── public/
│   └── vite.svg          # Favicon
├── src/
│   ├── components/       # React components
│   │   ├── VerifyTab.tsx
│   │   ├── ReportsTab.tsx
│   │   ├── AboutTab.tsx
│   │   └── ResultsDisplay.tsx
│   ├── services/
│   │   └── api.ts        # API client
│   ├── types/
│   │   └── index.ts      # TypeScript types
│   ├── App.tsx           # Main app
│   ├── main.tsx          # Entry point
│   └── index.css         # Tailwind styles
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## Features

- 📄 **Upload Certificates** - Drag and drop PDF files
- 🔍 **Verification Workflow** - Real-time progress display
- 📊 **Results Dashboard** - Key metrics and detailed breakdown
- 📧 **Email Trail** - View outgoing requests and university replies
- 🤖 **AI Analysis** - See how the AI made its decision
- 📋 **Audit Trail** - Complete log of all actions
- 💾 **Export Reports** - Download as JSON

## API Proxy

In development mode, API requests are proxied:
- `/api/*` → `http://localhost:8000/*`

Configure in `vite.config.ts` if needed.
