# Drone Simulation Visualizer - Complete Build Plan
## Based on Fly-in Project Architecture

---

## **PHASE 1: Project Setup & Foundation**

### 1.1 Environment Setup
- [ ] Create `visualizer.py` file in project root
- [ ] Install required dependencies: `pip install pygame`
- [ ] Verify Pygame installation works: `python3 -c "import pygame; print('OK')"`
- [ ] Set up virtual environment if needed: `python3 -m venv v`

### 1.2 Import Required Modules
- [ ] Import `pygame` for graphics
- [ ] Import `sys` for system operations
- [ ] Import `re` for regex (ANSI code removal)
- [ ] Import `math` for distance calculations
- [ ] Import `typing` for type hints
- [ ] Import `models.py` classes: `SimulationMap`, `Zone`, `Connection`, `Drone`
- [ ] Import `map_parser.py`: `MapParser` class

### 1.3 Create Basic Class Structure
- [ ] Create `class SimulationVisualizer` with `__init__` method
- [ ] Add class constants for window size, colors, fonts
- [ ] Define `Color` class with all color constants
- [ ] Initialize Pygame in `__init__`

---

## **PHASE 2: Input Handling**

### 2.1 Map File Loading
- [ ] Create method `_load_map()` to load `.txt` map file
- [ ] Use `MapParser` to parse map into `SimulationMap` object
- [ ] Handle file not found errors gracefully
- [ ] Extract zone data: names, coordinates (x, y), types, capacities
- [ ] Extract connection data: linked zones, capacities
- [ ] Store start zone and end zone references

### 2.2 Simulation Output Parsing
- [ ] Create method `_parse_turns()` to read stdin from simulator
- [ ] Read piped output line by line from `sys.stdin`
- [ ] Skip non-movement lines (summaries, empty lines, stats)
- [ ] Identify turn structure: "D1-zone1 D2-zone2 ..."

### 2.3 Movement Parsing
- [ ] Create method `_parse_movement()` to parse individual movements
- [ ] Extract drone ID (format: "D1", "D2", etc.)
- [ ] Extract location (zone name or connection name)
- [ ] Remove ANSI color codes using regex
- [ ] Handle both zone movements and in-transit (zone1-zone2)
- [ ] Create method `_remove_ansi_codes()` for cleanup

### 2.4 Data Structure Building
- [ ] Store turns as list: `List[Dict[str, str]]`
  - Each turn is a dictionary: `{"D1": "zone1", "D2": "zone2"}`
- [ ] Store all drones: `Set[str]` of drone IDs
- [ ] Build drone history: `Dict[str, List[str]]` for path tracking
- [ ] Create method `_build_drone_history()` to track all drone paths

---

## **PHASE 3: Screen & Position Calculations**

### 3.1 Coordinate System Setup
- [ ] Initialize Pygame display window (width, height)
- [ ] Create game area (left side) and sidebar (right side)
- [ ] Define padding and margins

### 3.2 Zone Position Mapping
- [ ] Create method `_calculate_positions()` to map zones to screen coordinates
- [ ] Find min/max x,y coordinates from all zones
- [ ] Calculate scale factor to fit all zones on screen
- [ ] Center the layout in the available space
- [ ] Store positions: `Dict[zone_name] -> (screen_x, screen_y)`
- [ ] Handle edge case: maps with single zone or negative coordinates

### 3.3 Viewport & Zoom
- [ ] Add zoom level variable (starts at 1.0)
- [ ] Add pan offsets (x, y)
- [ ] Create method `_screen_pos(world_x, world_y)` to convert world→screen
- [ ] Implement zoom in/out controls (UP/DOWN keys)

---

## **PHASE 4: Drawing Core Elements**

### 4.1 Zones (Nodes)
- [ ] Create method `_draw_zones()` to render all zones
- [ ] For each zone:
  - Draw circle at zone position
  - Draw zone name label above circle
  - Draw zone type indicator (color)
  - Draw capacity label if > 1
  - Highlight on hover
- [ ] Color zones based on type:
  - Green = start zone
  - Red = end zone
  - Blue = normal zone
  - Orange = restricted zone
  - Cyan = priority zone
  - Dark red = blocked zone

