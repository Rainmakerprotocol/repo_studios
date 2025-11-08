# Command Center Viewer

A modern VS Code-styled progressive detail viewer for CommandView artifacts.

## Features

- **5 Zoom Levels**: Overview → Domain → Module → Functions → Neighborhood
- **8 View Packs**: Health, Dependency, Code Flow, State Effects, Quality Metrics, Coupling Insight, Risk & Assurance, Event Dynamics
- **Modern UI**: VS Code dark theme with professional styling
- **Interactive Diagrams**: Mermaid-based visualizations with click-to-drill functionality

## Quick Start

### Prerequisite: Build `selector.json`

The viewer expects a `selector.json` manifest under `/.repo_studios/command_center/reports/`. Generate it from the latest CommandView artifacts before launching the UI:

```bash
python -m command_center.viewer.generate_selector --repo-root .
```

Run the command from the repository root (or pass an explicit path with `--repo-root`).

### Option 1: Using the Python Server (Recommended)

The custom server serves from the repo root so the viewer can access CommandView reports:

```bash
# From the viewer directory
python serve_viewer.py

# Or specify a custom port
python serve_viewer.py --port 8080
```

Then open your browser to: **http://localhost:8000/.repo_studios/command_center/viewer/ui/**

**Note**: The server serves from repo root to enable access to `/.repo_studios/command_center/reports/`

### Option 2: UI-Only Mode (No Reports Access)

If you only want to test the UI without reports:

```bash
python serve_viewer.py --ui-only
```

Then open: **http://localhost:8000/**

### Option 3: Using Python's Built-in Server

```bash
# From the REPO ROOT (not the ui directory!)
cd /path/to/repo_studios
python -m http.server 8000
```

Then open: **http://localhost:8000/.repo_studios/command_center/viewer/ui/**

### Option 3: Using Any Web Server

Serve the `ui/` directory with any web server that supports:
- Proper MIME types for `.js` files (`application/javascript`)
- Proper MIME types for `.css` files (`text/css`)
- CORS headers (for local development)

## File Structure

```
viewer/
├── ui/
│   ├── index.html          # Main HTML structure
│   ├── viewer.css          # VS Code-styled CSS
│   └── viewer.js           # Application logic (3,439 lines)
├── refresh.py              # Python backend for data loading
├── serve_viewer.py         # Development server with proper MIME types
└── README.md               # This file
```

## Configuration

The viewer is configured via `window.viewerConfig` in `index.html`:

```javascript
window.viewerConfig = {
  // Base URL for reports
  reportsBaseUrl: '/.repo_studios/command_center/reports/',
  
  // Optional: API endpoint for selector refresh
  selectorApiEndpoint: '/api/selector',
};
```

**Path Options**:
- **Serving from repo root** (default): `'/.repo_studios/command_center/reports/'`
- **Serving from ui directory**: `'../../../reports/'`
- **Production API**: `'/api/reports/'`

## Troubleshooting

### Buttons Don't Work

**Cause**: JavaScript not loading or MIME type issues

**Solution**:
1. Use the provided `serve_viewer.py` script
2. Check browser console (F12) for errors
3. Verify `viewer.js` loads with `Content-Type: application/javascript`

### View Tabs Not Showing

**Cause**: Missing `#view-tabs` container or JavaScript not initializing

**Solution**:
1. Verify `<div id="view-tabs">` exists in HTML
2. Check console for `renderViewTabs()` errors
3. Ensure `bootstrap()` function completes successfully

### Blank Diagram Panel / 404 Errors

**Cause**: Reports path incorrect or data not available

**Solution**:
1. **Check server mode**: Use `serve_viewer.py` (serves from repo root)
2. **Verify reports exist**: Check `/.repo_studios/command_center/reports/` has data
3. **Check Network tab**: Look for 404s on JSON files
4. **Update config**: Adjust `reportsBaseUrl` in `index.html` if needed

### Refresh Button Shows Demo Data

**Cause**: No selector.json endpoint or reports not accessible

**Solution**:
1. Ensure reports directory is accessible via configured path
2. Create `selector.json` in reports directory (or use API endpoint)
3. Check console for fetch errors
4. Verify `window.viewerConfig.reportsBaseUrl` is correct

### Styling Looks Wrong

**Cause**: CSS not loading

**Solution**:
1. Check `viewer.css` loads with `Content-Type: text/css`
2. Hard refresh browser (Ctrl+F5 or Cmd+Shift+R)
3. Clear browser cache

### Module Loading Errors

**Cause**: Server not setting correct MIME type for JavaScript modules

**Solution**:
- Use `serve_viewer.py` which sets proper MIME types
- Or configure your server to serve `.js` files as `application/javascript`

## Browser Console Debugging

Open DevTools (F12) and check:

**Console Tab**: Look for JavaScript errors
```
✓ No errors = JavaScript loaded correctly
✗ "Failed to load resource" = Path or MIME type issue
✗ "Mermaid is not defined" = CDN blocked
```

**Network Tab**: Verify file loading
```
✓ viewer.css: 200 OK, text/css
✓ viewer.js: 200 OK, application/javascript
✓ mermaid.min.js: 200 OK from CDN
```

**Elements Tab**: Inspect DOM
```
✓ Buttons have event listeners attached
✓ Diagram container has content
✓ CSS classes applied correctly
```

## Development

### Modifying the UI

1. Edit `ui/viewer.css` for styling changes
2. Edit `ui/viewer.js` for functionality changes
3. Edit `ui/index.html` for structure changes
4. Refresh browser to see changes

### Adding New View Packs

Edit `viewer.js` and add to the `VIEW_PACKS` array (line 12):

```javascript
{
  id: "my-pack",
  title: "My Pack",
  views: [
    {
      id: "my-view",
      label: "My View",
      description: "Description of my view",
      status: "prototype",
      builder: "myViewBuilder",
      requirements: ["inventoryBasics"],
    }
  ]
}
```

Then implement the builder function in `VIEW_BUILDERS` (line 305).

## Architecture

- **State Management**: Global `state` object with reactive updates
- **Rendering Pipeline**: Data normalization → Level building → Mermaid generation
- **Interaction Model**: Click handlers registered during render
- **Data Loading**: Async fetch with caching for CommandView artifacts

## VS Code Theme

The viewer uses an authentic VS Code dark theme with:
- Background: `#1e1e1e`
- Sidebar: `#252526`
- Accent: `#007acc`
- Borders: `#3e3e42`
- Text: `#cccccc`

All colors are defined as CSS variables in `:root` for easy customization.