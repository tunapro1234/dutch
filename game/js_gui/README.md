# Dutch Cabo - Advanced GUI

React-based web interface for the Dutch Cabo card game with beautiful card rendering and real-time game state updates.

## Features

🎮 **Beautiful Card Rendering**
- Realistic playing card design with suits and values
- Smooth animations for dealing, discarding, and flipping
- Card backs with "CABO" branding
- Known/unknown card indicators

🌐 **Real-time Game State**
- Live updates every 2 seconds
- Current player highlighting with pulse animation
- Turn counter and game status
- Dutch call notifications

📱 **Responsive Design**
- Mobile-friendly interface
- Adaptive card sizing
- Touch-friendly controls
- Modern gradient backgrounds

🤖 **AI Integration**
- SmartBayes vs SimpleAI gameplay
- Visual AI decision indicators
- Player statistics and scores
- Hand size tracking

## Quick Start

### Option 1: Through Dutch.py (Recommended)
```bash
python dutch.py --mode advanced-gui
```

### Option 2: Interactive Menu
```bash
python dutch.py
# Choose option 9: Advanced GUI
```

### Option 3: Direct Launch
```bash
cd game/js_gui
npm install
npm start
```

## Requirements

- **Node.js** (v14+) - [Download here](https://nodejs.org/)
- **npm** (comes with Node.js)
- **Python** backend with Flask (optional, demo mode available)

## Installation

1. **Install Node.js and npm**
   ```bash
   # Check if installed
   node --version
   npm --version
   ```

2. **Install Python dependencies** (for backend)
   ```bash
   pip install flask flask-cors
   ```

3. **Install React dependencies**
   ```bash
   cd game/js_gui
   npm install
   ```

## Architecture

```
React Frontend (Port 3000)
    ↕ HTTP/WebSocket
Python Backend (Port 5000)
    ↕ Direct Import
Dutch Cabo Game Engine
```

### Frontend (React)
- **App.js** - Main application with API integration
- **components/Card.js** - Beautiful card rendering
- **components/GameBoard.js** - Game layout and deck area
- **components/Player.js** - Player information and hands

### Backend (Python Flask)
- **game/api/server.py** - REST API endpoints
- Auto-play AI game loop
- Real-time game state serialization
- CORS enabled for frontend

## API Endpoints

- `GET /` - API information
- `POST /api/game/init` - Initialize new game
- `GET /api/game/state` - Get current game state
- `POST /api/game/action` - Handle game actions
- `GET /api/health` - Health check

## Development

### Frontend Development
```bash
cd game/js_gui
npm start
# Runs on http://localhost:3000
```

### Backend Development
```bash
python -c "from game.api.server import run_server; run_server(debug=True)"
# Runs on http://localhost:5000
```

### Testing
```bash
python scripts/test_advanced_gui.py
```

## Configuration

### Environment Variables
- `REACT_APP_API_URL` - Backend API URL (default: http://localhost:5000)

### Game Settings
- Turn delay: 2 seconds between AI moves
- Auto-refresh: 2 seconds for frontend updates
- Player types: SmartBayes (Gym), SimpleAI

## Troubleshooting

### Common Issues

**"node: command not found"**
- Install Node.js from https://nodejs.org/

**"npm install fails"**
- Delete `node_modules` folder and try again
- Check internet connection
- Try `npm cache clean --force`

**"Backend connection failed"**
- Install Flask: `pip install flask flask-cors`
- Check if port 5000 is free
- Backend runs in demo mode if unavailable

**"Cards not displaying correctly"**
- Check browser console for errors
- Ensure all CSS files are loaded
- Try refreshing the page

### Performance Tips

- Close other applications using ports 3000/5000
- Use modern browser (Chrome, Firefox, Safari, Edge)
- Ensure stable internet connection
- Keep terminal windows open during development

## Browser Support

- ✅ Chrome (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ❌ Internet Explorer

## Future Enhancements

- [ ] WebSocket real-time communication
- [ ] Interactive card clicking
- [ ] Sound effects and music
- [ ] Game replay system
- [ ] Tournament mode
- [ ] Custom AI configuration
- [ ] Multiple simultaneous games

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes to React components
4. Test with `npm start`
5. Submit pull request

## License

Same as main Dutch Cabo project. 