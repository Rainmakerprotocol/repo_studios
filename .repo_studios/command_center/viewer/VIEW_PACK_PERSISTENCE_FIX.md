# View Pack Selection Persistence Fix

## Problem Summary

When switching between CommandView artifacts or changing zoom levels, the active View Pack selection was being reset to the default "Function Inventory Overview" instead of maintaining the user's last selected view.

### User Experience Issue

1. User selects a View Pack (e.g., "Screening Signal Timeline")
2. User switches to a different CommandView artifact
3. View Pack resets to "Function Inventory Overview" ❌
4. User changes zoom level
5. View Pack resets again ❌

### Expected Behavior

The View Pack selection should persist when:

- Switching between CommandView artifacts
- Changing zoom levels
- The same view is available in the new context

## Root Cause

The viewer had a selection memory system that persisted:

- Current zoom level (`currentLevel`)
- Level selections (`rootId`, `domainId`, `moduleId`, `functionId`)

However, it was **NOT** persisting:

- Active view pack selections (`activeViews`)
- Active view index (`activeViewIndex`)

## Solution

Modified two functions in `viewer.js`:

### 1. `persistActiveSelectionMemory()` (lines 605-630)

**Added** persistence of view pack state:

```javascript
const memory = {
  currentLevel: state.currentLevel,
  selections: { ... },
  activeViews: state.activeViews.length > 0 ? [...state.activeViews] : null,  // NEW
  activeViewIndex: state.activeViewIndex >= 0 ? state.activeViewIndex : null, // NEW
};
```

### 2. `restoreSelectionMemory()` (lines 632-673)

**Added** restoration of view pack state:

```javascript
// Restore active view pack selection
if (memory.activeViews && Array.isArray(memory.activeViews) && memory.activeViews.length > 0) {
  state.activeViews = [...memory.activeViews];
  state.activeViewIndex = memory.activeViewIndex ?? 0;
  console.log("[restoreSelectionMemory] Restored active views:", state.activeViews, "index:", state.activeViewIndex);
}
```

## How It Works

### Selection Flow

1. **Before switching artifacts/levels**: `persistActiveSelectionMemory()` saves current state including active views
2. **During switch**: `clearActiveViewSelection()` temporarily clears the view selection
3. **After loading new data**: `restoreSelectionMemory()` restores the saved view selection
4. **Rendering**: `renderViewPacks()` and `renderCurrentLevel()` use the restored state

### Memory Key System

The viewer uses a memory key system based on:

- Artifact slug (e.g., "scripts", ".repo_studios")
- Relative path (for more specific matching)

This allows the same view pack selection to be restored when returning to the same artifact.

## Testing

To verify the fix works:

1. **Test Case 1: Artifact Switching**
   - Select a View Pack (e.g., "Screening Signal Timeline")
   - Switch to a different CommandView artifact
   - ✅ View Pack selection should be maintained

2. **Test Case 2: Zoom Level Changes**
   - Select a View Pack
   - Change zoom levels (Level 0 → Level 1 → Level 2)
   - ✅ View Pack selection should be maintained

3. **Test Case 3: Return to Previous Artifact**
   - Select View Pack A in artifact X
   - Switch to artifact Y
   - Return to artifact X
   - ✅ View Pack A should still be selected

## Files Modified

- `.repo_studios/command_center/viewer/ui/viewer.js`
  - `persistActiveSelectionMemory()` function (lines 605-630)
  - `restoreSelectionMemory()` function (lines 632-673)

## Additional Notes

- The fix maintains backward compatibility - if no view pack was selected, it won't force one
- The memory system is in-memory only (not persisted to localStorage), so it resets on page reload
- If a view pack is not available in the new context, it will gracefully fall back to zoom levels
- Console logging added for debugging: check browser console for "[restoreSelectionMemory] Restored active views" messages

## Future Enhancements (Optional)

Consider adding:

1. **localStorage persistence** - Save view pack preferences across browser sessions
2. **Per-view-pack memory** - Remember different selections for different view packs
3. **Smart fallback** - If exact view isn't available, try to select a similar view from the same pack
