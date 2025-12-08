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
pnpm install

# Start development server
pnpm run dev

# Build for production
pnpm run build

# Preview production build
pnpm run preview
```

## Development

The development server runs on `http://localhost:3000`.

Make sure the Python backend is running:
```bash
# From project root
uvicorn api.main:app --reload
```

## Project Structure

```
ui/
├── public/
│   ├── sample/           # Sample PDFs
│   └── vite.svg          # Favicon
├── src/
│   ├── components/       # React components
│   │   ├── index.ts
│   │   ├── AboutTab.tsx
│   │   ├── ReportsTab.tsx
│   │   ├── ResultsDisplay.tsx
│   │   └── VerifyTab.tsx
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
