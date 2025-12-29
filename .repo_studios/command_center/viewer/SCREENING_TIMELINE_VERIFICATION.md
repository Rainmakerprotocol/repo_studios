# Screening Signal Timeline - Verification Guide

<!-- markdownlint-disable MD013 -->
<!-- Technical verification guide with inline implementation details; line length exempt -->

## ✅ Feature Status: IMPLEMENTED · Multi-View Coexistence Verified (2025-11-08)

The Screening Signal Timeline feature has been implemented and regression tests are passing.
This guide will help you verify the end-to-end functionality in the browser.

---

## 📋 Prerequisites

1. **Viewer Server Running**: Ensure `serve_viewer.py` is running on port 8000

   ```bash
   .venv\Scripts\python.exe .repo_studios\command_center\viewer\serve_viewer.py
   ```

1. **Selector Data Generated**: Ensure `selector.json` exists with screening artifacts

   ```bash
   .venv\Scripts\python.exe .repo_studios\command_center\viewer\generate_selector.py --repo-root .
   ```

1. **Screening Data Available**: At least one CommandView artifact must have screening history data

---

## 🔍 Verification Steps

### Step 1: Open the Viewer

Navigate to: **<http://localhost:8000/.repo_studios/command_center/viewer/ui/>**

### Step 2: Select a Screening Artifact

In the left sidebar under **"CommandView Artifacts"**:

- Look for artifacts that have screening data (typically named with timestamps)
- Click on an artifact to load it

### Step 3: Check View Pack Availability

Scroll down in the left sidebar to **"View Packs"** section:

- Expand **"Health Pack"**
- Look for **"Screening Signal Timeline"** button

**Expected States:**

✅ **ENABLED** (blue/clickable):

- Button is active and clickable
- Tooltip shows: "Select to render this view"
- This means screening history data is available; even a lone snapshot unlocks the tab and the view will display a status message when no events exist yet

❌ **DISABLED** (grayed out):

- Button is inactive
- Tooltip shows: "Screening history data is not available in this CommandView artifact"
- This means the selected artifact has no screening history

### Step 4: Render the Timeline

If the button is enabled:

1. Click **"Screening Signal Timeline"**
1. A new tab should appear at the top showing "Health · Screening Signal Timeline"
1. The main diagram area should display a Mermaid timeline diagram

### Step 5: Verify Timeline Content

The timeline should display:

**Title Section:**

```text
[Artifact Name] Screening Scores

```

**Pack Sections:**
Each screening pack should have its own section with events showing:

- **Timestamp**: Format like `2025-11-06 10h14Z`
- **Event Details**: Including:
  - `[SEVERITY]` - OK, WARNING, or CRITICAL
  - `score X.X` - Current score value
  - `delta +/-X.X` - Change from previous event
  - `thresholds warn>=X fail>=X` - Threshold values
  - `docs X/Y missing Z` - Documentation metrics
  - `severity changed from [PREVIOUS]` - If severity changed
  - `folder [name]` - If folder context changed
  - `inventory [timestamp]` - If different from event timestamp

**Example Event:**

```text
2025-11-06 10h14Z : [OK] score 85.0 delta +5.0 thresholds warn>=70 fail>=50 docs 42/50 missing 8

```

### Step 6: Confirm Multi-View Coexistence

1. With the timeline tab active, select another available view (for example, **Code Flow · Function Call Graph**).
1. Verify the newly selected view renders immediately without triggering a fresh data load.
1. Click back on **Health · Screening Signal Timeline** in the tab header.

**Expected Outcome:** The original timeline diagram remains in place with identical status messaging and pack/event counts—no flicker, spinner, or reset to the empty state. This confirms that multi-view toggles preserve in-memory diagrams.

---

## 🐛 Troubleshooting

### Issue 1: "Screening Signal Timeline" Button is Disabled

**Cause**: The selected artifact doesn't have screening history data

**Solutions**:

1. Try selecting a different artifact from the sidebar
1. Check if screening data was generated for this artifact:
   - Look for `*_commandview_screening_*.json` files in reports

1. Generate new screening data if needed

### Issue 2: Button Shows "View wiring pending implementation"

**Cause**: The builder function is not registered

**Solution**: Check that `VIEW_BUILDERS` includes:

```javascript
screeningSignalTimelineView: buildScreeningSignalTimelineViewDefinition

```

### Issue 3: Timeline Shows "No screening history events"

**Cause**: Screening payload has no `score_history` or `score_snapshot`

