# Viewer Troubleshooting Guide

## Quick Diagnostic

1. **Open the diagnostic page**: http://127.0.0.1:8000/.repo_studios/command_center/viewer/ui/diagnostic.html
2. **Click "Run All Tests"** to verify configuration and network connectivity
3. **Check browser console** (F12) for detailed logging

## Recent Changes Made

### 1. Fixed DEFAULT_REPORTS_BASE_URL
- **Changed from**: `"../../reports/"` (relative path)
- **Changed to**: `"/.repo_studios/command_center/reports/"` (absolute path)
- **Why**: When serving from repo root, relative paths don't resolve correctly

### 2. Added Comprehensive Logging
Added console logging to track data flow:
- `[refreshSelectorData]` - Selector fetch process
- `[setEntries]` - Entry population
- `[renderSelector]` - DOM rendering
- `[selectOption]` - Option selection
- `[loadCommandViewPayloads]` - Artifact loading

### 3. Created Diagnostic Tools
- `diagnostic.html` - Interactive test page
- Console logging throughout the codebase

## Common Issues & Solutions

### Issue 1: Artifacts Not Populating

**Symptoms**: Sidebar shows no CommandView artifacts

**Check**:
1. Open browser console (F12)
2. Look for `[refreshSelectorData]` logs
3. Check if selector.json is being fetched successfully

**Possible Causes**:
- ❌ selector.json not found (404 error)
- ❌ selector.json in wrong location
- ❌ CORS or network error

**Solutions**:
```bash
# Verify selector.json exists
ls .repo_studios/command_center/reports/selector.json

# Regenerate if missing
python .repo_studios/command_center/viewer/generate_selector.py --repo-root .

# Check server is running from repo root
# Should see: "Serving from: C:\Users\genet\repo_studios"
```

### Issue 2: Zoom Levels Non-Responsive

**Symptoms**: Level buttons don't respond to clicks

**Check**:
1. Console for `[selectOption]` logs when clicking artifacts
2. Console for `[loadCommandViewPayloads]` logs
3. Network tab for artifact JSON files (should be 200 OK)

**Possible Causes**:
- ❌ Artifact JSON files not loading (404)
- ❌ Invalid JSON format
- ❌ Schema version mismatch

**Solutions**:
```javascript
// In browser console, check:
console.log(window.state);  // Should show loaded data
console.log(window.state.levels);  // Should show level data
console.log(window.state.normalizedData);  // Should show normalized data
```

### Issue 3: View Packs Non-Responsive

**Symptoms**: View pack buttons don't work

**Check**:
1. Console for `[renderViewPacks]` logs
2. Check if data requirements are met

**Possible Causes**:
- ❌ No artifact selected (view packs need data)
- ❌ Artifact missing required fields
- ❌ View requirements not satisfied

**Solutions**:
1. First select a CommandView artifact from the sidebar
2. Check console for requirement errors
3. Verify artifact has necessary data fields

## Debugging Workflow

### Step 1: Verify Server Setup
```bash
# Server should be running from repo root
cd C:\Users\genet\repo_studios
.venv\Scripts\python.exe .repo_studios\command_center\viewer\serve_viewer.py
```

Expected output:
```
Starting Command Center Viewer server...
Serving from: C:\Users\genet\repo_studios
Viewer URL: http://localhost:8000/.repo_studios/command_center/viewer/ui/
```

### Step 2: Verify selector.json
```bash
# Check file exists
cat .repo_studios/command_center/reports/selector.json

# Should show entries like:
# {
#   "entries": [
#     { "slug": "producers", "options": [...] },
#     { "slug": "scripts", "options": [...] }
#   ]
# }
```

### Step 3: Open Diagnostic Page
Navigate to: http://127.0.0.1:8000/.repo_studios/command_center/viewer/ui/diagnostic.html

Click "Run All Tests" and verify:
- ✓ window.viewerConfig exists
- ✓ reportsBaseUrl configured
- ✓ Selector fetch (200 OK)
- ✓ Selector data valid
- ✓ Artifact fetch (200 OK)
- ✓ Artifact data valid

### Step 4: Open Main Viewer
Navigate to: http://127.0.0.1:8000/.repo_studios/command_center/viewer/ui/

Open browser console (F12) and look for:
```
[refreshSelectorData] Config: {reportsBaseUrl: "/.repo_studios/command_center/reports/"}
[refreshSelectorData] Selector URL: /.repo_studios/command_center/reports/selector.json
[refreshSelectorData] Response status: 200 OK
[refreshSelectorData] Payload received: {entries: Array(2), generated_at: "..."}
[setEntries] Called with entries: (2) [{…}, {…}]
[renderSelector] Rendering 2 entries
[renderSelector] Adding option: producers (2025-11-06 10:14 UTC)
[renderSelector] Adding option: scripts (2025-11-05 20:49 UTC)
[renderSelector] Rendered 2 items
```

### Step 5: Click an Artifact
Click on "producers" or "scripts" in the sidebar.

Expected console output:
```
[selectOption] Selecting option: {slug: "producers", ...}
[loadCommandViewPayloads] Loading option: {slug: "producers", ...}
[loadCommandViewPayloads] Inventory URL: /.repo_studios/command_center/reports/index_scan/...
[loadCommandViewPayloads] Inventory loaded, files: 20
```

### Step 6: Verify Zoom Levels
After artifact loads, zoom level buttons should be enabled.

Check console for:
```
[renderLevelSidebar] ...
[updateLevelButtonsState] ...
```

## Network Tab Checklist

Open DevTools → Network tab, then refresh the page.

Should see successful (200 OK) requests for:
1. ✓ `index.html`
2. ✓ `viewer.css`
3. ✓ `viewer.js`
4. ✓ `mermaid.min.js` (from CDN)
5. ✓ `selector.json`
6. ✓ `producers_commandview_*.json` (when artifact clicked)
7. ✓ `producers_commandview_screening_*.json` (optional)

## Configuration Reference

### Current Configuration (index.html)
```javascript
window.viewerConfig = {
  reportsBaseUrl: '/.repo_studios/command_center/reports/',
};
```

### Current Default (viewer.js)
```javascript
const DEFAULT_REPORTS_BASE_URL = "/.repo_studios/command_center/reports/";
```

Both should point to the same location when serving from repo root.

## Still Not Working?

If after following all steps the viewer still doesn't work:

1. **Capture console output**: Copy all console logs
2. **Capture network errors**: Screenshot Network tab showing any 404s
3. **Check diagnostic results**: Screenshot diagnostic.html test results
4. **Verify file structure**:
   ```bash
   ls -R .repo_studios/command_center/reports/
   ```

The issue is likely one of:
- Path mismatch between config and actual file locations
- CORS or server configuration issue
- JavaScript error preventing execution
- Missing or corrupted artifact files