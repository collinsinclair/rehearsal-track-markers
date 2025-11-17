# Implementation Plan: Rehearsal Track Marker Application

## Planning Philosophy

This plan follows a **build-test-integrate-validate** cycle, establishing foundational architecture before detailed features. Each phase includes explicit testing checkpoints to catch issues early and validate design decisions before building dependent features.

---

## Phase 1: Project Foundation & Architecture

### 1.1 Environment Setup
- Set up Python development environment with PySide6
- Establish project directory structure
- Configure version control (git repository structure)
- Create requirements.txt/setup.py
- Set up basic logging framework

**Test Checkpoint:**
- Verify PySide6 installation
- Run "hello world" Qt application
- Confirm Python environment consistency across development machines

### 1.2 Core Data Models
- Design and implement data classes (Show, Track, Marker)
- Establish data validation rules
- Create in-memory data structure prototypes
- Define interfaces between models

**Test Checkpoint:**
- Unit tests for data model validation (unique marker names, etc.)
- Test data structure manipulation (add/remove/reorder)
- Verify model constraints work correctly
- Manual testing: create sample data in Python REPL

### 1.3 Persistence Layer (JSON)
- Implement JSON serialization/deserialization
- Create file system utilities for app directory structure
- Build show loading/saving functionality
- Handle file path abstraction (cross-platform)

**Test Checkpoint:**
- Unit tests for JSON round-trip (save/load produces identical data)
- Test with edge cases (empty shows, special characters in names)
- Manual testing: examine generated JSON files for human-readability
- Cross-platform path testing (if multiple OS available)

### 1.4 Audio File Management
- Implement audio file copying to app storage
- Create file organization utilities
- Handle supported format detection
- Build basic error handling for missing/corrupted files

**Test Checkpoint:**
- Unit tests for file copying operations
- Test with various audio formats (MP3, WAV, M4A, FLAC)
- Test with large files, malformed files, missing files
- Manual verification: examine created directory structures

---

## Phase 2: Audio Playback Engine

### 2.1 Qt Multimedia Integration
- Set up QMediaPlayer for basic audio playback
- Implement play/pause/stop functionality
- Create position tracking mechanism
- Handle audio format support detection

**Test Checkpoint:**
- Integration test: load and play each supported audio format
- Test playback state transitions
- Manual testing: verify smooth playback, no stuttering
- Test on different OS if available

### 2.2 Seek & Navigation
- Implement scrubbing/seeking to specific timestamps
- Add skip forward/backward by increment
- Create position change event handling
- Test latency of seek operations

**Test Checkpoint:**
- Performance testing: measure seek latency (<100ms target)
- Test edge cases (seek beyond end, negative values)
- Manual testing: verify immediate response to seek commands
- Test with various audio file lengths and formats

### 2.3 Playback State Management
- Implement playback state preservation (playing vs paused)
- Create state change notification system
- Handle edge cases (jumping while playing, etc.)

**Test Checkpoint:**
- Unit tests for state transitions
- Integration tests: verify state maintained during marker jumps
- Manual testing: jump to markers while playing and while paused

---

## Phase 3: Basic UI Framework

### 3.1 Main Window Structure
- Create main application window
- Implement basic menu bar (File, Edit, Help)
- Set up layout framework (splitter for sidebar + main area)
- Establish styling/theming approach

**Test Checkpoint:**
- Visual inspection: window resizing, minimum sizes
- Test on different screen resolutions
- Cross-platform visual testing (if available)
- Accessibility check (keyboard navigation, contrast)

### 3.2 Track Sidebar (Shell)
- Create track list widget
- Implement basic track selection
- Add "Add Track" button (non-functional initially)
- Set up visual highlight for selected track

**Test Checkpoint:**
- Visual testing: layout with 0, 1, 5, 50 tracks
- Test selection behavior
- Manual testing: ensure clear visual feedback

### 3.3 Main Content Area (Shell)
- Create playback controls section (buttons without functionality)
- Add progress bar widget
- Create marker list section
- Implement basic layout and spacing

**Test Checkpoint:**
- Visual inspection: spacing, alignment, readability
- Test window resizing behavior
- Verify layout on different screen sizes
- User feedback session: show mockup to potential users

---

## Phase 4: Core Feature Integration

### 4.1 Show Management Integration
- Connect "New Show" menu item to data model
- Implement show creation dialog
- Connect show saving/loading to UI
- Add recent shows (if time permits)

