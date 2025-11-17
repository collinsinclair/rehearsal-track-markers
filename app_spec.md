# Rehearsal Track Marker Application - Specification Document

## 1. Overview

### 1.1 Purpose
A desktop application for musical theatre rehearsals that enables users to add timestamped markers to audio tracks (rehearsal tracks) and quickly jump to specific locations in the music. The primary goal is to eliminate the inefficiency of manually scrubbing through audio files to find specific measures, rehearsal marks, or cues during rehearsals.

### 1.2 Core Value Proposition
- **Low-latency navigation**: Jumping to markers must be faster than manual scrubbing
- **Simple workflow**: Non-technical users (stage managers, choreographers, MDs) can create and use markers with minimal training
- **Rehearsal-focused**: Designed specifically for the live rehearsal environment while supporting pre-rehearsal preparation

### 1.3 Key Principle
**Feature scope**: If a feature is not explicitly mentioned in this document, it is not part of the application. This ensures focus on core functionality.

---

## 2. Technical Stack

### 2.1 Core Technologies
- **Framework**: PySide6 (Qt for Python)
- **Language**: Python
- **Audio Support**: Qt Multimedia (supports MP3, WAV, M4A, FLAC, OGG, and other common formats)
- **Data Format**: JSON (for show/project files)
- **Internal Storage**: SQLite (if needed for performance; optional)

### 2.2 Platform
- **Target**: Desktop application (Windows, macOS, Linux)
- **Rationale**: Better performance, predictable audio latency, offline reliability, direct file system access

---

## 3. Data Model

### 3.1 Show/Production Structure
- A **show** (or **production**) is the top-level organizational unit
- Each show contains:
  - Show name
  - Ordered list of tracks
  - Configuration settings (e.g., skip increment)

### 3.2 Track Structure
- Each **track** contains:
  - Original filename
  - Path to audio file in app storage
  - Ordered list of markers
  - Metadata (duration, format, etc.)

### 3.3 Marker Structure
- Each **marker** contains:
  - Name/label (text string, must be unique per track)
  - Timestamp (milliseconds from start)
  
**Constraints**:
- Marker names must be unique within a track
- No restriction on naming convention (user can use "42", "Reh C", "Dorothy enters", etc.)
- No additional metadata in MVP

---

## 4. File Organization & Persistence

### 4.1 Directory Structure
```
~/AppData/[AppName]/
├── shows/
│   ├── [show-name]/
│   │   ├── audio/
│   │   │   ├── [original-filename-1.mp3]
│   │   │   ├── [original-filename-2.wav]
│   │   │   └── ...
│   │   └── [show-name].json
│   └── [another-show]/
│       └── ...
```

### 4.2 Audio File Handling
- **Strategy**: Copy audio files to app storage (not reference in place)
- **Rationale**: Prevents breakage if user moves/deletes original files
- **Supported Formats**: All common audio formats the user's system can play (MP3, WAV, M4A, FLAC, OGG, etc.)

### 4.3 Show File Format (JSON)
- Human-readable and version-control friendly
- Contains: show name, track list, markers, settings
- Can be exported/imported for sharing between users
- Example structure:
```json
{
  "show_name": "Into the Woods - Spring 2025",
  "settings": {
    "skip_increment_seconds": 5,
    "marker_nudge_increment_ms": 100
  },
  "tracks": [
    {
      "filename": "01-prologue.mp3",
      "markers": [
        {"name": "Measure 1", "timestamp_ms": 0},
        {"name": "Reh A", "timestamp_ms": 15420},
        {"name": "Witch enters", "timestamp_ms": 45200}
      ]
    }
  ]
}
```

### 4.4 Import/Export
- Users can export show files to share with others
- Users can import show files created by others
- No real-time collaborative editing
- No enforced user roles (every user has full access)

---

## 5. Features

### 5.1 MVP Features (Version 0)

#### 5.1.1 Show Management
- Create new show
- Open existing show
- Save show
- Import show (from JSON file)
- Export show (to JSON file)

#### 5.1.2 Track Management
- Add tracks to show (file picker and drag-and-drop)
- Remove tracks from show
- Reorder tracks (drag to reposition)
- Display track list in sidebar
- Select track to view/edit

#### 5.1.3 Playback Controls
- Play/pause (spacebar)
- Scrubbing (click/drag on timeline)
- Skip forward/backward by configurable increment (default: 5 seconds)
- Progress bar showing current position
- Time display: current time / total duration
- Visual indication of marker positions on timeline

