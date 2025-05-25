# Contributing to Olympian AI

## 🏛️ Welcome, Divine Contributor!

We're thrilled that you want to contribute to Olympian AI! This document provides guidelines for contributing to the project.

## 🔱 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Respect differing viewpoints and experiences

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/olympian-ai-dynamic.git
   cd olympian-ai-dynamic
   ```

3. Set up the development environment:
   ```bash
   # Backend
   cd backend
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   
   # Frontend
   cd ../frontend
   npm install
   ```

## 🎯 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### 4. Commit Your Changes

We follow conventional commits:

```bash
git commit -m "feat: add divine thunder animation"
git commit -m "fix: resolve WebSocket reconnection issue"
git commit -m "docs: update API documentation"
```

Commit types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## 📋 Pull Request Guidelines

### PR Title

Follow the same convention as commits:
- `feat: add divine thunder animation`
- `fix: resolve WebSocket reconnection issue`

### PR Description

Include:
- What changes were made
- Why these changes were made
- How to test the changes
- Screenshots (for UI changes)
- Breaking changes (if any)

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated (if needed)
- [ ] No console errors or warnings
- [ ] Responsive design maintained
- [ ] Accessibility considered

## 🎨 Code Style Guidelines

### Python (Backend)

- Use Black for formatting
- Use type hints
- Follow PEP 8
- Maximum line length: 100 characters

```python
# Good
async def discover_services(self, service_type: str) -> Dict[str, Any]:
    """Discover services of a specific type."""
    ...

# Bad
async def discover_services(self, service_type):
    ...
```

### TypeScript/React (Frontend)

- Use functional components with hooks
- Use TypeScript strictly
- Follow ESLint rules
- Use descriptive variable names

```typescript
// Good
interface ServiceStatus {
  type: string
  status: 'connected' | 'disconnected' | 'error'
}

// Bad
interface ServiceStatus {
  type: any
  status: string
}
```

### CSS/Tailwind

- Use Tailwind utility classes
- Follow the divine theme system
- Keep custom CSS minimal
- Use CSS variables for theming

## 🧑‍💻 Areas for Contribution

### High Priority

1. **Service Discovery Plugins**
   - Add support for new services
   - Improve discovery algorithms
   - Add service health checks

2. **UI/UX Improvements**
   - Enhance divine animations
   - Improve mobile responsiveness
   - Add accessibility features

3. **Documentation**
   - API documentation
   - User guides
   - Video tutorials

### Feature Ideas

- Voice input/output integration
- Multi-language support
- Plugin system for custom tools
- Advanced prompt templates
- Collaborative features

## 🔧 Development Tips

### Backend Development

```bash
# Run with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run specific tests
pytest tests/test_discovery.py -v

# Check code coverage
pytest --cov=app --cov-report=html
```

### Frontend Development

```bash
# Start dev server
npm run dev

# Type checking
npm run type-check

# Build for production
npm run build
```

### Using Docker

```bash
# Build and run all services
docker-compose up --build

# Run specific service
docker-compose up backend

# View logs
docker-compose logs -f backend
```

## 📦 Project Structure

```
olympian-ai-dynamic/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Core functionality
│   │   └── services/     # Service integrations
│   ├── tests/           # Test files
│   └── main.py          # Entry point
└── frontend/
    ├── src/
    │   ├── components/   # React components
    │   ├── contexts/     # React contexts
    │   ├── pages/        # Page components
    │   └── lib/          # Utilities
    └── public/           # Static assets
```

## 💡 Need Help?

- Check existing issues and PRs
- Join our Discord community
- Ask questions in GitHub Discussions
- Review the documentation

## 🎆 Recognition

Contributors will be:
- Listed in our README
- Mentioned in release notes
- Given special Discord roles
- Invited to contributor meetings

---

Thank you for contributing to Olympian AI! May the gods smile upon your code! ⚡