### 4.2 Connections (Edges)
- [ ] Create method `_draw_connections()` to render all edges
- [ ] For each connection:
  - Draw line between two zones
  - Draw capacity number at midpoint
  - Handle different capacity levels (thickness variation optional)

### 4.3 Zones-Only Test
- [ ] Run visualizer with simple map (01_linear_path.txt)
- [ ] Verify all zones appear on screen
- [ ] Verify all connections visible
- [ ] Verify labels readable

---

## **PHASE 5: Drone Rendering**

### 5.1 Get Drone Position
- [ ] Create method `_get_drone_position(drone_id, location)`
- [ ] If location is a zone name: return zone position
- [ ] If location is a connection (zone1-zone2):
  - Find both zone positions
  - Return midpoint (drone in transit)
- [ ] Return `None` if location not found

### 5.2 Draw Drones at Current Turn
- [ ] Create method `_draw_drones()` to render all drones
- [ ] For current turn:
  - For each drone in turn:
    - Get its position
    - Draw colored circle (unique color per drone)
    - Draw drone label (D1, D2, etc.)
    - Mark if drone has arrived (✓ symbol)

### 5.3 Drone Color Assignment
- [ ] Create method `_get_drone_color(drone_id)`
- [ ] Generate unique colors from palette (20+ colors)
- [ ] Hash drone ID to consistent color
- [ ] Same drone always same color across turns

---

## **PHASE 6: Turn Navigation**

### 6.1 Turn State Management
- [ ] Initialize `current_turn = 0`
- [ ] Calculate `max_turn = len(turns) - 1`
- [ ] Create method to validate turn number (0 to max_turn)

### 6.2 Keyboard Controls
- [ ] SPACE / RIGHT ARROW: Go to next turn
  - Check if `current_turn < max_turn`
  - Increment `current_turn`
- [ ] LEFT ARROW: Go to previous turn
  - Check if `current_turn > 0`
  - Decrement `current_turn`
- [ ] 'r' key: Reset to turn 0
  - Set `current_turn = 0`
- [ ] 'e' key: Jump to end
  - Set `current_turn = max_turn`
- [ ] 'q' key: Quit program
  - Set `running = False`

### 6.3 Event Handling
- [ ] Create method `_handle_events()` to process Pygame events
- [ ] Check for KEYDOWN events
- [ ] Update state based on key pressed
- [ ] Allow continuous keyboard input

---

## **PHASE 7: User Interface (Sidebar)**

### 7.1 Sidebar Layout
- [ ] Create method `_draw_sidebar()` to render right panel
- [ ] Sidebar should show:
  - Title: "SIMULATION"
  - Current turn counter: "Turn: 3/45"
  - Number of drones moving this turn

### 7.2 Drone List Display
- [ ] List all drones moving in current turn
- [ ] For each drone show:
  - Colored dot (drone color)
  - Drone ID (D1, D2, etc.)
  - Current location (zone or connection)
  - Arrival status (✓ if at end zone)

### 7.3 Controls Panel
- [ ] Display all keyboard controls:
  - SPACE/→: Next turn
  - ←: Previous turn
  - 'r': Reset
  - 'e': End
  - 'g': Grid toggle
  - 'h': History toggle
  - 'd': Debug info
  - 'q': Quit

### 7.4 Styling
- [ ] Use contrasting colors (light text on dark background)
- [ ] Use multiple font sizes for hierarchy
- [ ] Add spacing/padding for readability

---

## **PHASE 8: Header & Statistics**

### 8.1 Top Header
- [ ] Create method `_draw_header()` to show info at top
- [ ] Display:
  - Map file path
  - Total zones: {count}
  - Total drones: {count}
  - Connection count (optional)

### 8.2 Real-time Stats
- [ ] Show in sidebar:
  - Turns parsed: {count}
  - Zones loaded: {count}
  - Drones tracked: {count}

---

## **PHASE 9: Interactive Features**

