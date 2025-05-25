# Olympian AI Frontend

## 🏛️ Divine User Interface

The Olympian AI frontend is a Zeus-inspired interface that brings divine aesthetics to AI interaction.

## 🚀 Quick Start

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

## 🎨 Design System

### Divine Color Palette

- **Zeus Purple** (`#4B0082`): Primary divine color
- **Olympus Gold** (`#FFD700`): Secondary accent
- **Sky Blue** (`#87CEEB`): Tertiary accent
- **Marble White** (`#F8F8FF`): Light backgrounds

### Typography

- **Headers**: Cinzel (serif) - Divine authority
- **Body**: Philosopher (sans-serif) - Wisdom and clarity
- **Accents**: Uncial Antiqua (cursive) - Ancient mystique

### Components

- **Divine Cards**: Hover effects with golden glow
- **Thunder Buttons**: Ripple effects on interaction
- **Marble Backgrounds**: Subtle texture overlays
- **Lightning Animations**: Dynamic loading states

## 🏗️ Architecture

```
src/
├── components/       # Reusable UI components
│   ├── ui/          # Base UI components
│   └── Layout.tsx   # Main layout wrapper
├── contexts/        # React contexts
│   ├── WebSocketContext.tsx
│   └── ConfigContext.tsx
├── pages/           # Page components
│   ├── DivineDashboard.tsx
│   ├── DivineChatInterface.tsx
│   ├── ProjectWorkspace.tsx
│   ├── DynamicConfiguration.tsx
│   └── SystemMonitoring.tsx
├── lib/             # Utilities and API
│   ├── api.ts       # API client
│   └── utils.ts     # Helper functions
└── App.tsx          # Main app component
```

## ✨ Features

### Divine Dashboard
- Real-time service status
- System resource monitoring
- Quick action shortcuts
- Activity timeline

### Divine Dialogue (Chat)
- Streaming AI responses
- Conversation management
- Model selection
- Markdown rendering with syntax highlighting

### Sacred Projects
- Workspace configuration
- Context file management
- Tool selection
- Project templates

### Dynamic Configuration
- Auto-discovery visualization
- Service management
- Preference customization
- Security settings

### System Oracle
- Real-time metrics
- Resource optimization
- Process monitoring
- Performance graphs

## 🔌 WebSocket Integration

The frontend maintains a persistent WebSocket connection for:
- Real-time chat streaming
- Service discovery updates
- Configuration changes
- System metrics

## 🎨 Animations

- **Divine Glow**: Pulsing golden aura
- **Thunder Strike**: Lightning bolt effects
- **Float**: Gentle levitation
- **Shimmer**: Golden text effects

## 🛠️ Development

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

### Code Style

```bash
# Lint code
npm run lint

# Type check
npm run type-check
```

### Building

```bash
# Production build
npm run build

# Analyze bundle
npm run build -- --analyze
```

## 📝 Testing

```bash
# Run tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

## 🚀 Deployment

### Static Hosting

The build output can be deployed to any static hosting service:

```bash
npm run build
# Deploy dist/ folder
```

### Docker

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

## 🎆 Performance

- Lazy loading for routes
- Optimized bundle splitting
- Image optimization
- Service worker for offline support

---

May your interface shine with divine brilliance! ⚡