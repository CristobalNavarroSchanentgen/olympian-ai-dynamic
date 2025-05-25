# Sacred Ollama Endpoint Management 🏛️

The Sacred Ollama Endpoint Management system provides divine control over your Ollama configurations in the Olympian AI Dynamic interface. This comprehensive guide will walk you through the sacred art of endpoint management.

## ✨ Features Overview

### Divine Endpoint Control
- **Add Custom Oracles**: Register new Ollama endpoints beyond auto-discovery
- **Test Connectivity**: Verify divine connections with real-time testing
- **Priority Management**: Set endpoint priorities for optimal divine ordering
- **Primary Oracle Selection**: Designate your primary Ollama endpoint
- **Status Monitoring**: Real-time connection status and health monitoring

### Sacred Interface Elements
- **Real-time Testing**: Test individual endpoints or all at once
- **Visual Status Indicators**: Clear divine status visualization
- **Responsive Design**: Divine experience across all devices
- **Drag & Drop Reordering**: Intuitive endpoint priority management
- **Detailed Metrics**: Response times, model counts, and version information

## 🌟 Accessing Sacred Settings

1. Navigate to the **Sacred Configuration** page in your Olympian AI interface
2. Click on the **Sacred Ollama** tab
3. Behold the divine endpoint management interface

## ⚡ Adding New Ollama Endpoints

### Via Sacred Interface
1. Click the **"Add Oracle"** button
2. Fill in the sacred details:
   - **Endpoint URL**: `http://your-ollama-host:11434`
   - **Display Name**: Custom name for your oracle
   - **Priority**: 0-100 (higher = more divine priority)
   - **Timeout**: Connection timeout in seconds
3. Toggle **"Enable endpoint immediately"** if desired
4. Click **"Register Oracle"** to complete the sacred ritual

### Supported URL Formats
```
http://localhost:11434          # Local instance
http://192.168.1.100:11434     # Network instance
https://ollama.example.com     # Remote secure instance
my-ollama-server:11434         # Auto-adds http://
```

## 🔥 Testing Divine Connectivity

### Individual Endpoint Testing
- Click the **Test** button (🧪) next to any endpoint
- View real-time status updates
- See detailed metrics:
  - Response time
  - Available models count
  - Ollama version
  - Error messages (if any)

### Bulk Divine Testing
- Click **"Test All"** to test all endpoints simultaneously
- Get comprehensive connectivity overview
- Identify problematic oracles quickly

## 👑 Primary Oracle Management

### Setting Primary Endpoint
1. Ensure the endpoint is enabled and responding
2. Click the **Star** icon (⭐) next to your chosen oracle
3. The endpoint becomes your **Primary Oracle** (highlighted in divine gold)

### Primary Oracle Benefits
- Used as default for new conversations
- Prioritized in API calls
- Clearly marked with sacred golden styling
- Appears first in endpoint lists

## ⚙️ Advanced Configuration

### Priority System
Endpoints are ordered by:
1. **Primary Oracle** (always first)
2. **Priority Score** (0-100, higher first)
3. **Connection Status** (connected first)
4. **Name** (alphabetical)

### Endpoint Sources
- **Discovered**: Auto-detected by divine discovery
- **Custom**: Manually added sacred oracles

### Status Indicators
- 🟢 **Connected**: Oracle is responding divinely
- 🔴 **Error**: Connection failed or oracle is unresponsive
- 🔵 **Testing**: Currently testing divine connection
- ⚪ **Unknown**: Status not yet determined

## 🛠️ API Integration

### Backend Endpoints
```
GET    /api/ollama/config/endpoints          # List all endpoints
POST   /api/ollama/config/endpoints          # Add new endpoint
PUT    /api/ollama/config/endpoints/{url}    # Update endpoint
DELETE /api/ollama/config/endpoints/{url}    # Remove endpoint
POST   /api/ollama/config/endpoints/test     # Test single endpoint
POST   /api/ollama/config/endpoints/test-all # Test all endpoints
POST   /api/ollama/config/endpoints/set-primary # Set primary oracle
POST   /api/ollama/config/discover           # Trigger discovery
```