### 9.1 Hover Detection
- [ ] Create method `_update_hovered_zone()` to detect mouse position
- [ ] Calculate distance from mouse to each zone
- [ ] If distance < threshold: mark zone as hovered
- [ ] Update `self.hovered_zone`
- [ ] Handle MOUSEMOTION events

### 9.2 Hover Highlight
- [ ] In `_draw_zones()`: check if zone is hovered
- [ ] If hovered: draw extra circle around zone (yellow outline)
- [ ] Show zone details in sidebar when hovered (optional)

### 9.3 Grid Overlay (Optional)
- [ ] Create method `_draw_grid()` to render grid
- [ ] Only draw if `show_grid = True`
- [ ] Draw vertical and horizontal lines every 50 pixels
- [ ] Use dark color (low opacity)
- [ ] Toggle with 'g' key

---

## **PHASE 10: Advanced Features**

### 10.1 Zoom Controls
- [ ] UP arrow: Increase zoom (multiply by 1.1)
- [ ] DOWN arrow: Decrease zoom (divide by 1.1)
- [ ] Update `_screen_pos()` to apply zoom
- [ ] Cap zoom level (min: 0.1x, max: 5x)

### 10.2 Drone History/Breadcrumbs
- [ ] Create method to show drone paths (all past positions)
- [ ] Toggle with 'h' key
- [ ] Display fading dots showing drone trail
- [ ] Only show up to current turn

### 10.3 Debug Mode
- [ ] Create method `_print_debug_info()` to console output
- [ ] Toggle with 'd' key
- [ ] Print:
  - Current turn data
  - Zone coordinates and screen positions
  - All drones in current turn
  - Any parsing information

---

## **PHASE 11: Main Drawing Loop**

### 11.1 Draw Method
- [ ] Create method `_draw()` to render entire frame
- [ ] Clear screen to black
- [ ] Fill game area background
- [ ] Draw in order:
  1. Connections (behind everything)
  2. Zones (middle layer)
  3. Drones (top layer)
  4. Grid (if enabled)
  5. Sidebar (UI)
  6. Header (UI)

### 11.2 Display Update
- [ ] Call `pygame.display.flip()` to update screen
- [ ] Control frame rate with clock.tick(FPS)

### 11.3 Main Loop
- [ ] Create method `run()` as main loop
- [ ] While `running = True`:
  - Handle events
  - Draw frame
  - Tick clock
- [ ] Exit loop when 'q' pressed or window closed

---

## **PHASE 12: Startup & Cleanup**

### 12.1 Entry Point
- [ ] Create `main()` function
- [ ] Check command line arguments: `sys.argv[1]` = map file
- [ ] Read stdin for simulation output
- [ ] Create visualizer instance
- [ ] Call `visualizer.run()`
- [ ] Print startup messages

### 12.2 Error Handling
- [ ] Try/catch for map loading errors
- [ ] Try/catch for stdin reading errors
- [ ] Try/catch for Pygame errors
- [ ] Print error messages to stderr
- [ ] Exit gracefully with error code

### 12.3 Cleanup
- [ ] On exit: call `pygame.quit()`
- [ ] Close any open files
- [ ] Print "Goodbye" message (optional)

### 12.4 Script Entry
- [ ] Add `if __name__ == "__main__": main()`
- [ ] Allow running as: `python3 visualizer.py <map_file>`

---

## **PHASE 13: Testing**

### 13.1 Test with Easy Maps
- [ ] Test with `maps/easy/01_linear_path.txt`
  - Verify 2 drones move linearly
  - Verify all zones appear
- [ ] Test with `maps/easy/02_simple_fork.txt`
  - Verify zones branch out
  - Verify drones split
- [ ] Test with `maps/easy/03_basic_capacity.txt`
  - Verify bottleneck zone shows capacity

### 13.2 Test with Medium Maps
- [ ] Test with `maps/medium/01_dead_end_trap.txt`
  - Verify dead-end zone is visible
  - Check drones navigate around it
- [ ] Test with `maps/medium/02_circular_loop.txt`
  - Verify loop structure is clear
- [ ] Test with `maps/medium/03_priority_puzzle.txt`
  - Verify priority zones highlighted differently