**Test Checkpoint:**
- Functional test: create new show, save, close app, reopen
- Test with various show names (special characters, long names)
- Manual testing: verify file system structure created correctly

### 4.2 Track Management Integration
- Connect "Add Track" to file picker
- Implement drag-and-drop for audio files
- Connect track list to data model
- Implement track selection → audio player connection
- Add track removal functionality
- Implement drag-to-reorder tracks

**Test Checkpoint:**
- Functional test: add multiple tracks, switch between them
- Test drag-and-drop with various file types
- Test reordering (drag first to last, last to first, middle positions)
- Edge case testing: add same file twice, add non-audio file
- Manual testing: verify audio files copied correctly

### 4.3 Playback Controls Integration
- Connect play/pause buttons to audio engine
- Connect skip forward/backward buttons
- Implement progress bar scrubbing
- Add time display (current/total)
- Implement spacebar shortcut

**Test Checkpoint:**
- Functional test: all playback controls work correctly
- Test keyboard shortcuts
- Test scrubbing accuracy (click at various points)
- Performance test: verify responsiveness during playback
- Manual testing: feel for latency and smoothness

### 4.4 Marker Creation
- Implement "Add Marker" button functionality
- Create marker naming dialog
- Implement 'M' hotkey for adding markers
- Connect markers to data model
- Display markers in list

**Test Checkpoint:**
- Functional test: add marker while paused, while playing
- Test marker name validation (duplicates, empty names)
- Test hotkey timing accuracy (press M during playback)
- Edge case: add marker at time 0, at end of track
- Manual testing: verify timestamp captured accurately

### 4.5 Marker Visualization
- Display markers on progress bar (vertical ticks)
- Implement marker positioning calculation
- Test visual clarity with various marker densities

**Test Checkpoint:**
- Visual testing: 0 markers, 5 markers, 50 markers, 200 markers
- Test with short tracks (<30s) and long tracks (>10min)
- Manual testing: verify markers align correctly with timeline

### 4.6 Marker Navigation
- Implement click-to-jump functionality
- Ensure playback state preservation
- Test seek accuracy

**Test Checkpoint:**
- Functional test: jump to markers while playing/paused
- Performance test: measure jump latency
- Test rapid marker jumping (click multiple markers quickly)
- Manual testing: verify jumps feel instantaneous

### 4.7 Marker Editing
- Implement marker selection in list
- Connect Edit button to rename dialog
- Implement Delete button with confirmation
- Add visual highlight for selected marker
- Implement arrow key nudging

**Test Checkpoint:**
- Functional test: rename marker, delete marker, nudge marker
- Test nudge accuracy (verify timestamp changes correctly)
- Test keyboard focus behavior (arrow keys only work when marker selected)
- Edge case: nudge marker beyond track boundaries
- Manual testing: verify 100ms nudge increment feels right

---

## Phase 5: Settings & Configuration

### 5.1 Settings Implementation
- Create settings data structure (per-show settings)
- Implement skip increment configuration
- Implement marker nudge increment configuration
- Add settings to JSON serialization

**Test Checkpoint:**
- Unit tests: settings save/load correctly
- Functional test: change settings, verify behavior updates
- Test default values for new shows

### 5.2 Settings UI
- Create settings dialog/panel (if needed)
- Allow inline editing of skip increment
- Consider accessibility of settings

**Test Checkpoint:**
- Visual testing: settings interface clarity
- Functional test: change settings and verify they take effect
- Manual testing: user can find and modify settings easily

---

## Phase 6: Import/Export

### 6.1 Export Functionality
- Implement export show to JSON
- Create file picker for export location
- Consider audio file inclusion option (optional)

**Test Checkpoint:**
- Functional test: export show, verify JSON is valid
- Test exporting show with various track/marker counts
- Cross-user test: export on one machine, verify readability

### 6.2 Import Functionality
- Implement import from JSON
- Handle audio file copying during import
- Add error handling for malformed JSON

**Test Checkpoint:**
- Functional test: import exported show
- Test with hand-crafted JSON files (edge cases)
- Cross-machine test: export on Machine A, import on Machine B
- Error testing: import invalid JSON, missing audio files

---

## Phase 7: Polish & Hardening

### 7.1 Error Handling
- Add user-friendly error messages
- Handle missing audio files gracefully
- Implement recovery from corrupted show files
- Add logging for debugging

**Test Checkpoint:**
- Fault injection testing: delete audio file while show open
- Test with corrupted JSON files
- Test with unreadable directories
- Manual testing: verify error messages are clear and actionable