### WebSocket Notifications
Real-time updates are pushed via WebSocket for:
- Endpoint additions/removals
- Connectivity test results
- Primary oracle changes
- Discovery completion

## 🎨 UI Components

### SacredOllamaEndpoints Component
The main component provides:
- **Status Overview Cards**: Total, connected, primary, and error counts
- **Add Oracle Form**: Expandable form for new endpoint registration
- **Endpoint List**: Sortable, interactive list of all oracles
- **Bulk Actions**: Test all, refresh, and discovery triggers

### Visual Design Elements
- **Divine Theming**: Olympus gold and Zeus blue color scheme
- **Animated Interactions**: Smooth transitions and hover effects
- **Status-based Styling**: Color-coded endpoint status indication
- **Responsive Layout**: Adapts to all screen sizes

## 🔧 Configuration Storage

### User Preferences
Stored in `user_preferences.custom_endpoints`:
```json
{
  "custom_endpoints": [
    "http://localhost:11434",
    "http://remote-ollama:11434"
  ]
}
```

### Manual Overrides
Detailed configurations in `user_preferences.manual_overrides.ollama_endpoints`:
```json
{
  "ollama_endpoints": {
    "http://localhost:11434": {
      "name": "Local Divine Oracle",
      "enabled": true,
      "timeout": 30,
      "priority": 10,
      "added_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

## 🚀 Best Practices

### Endpoint Naming
- Use descriptive names: "Production Ollama", "Local Dev"
- Include location or purpose
- Keep names concise for UI display

### Priority Assignment
- **90-100**: Production/critical endpoints
- **50-89**: Development/testing endpoints
- **10-49**: Backup/fallback endpoints
- **0-9**: Experimental oracles

### Security Considerations
- Use HTTPS for remote endpoints when possible
- Configure appropriate timeouts for network conditions
- Regularly test endpoint connectivity
- Monitor for unauthorized access

## 🐛 Troubleshooting

### Common Issues

#### "Connection Failed" Errors
1. Verify Ollama is running on target host
2. Check firewall/network connectivity
3. Confirm correct port (default: 11434)
4. Test with curl: `curl http://your-host:11434/api/version`

#### "Timeout" Errors
1. Increase timeout value in endpoint settings
2. Check network latency to target host
3. Verify Ollama isn't overloaded

#### "Models Not Loading"
1. Ensure Ollama has models installed
2. Check Ollama logs for errors
3. Verify API access permissions

### Debug Mode
Enable debug logging in the backend to see detailed endpoint interaction logs:
```bash
export DEBUG=true
export LOG_LEVEL=debug
```

## 📊 Monitoring & Metrics

### Real-time Metrics
- Response time tracking
- Model availability counts
- Connection success rates
- Error frequency analysis

### Health Monitoring
- Automatic periodic health checks
- Notification of endpoint failures
- Historical connection data

## 🔮 Future Enhancements

### Planned Features
- Load balancing across multiple endpoints
- Automatic failover capabilities
- Endpoint performance analytics
- Model-specific routing
- Advanced security features

### Integration Roadmap
- Kubernetes service discovery
- Docker Compose integration
- Cloud provider auto-discovery
- Enterprise SSO integration

## 💡 Tips & Tricks

### Power User Features
- Use keyboard shortcuts for quick testing
- Drag endpoints to reorder priorities
- Double-click endpoint names to edit inline
- Use bulk operations for efficiency

### Performance Optimization
- Set appropriate priorities for fastest endpoints
- Use local endpoints when possible
- Configure reasonable timeouts
- Monitor endpoint health regularly

---

*May your Ollama oracles respond swiftly and your divine configurations bring forth intelligent conversations! 🏛️⚡*