### 13.3 Test with Hard Maps
- [ ] Test with `maps/hard/01_maze_nightmare.txt`
  - Verify complex maze renders correctly
  - Check drones navigate through maze
- [ ] Test with `maps/hard/02_capacity_hell.txt`
  - Verify capacity labels on all gates
- [ ] Test with `maps/hard/03_ultimate_challenge.txt`
  - Verify large map fits on screen

### 13.4 Test Features
- [ ] Test all keyboard controls
  - SPACE/Arrow keys work
  - Turn counter updates
  - Drones change position
- [ ] Test mouse hover detection
  - Zones highlight on hover
  - Sidebar updates on hover
- [ ] Test debug mode ('d' key)
  - Console output appears
  - Information is accurate
- [ ] Test zoom (UP/DOWN arrows)
  - Zones scale properly
  - Drones scale with zones
- [ ] Test quit ('q' key)
  - Program exits cleanly

---

## **PHASE 14: Polish & Optimization**

### 14.1 Visual Polish
- [ ] Adjust font sizes for readability
- [ ] Fine-tune colors for contrast
- [ ] Add spacing/padding for cleanliness
- [ ] Test on different screen sizes
- [ ] Ensure sidebar doesn't overlap game area

### 14.2 Performance
- [ ] Profile with large maps (25+ drones)
- [ ] Optimize drawing loops if needed
- [ ] Reduce redraws if possible
- [ ] Check memory usage
- [ ] Ensure smooth 30 FPS

### 14.3 Edge Cases
- [ ] Handle map with single zone
- [ ] Handle map with many drones (50+)
- [ ] Handle very long location names
- [ ] Handle drones that don't move at some turns
- [ ] Handle connections with high capacity (100+)

### 14.4 Documentation
- [ ] Add docstrings to all methods
- [ ] Add inline comments for complex logic
- [ ] Document coordinate system
- [ ] Document color meanings
- [ ] Add usage examples in comments

---

## **PHASE 15: Final Integration**

### 15.1 Pipe Integration Test
- [ ] Run: `python3 simulator.py maps/easy/01_linear_path.txt | python3 visualizer.py maps/easy/01_linear_path.txt`
- [ ] Verify visualizer starts
- [ ] Verify drones animate
- [ ] Verify all turns visible

### 15.2 Cross-platform Testing
- [ ] Test on Linux
- [ ] Test on macOS
- [ ] Test on Windows
- [ ] Verify keyboard mapping works

### 15.3 User Experience
- [ ] Test first-time user experience
- [ ] Ensure controls are intuitive
- [ ] Verify startup messages are helpful
- [ ] Check error messages are clear

---

## **Completion Checklist**

- [ ] All 15 phases completed
- [ ] All maps tested successfully
- [ ] All features working
- [ ] No crashes or errors
- [ ] Smooth 30 FPS performance
- [ ] Code documented
- [ ] Ready for production

---

## **Quick Reference: What Each Phase Creates**

| Phase | Creates | Purpose |
|-------|---------|---------|
| 1 | Basic class & init | Foundation |
| 2 | Parsers & data structures | Input handling |
| 3 | Position calculations | Screen mapping |
| 4 | Zone & connection drawing | Basic visualization |
| 5 | Drone rendering | Animate drones |
| 6 | Turn navigation | User control |
| 7 | Sidebar UI | Information display |
| 8 | Header & stats | Context info |
| 9 | Hover & grid | Interactivity |
| 10 | Zoom, history, debug | Advanced features |
| 11 | Main draw loop | Frame rendering |
| 12 | Startup & cleanup | Entry point |
| 13 | Test suite | Quality assurance |
| 14 | Polish | User experience |
| 15 | Integration | Final testing |

---

## **Time Estimate**

- Phase 1-3: **Foundation** (~30 min)
- Phase 4-5: **Core Visualization** (~1 hour)
- Phase 6-8: **Navigation & UI** (~45 min)
- Phase 9-10: **Interactivity** (~30 min)
- Phase 11-12: **Main Loop** (~30 min)
- Phase 13-15: **Testing & Polish** (~1 hour)

**Total: ~4-5 hours for complete implementation**