**Check**:

1. Open browser DevTools (F12)
1. Look for console logs: `[loadCommandViewPayloads] Screening payload load failed`
1. Verify the screening JSON file exists and has valid data

### Issue 4: Diagram Doesn't Render

**Check Browser Console** (F12):

```javascript
// Look for errors like:
[buildScreeningSignalTimelineViewDefinition] ...
[buildScreeningTimelineDiagram] ...

```

**Common Issues**:

- Mermaid syntax error in generated timeline
- Missing import for `buildScreeningTimelineDiagram`
- Data format mismatch

---

## 📊 Expected Data Structure

The screening payload should contain:

```json
{
  "score_history": [
    {
      "timestamp": "2025-11-06T10:14:00Z",
      "context": {
        "folder_name": "scripts",
        "inventory_generated_at": "2025-11-06T10:14:00Z"
      },
      "packs": [
        {
          "id": "docstring_quality",
          "label": "Docstring Quality",
          "score": 85.0,
          "severity": "ok",
          "thresholds": {
            "warning": 70,
            "failure": 50
          },
          "metrics": {
            "functions_total": 50,
            "functions_documented": 42,
            "functions_missing": 8
          }
        }
      ]
    }
  ]
}

```

---

## ✨ Feature Capabilities

### What the Timeline Shows

1. **Chronological Events**: All screening events sorted by timestamp
1. **Per-Pack Sections**: Separate timeline section for each screening pack
1. **Score Progression**: Shows how scores change over time
1. **Severity Transitions**: Highlights when severity levels change
1. **Threshold Context**: Displays warning/failure thresholds
1. **Documentation Metrics**: Shows function documentation stats
1. **Delta Calculations**: Automatic calculation of score changes

### Interactive Features

- **Zoom Controls**: Use mouse wheel or +/- buttons to zoom
- **Pan**: Click and drag to pan the diagram
- **Tab Switching**: Switch between timeline and zoom levels
- **Resizable Sidebar**: Drag the right edge of sidebar to resize

---

## 🔧 Implementation Details

### Files Involved

1. **Builder**: `.repo_studios/command_center/viewer/ui/builders/screening_signal_timeline.js`
1. **View Definition**: `buildScreeningSignalTimelineViewDefinition()` in `viewer.js`
1. **Data Normalization**: `buildScreeningHistory()` in `viewer.js`
1. **Requirement Check**: `findViewRequirementIssue()` case "screeningHistory"

### Key Functions

- `buildScreeningTimelineDiagram()` - Main diagram builder
- `summarizeScreeningHistory()` - Groups events by pack
- `formatScreeningTimelineEvent()` - Formats event details
- `formatTimelineTimestamp()` - Formats timestamps
- `.repo_studios/tests/tests_command_center/viewer/test_screening_signal_timeline_view.py::test_screening_timeline_definition_is_stable_across_repeated_calls` - Regression guard ensuring repeated renders preserve diagram state for multi-view coexistence

---

## 📝 Testing Checklist

- [ ] Viewer loads without errors
- [ ] Artifacts list populates in sidebar
- [ ] Can select an artifact
- [ ] Health Pack section is visible
- [ ] Screening Signal Timeline button appears
- [ ] Button state (enabled/disabled) is correct
- [ ] Clicking button creates new tab
- [ ] Timeline diagram renders
- [ ] Timeline shows correct pack sections
- [ ] Events display with proper formatting
- [ ] Timestamps are readable
- [ ] Score deltas calculate correctly
- [ ] Severity labels are correct
- [ ] Can zoom in/out on timeline
- [ ] Can pan the timeline
- [ ] Can switch back to zoom levels tab
- [ ] Switching between timeline and other view tabs preserves both diagrams without reloading or resetting counts
- [ ] Can close the timeline tab

---

## 🎯 Success Criteria

The feature is working correctly if:

1. ✅ Timeline renders as a Mermaid diagram
1. ✅ All screening packs have their own sections
1. ✅ Events are chronologically ordered
1. ✅ Event details include score, delta, thresholds, and metrics
1. ✅ Severity transitions are highlighted
1. ✅ Status message shows pack and event counts

---

## 📞 Next Steps

If verification is successful:

- ✅ Feature is live and ready for use
- Document any edge cases discovered
- Consider adding more screening packs

If issues are found:

- Note the specific error messages
- Check browser console for detailed logs
- Verify data format in screening JSON files
- Report findings for debugging
