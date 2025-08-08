# Startup Discovery Frontend

A React-based frontend for the Startup Discovery RAG application.

## Features

- **Search Interface**: Natural language search for startups
- **Q&A Interface**: Ask questions about startups and get AI-powered answers
- **Modern UI**: Clean, responsive design with Tailwind CSS
- **Real-time Results**: Instant search and Q&A responses

## Quick Start

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Start Development Server**:
   ```bash
   npm run dev
   ```

3. **Build for Production**:
   ```bash
   npm run build
   ```

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`:

- `GET /search?q=query` - Search startups
- `GET /ask?q=query` - Get Q&A responses

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **HTTP Client**: Axios