#### 5.1.4 Marker Management
- Add marker at current playback position (hotkey: `M` or GUI button)
- Add marker while track is playing (hotkey captures exact timestamp)
- Jump to marker (click on marker in list)
- Rename marker (select marker, click edit)
- Delete marker (select marker, click delete)
- Nudge marker position ±X ms using arrow keys (when marker is selected)
  - Default increment: 100ms (user-configurable)
  - Non-modal: arrow keys work when marker is selected
- Display all markers for current track in a list
- Markers maintain playback state (if playing before jump, continue playing; if paused, stay paused)

#### 5.1.5 UI/UX Requirements
- Single-click interactions only (no hidden context menus)
- All actions available from visible controls
- Clear visual feedback for selected marker
- Real-time timestamp update when nudging markers
- Instructions/tooltips for new users
- Professional, uncluttered interface

### 5.2 Deferred Features (Post-MVP)
- Speed/tempo adjustment (high priority for future)
- Waveform visualization
- Loop regions
- Per-app volume control (use OS volume instead)
- Multiple marker types or categories
- Annotations beyond marker names
- Undo/redo (nice to have, but not MVP)

---

## 6. User Interface

### 6.1 Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│ File  Edit  Help                     [Show Name]        │
├──────────┬──────────────────────────────────────────────┤
│          │  ┌────────────────────────────────────────┐  │
│ TRACKS   │  │  Track: "Defying Gravity"              │  │
│          │  ├────────────────────────────────────────┤  │
│ • Track1 │  │  [Play] [Pause] [<<5s] [5s>>]          │  │
│ • Track2 │  │                                        │  │
│ • Track3 │  │  ═══●═══════════════  2:34 / 4:12      │  │
│   ...    │  │      ^markers shown as ticks           │  │
│          │  ├────────────────────────────────────────┤  │
│ [+Track] │  │  MARKERS                               │  │
│          │  │  [+ Add Marker (M)]                    │  │
│          │  │                                        │  │
│          │  │  • Measure 42      [Edit] [Delete]     │  │
│          │  │  • Reh. Mark C     [Edit] [Delete]     │  │
│          │  │  • Dorothy enters  [Edit] [Delete]     │  │
│          │  └────────────────────────────────────────┘  │
└──────────┴──────────────────────────────────────────────┘
```

### 6.2 UI Regions

#### 6.2.1 Track Sidebar (Left)
- Displays all tracks in current show
- Click to select/switch tracks
- Drag to reorder
- "+ Track" button to add new tracks
- Shows currently selected track with highlight

#### 6.2.2 Main Content Area (Right)
**Playback Section**:
- Track name/title
- Playback controls (Play, Pause, Skip Back, Skip Forward)
- Progress bar with:
  - Current playback position indicator
  - Marker positions shown as vertical ticks/lines
  - Clickable/draggable for scrubbing
- Time display (current / total) - subtle styling, not prominent

**Marker Section**:
- "Add Marker" button with hotkey hint (M)
- List of all markers for current track
- Each marker shows:
  - Marker name
  - Edit button
  - Delete button
- Selected marker has visual highlight
- Timestamp shown on hover (not prominently displayed)

### 6.3 Design Principles
- **Clarity over density**: Space out controls, avoid cramming
- **Discoverability**: New users should understand how to accomplish tasks without a manual
- **Visual hierarchy**: Marker names are prominent; timestamps are secondary
- **Consistent interactions**: Single-click for all actions
- **Immediate feedback**: Visual confirmation of all state changes

---

## 7. Workflows

### 7.1 Creating a New Show
1. User selects File → New Show
2. Dialog prompts for show name
3. App creates show directory structure
4. Empty show opens (ready to add tracks)

### 7.2 Adding Tracks to Show
1. User clicks "+ Track" button or File → Add Tracks
2. File picker opens (supports multi-select)
   - Alternatively: drag-and-drop audio files onto track list
3. App copies audio files to show's audio directory
4. Tracks appear in sidebar in selection order
5. User can drag to reorder as needed

### 7.3 Adding Markers During Rehearsal
**Real-time approach**:
1. Track is playing
2. User hears the spot they want to mark
3. User presses `M` (or clicks "Add Marker")
4. Timestamp is captured at that instant
5. Dialog prompts for marker name
6. User enters name (e.g., "Measure 52" or "Reh B")
7. Marker appears in list and on timeline

**Fine-tuning approach**:
1. User pauses at approximate location
2. User clicks "Add Marker" button
3. Dialog prompts for marker name
4. User enters name
5. Marker is created
6. User selects marker and uses arrow keys to nudge position forward/backward

### 7.4 Jumping to a Marker
1. User clicks on marker in list
2. Playback immediately jumps to that timestamp
3. Playback state is maintained (playing → keep playing; paused → stay paused)

### 7.5 Editing/Deleting Markers
**Renaming**:
1. User clicks marker in list (selects it)
2. User clicks "Edit" button
3. Dialog allows renaming
4. User confirms

**Deleting**:
1. User clicks marker in list (selects it)
2. User clicks "Delete" button
3. Confirmation prompt (optional, can be added)
4. Marker is removed

**Repositioning**:
1. User clicks marker in list (selects it)
2. Visual highlight confirms selection
3. User presses arrow keys:
   - Right arrow: nudge forward by X ms
   - Left arrow: nudge backward by X ms
4. Timestamp updates in real-time
5. User can jump to marker to verify position

### 7.6 Exporting/Importing Shows
**Export**:
1. File → Export Show
2. File picker for save location
3. JSON file is saved with show data (references to audio files, markers, settings)
4. Audio files can optionally be included in export (ZIP archive)

**Import**:
1. File → Import Show
2. File picker to select JSON file
3. App copies show data and audio files to app directory
4. Show appears in show list

---

## 8. Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `M` | Add marker at current position |
| `Left Arrow` | Nudge selected marker backward (when marker selected) |
| `Right Arrow` | Nudge selected marker forward (when marker selected) |
| `←` (button/hotkey TBD) | Skip backward X seconds |
| `→` (button/hotkey TBD) | Skip forward X seconds |

Additional shortcuts can be added as needed (e.g., Cmd/Ctrl+N for new show, etc.)

---

## 9. Settings/Configuration

### 9.1 User-Configurable Settings
- **Skip increment**: How many seconds forward/backward when using skip buttons (default: 5 seconds)
- **Marker nudge increment**: How many milliseconds to move when using arrow keys (default: 100ms)

### 9.2 Settings Persistence
- Settings stored per-show in JSON file
- Global app preferences (if any) stored separately

---

## 10. Non-Functional Requirements

### 10.1 Performance
- **Latency**: Marker jumps must feel instantaneous (<100ms perceived delay)
- **Responsiveness**: UI must remain responsive during audio playback
- **Startup time**: App should launch quickly (<2 seconds)

### 10.2 Reliability
- Audio playback must not stutter or skip
- App must handle large shows (50+ tracks, 100+ markers per track)
- Graceful handling of missing/corrupted audio files

### 10.3 Usability
- Non-technical users should be able to use the app without training
- Error messages should be clear and actionable
- Undo/redo strongly encouraged (but not MVP requirement)

### 10.4 Data Safety
- Auto-save functionality (or frequent save prompts)
- Show data must not be lost due to crashes
- Consider backup/recovery mechanisms

---

## 11. Future Considerations (Not MVP)

These are acknowledged as valuable but explicitly deferred:

1. **Speed/tempo adjustment** - HIGH priority for post-MVP
2. **Waveform visualization** - Helpful for precise marker placement
3. **Loop regions** - Useful for drilling specific sections
4. **Marker categories/types** - Distinguish measures from cues from rehearsal marks
5. **Multi-user collaboration** - Real-time editing, permissions
6. **Mobile companion app** - Remote control for playback
7. **Cloud sync** - Automatic backup and multi-device access
8. **Analytics** - Track which sections are rehearsed most frequently
9. **Metadata/notes** - Attach comments or instructions to markers
10. **Batch operations** - Add markers from CSV, auto-generate measure markers, etc.

---

## 12. Success Criteria

The MVP is successful if:
1. Users can create a show, add tracks, and add markers in <5 minutes
2. Jumping to a marker is measurably faster than manual scrubbing
3. The app is stable enough for use in live rehearsals without crashes
4. Non-technical users can operate the app without documentation
5. Shows can be shared between users via export/import

---

## 13. Open Questions / Decisions Needed

1. App name (placeholder: "[AppName]")
2. Exact directory structure for show storage (follow platform conventions)
3. Confirmation prompts for destructive actions (delete marker, remove track)?
4. Maximum reasonable limits (tracks per show, markers per track) for performance testing
5. Licensing/distribution strategy (open source? commercial?)

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-16  
**Status**: Ready for implementation