### 7.2 Auto-Save
- Implement periodic auto-save
- Add "unsaved changes" detection
- Prompt user on quit if unsaved changes

**Test Checkpoint:**
- Functional test: make changes, verify auto-save triggers
- Test quit behavior with unsaved changes
- Test crash recovery (force quit and relaunch)

### 7.3 Performance Optimization
- Profile application with large shows (50+ tracks, 100+ markers)
- Optimize UI rendering if needed
- Optimize data loading/saving

**Test Checkpoint:**
- Performance test: load show with 50 tracks, 100 markers each
- Measure UI responsiveness with large datasets
- Test memory usage over extended use

### 7.4 UI/UX Refinement
- Add tooltips for all controls
- Refine visual styling and spacing
- Ensure consistent interaction patterns
- Add keyboard navigation improvements

**Test Checkpoint:**
- Usability testing: observe non-technical users
- Visual inspection: overall polish and consistency
- Accessibility audit: keyboard-only navigation

---

## Phase 8: User Acceptance Testing

### 8.1 Alpha Testing with Target Users
- Recruit 2-3 stage managers/MDs for testing
- Provide test scenarios (create show, add tracks, mark, navigate)
- Collect feedback on workflow and pain points

**Test Checkpoint:**
- Observe users completing core workflows
- Document confusion points and stumbling blocks
- Measure time to complete tasks (vs. manual scrubbing)
- Collect satisfaction feedback

### 8.2 Real Rehearsal Pilot
- Deploy to actual rehearsal environment
- Monitor for crashes, bugs, usability issues
- Gather feedback on missing features vs. spec

**Test Checkpoint:**
- Stability testing: runs without crashes during 2-hour rehearsal
- Performance validation: marker jumps feel faster than scrubbing
- Usability validation: users don't need documentation
- Feature validation: are any MVP features insufficient?

### 8.3 Iteration Based on Feedback
- Prioritize critical fixes
- Address usability concerns
- Refine unclear UI elements
- Fix any crash-causing bugs

**Test Checkpoint:**
- Regression testing: verify fixes don't break existing features
- Re-test with users to validate improvements

---

## Phase 9: Documentation & Deployment

### 9.1 User Documentation
- Create quick-start guide
- Document keyboard shortcuts
- Add in-app help/tooltips (if not already present)
- Create FAQ for common issues

**Test Checkpoint:**
- Have new user follow quick-start guide without assistance
- Verify documentation matches actual behavior

### 9.2 Build & Distribution
- Create installable packages (Windows, macOS, Linux)
- Test installation process
- Verify app runs on fresh systems (no dev environment)

**Test Checkpoint:**
- Clean machine testing: install on machine without Python/Qt
- Cross-platform testing: test installers on each OS
- Verify file associations work correctly

### 9.3 Final Validation
- Run full test suite
- Perform end-to-end workflow tests
- Verify all success criteria met

**Test Checkpoint:**
- Success criteria validation:
  - ✓ Create show, add tracks, add markers in <5 minutes
  - ✓ Jumping faster than manual scrubbing
  - ✓ Stable in live rehearsals
  - ✓ Non-technical users can operate without docs
  - ✓ Shows shareable via import/export

---

## Testing Strategy Summary

### Continuous Testing
Throughout all phases:
- Run unit tests after each code change
- Perform manual spot-checks frequently
- Test on multiple platforms when possible
- Keep test coverage high for core functionality

### Types of Testing by Phase
1. **Foundation phases**: Unit tests, data validation
2. **Integration phases**: Functional tests, performance tests
3. **UI phases**: Visual testing, usability testing
4. **Final phases**: User acceptance testing, real-world pilots

### Test Environments
- **Development**: Local machine with full dev tools
- **Staging**: Clean installation to mimic user environment
- **Production**: Real rehearsal scenarios with target users

### Bug Tracking
- Maintain issue tracker throughout development
- Prioritize bugs: Critical (crashes) → Major (unusable) → Minor (polish)
- Re-test fixed bugs before marking as resolved

---

## Key Principles

1. **Test early, test often**: Don't wait until features are "complete"
2. **Build horizontally before vertically**: Get basic versions of all components working before perfecting any one component
3. **Validate assumptions**: If a design decision is uncertain, prototype and test it quickly
4. **User feedback is gold**: Get the app in front of actual users as soon as it's minimally functional
5. **Defer optimization**: Make it work, make it right, then make it fast

This plan ensures a stable, tested foundation before adding complexity, with continuous validation that the app meets its core goal: making rehearsals more efficient.

