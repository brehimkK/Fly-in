*This project has been created as part of the 42 curriculum by brel-bou.*

# Fly-in

## Description

Fly-in is a drone routing simulation project. The goal is to move a group of drones from a start hub to an end hub while respecting map constraints such as blocked zones, restricted zones, priority zones, zone capacity, and connection capacity.

The program reads a map file, parses all hubs and connections, calculates valid paths for each drone, prints the turn-by-turn simulation output, and displays the result with a Pygame visualizer.

The project focuses on three main parts:

* parsing and validating a custom map format;
* finding safe paths for multiple drones without collisions;
* showing the simulation visually in a clear and understandable way.

## Features

* Custom map parser.
* Support for multiple drones.
* Start and end hubs.
* Normal, restricted, priority, and blocked zones.
* Zone capacity with `max_drones`.
* Connection capacity with `max_link_capacity`.
* Turn-by-turn terminal output.
* Pygame visualizer with background, zone images, drone images, and connection images.
* Smooth drone movement between zones.
* Zoom and camera movement in the visualizer.
* Color indicators for zones.
* Collision avoidance using reservations.

## Instructions

### Requirements

This project uses Python and Pygame.

Install dependencies with:

```bash
make install
```

If dependencies are not installed automatically, install Pygame manually:

```bash
pip install pygame
```

### Run the project

To run the default map:

```bash
make run
```

The default map is defined inside the `Makefile`:

```makefile
MAP ?= config.txt
```

### Debug mode

The Makefile also contains a debug target using `pdb`:

```bash
make debug
```

For visual debugging, the project can also be launched from VS Code using a `launch.json` configuration.

### Linting

Run normal lint checks:

```bash
make lint
```

## Map Format

A map starts with the number of drones:

```txt
nb_drones: 3
```

Then it defines a start hub:

```txt
start_hub: start 0 0 [color=green max_drones=6]
```

Then normal hubs:

```txt
hub: waypoint1 1 0 [color=blue max_drones=2]
hub: waypoint2 2 0 [zone=restricted color=orange max_drones=1]
```

Then an end hub:

```txt
end_hub: goal 3 0 [color=red max_drones=6]
```

Finally, connections are defined:

```txt
connection: start-waypoint1 [max_link_capacity=2]
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Supported zone metadata:

```txt
zone=restricted
zone=priority
zone=blocked
color=<color_name>
max_drones=<positive_number>
```

Supported connection metadata:

```txt
max_link_capacity=<positive_number>
```

## Algorithm Choices and Implementation Strategy

The core of the project is a time-space pathfinding algorithm.

Instead of only searching by zone name, the algorithm searches using both the zone and the turn:

```txt
(zone, turn)
```

This is important because two drones can use the same zone at different times, but they should not exceed the zone capacity during the same turn.

For example:

```txt
Drone 1: waypoint1 at turn 2
Drone 2: waypoint1 at turn 5
```

This is valid because the drones are not occupying the zone at the same time.

The pathfinder uses a priority queue with this structure:

```txt
(cost, turn, current_zone, path_history)
```

The queue always explores the lowest-cost option first. This makes the algorithm close to a Dijkstra-style search, with extra rules for drone simulation constraints.

At each step, the drone has two possible actions.

First, it can wait in the same zone for one more turn. Waiting is necessary because a zone or connection may be full at the current turn but available later.

Second, it can try to move to a connected neighbor zone. Before the move is accepted, the algorithm checks:

* whether the neighbor zone is blocked;
* whether the connection has available capacity;
* whether the destination zone has available capacity;
* whether the destination zone is restricted;
* whether the move needs one turn or two turns;
* whether the move conflicts with existing reservations.

Normal zones take one turn to enter.

Restricted zones take two turns to enter. This means the connection must also be available for the extra turn.

Priority zones have a lower movement cost, so the algorithm prefers them when possible.

After a path is found for one drone, the path is reserved. The reservation system stores:

```txt
(zone_name, turn)
```

for zone usage, and:

```txt
(previous_zone, next_zone, turn)
```

for connection usage.

This allows the next drone to avoid already occupied zones and connections.

The general algorithm flow is:

```txt
1. Start from the start hub.
2. Push the first state into the priority queue.
3. Pop the cheapest state.
4. Skip it if it was already visited.
5. Return the path if the end hub is reached.
6. Try waiting.
7. Try moving through every valid connection.
8. Check capacities and restrictions.
9. Push valid states back into the queue.
10. Repeat until a path is found or no valid path exists.
```

A maximum turn limit is also used to prevent infinite searching on invalid or impossible maps.

## Visual Representation

The project includes a Pygame visualizer to make the simulation easier to understand.

The visualizer displays:

* a background map image;
* zone sprites;
* drone sprites;
* connection sprites;
* zone labels;
* drone labels;
* colored indicators for zone metadata;
* smooth drone movement from one zone to another.

The visual representation improves the user experience because the terminal output only shows movements as text. The visualizer makes it easier to see the structure of the map, bottlenecks, restricted areas, and how drones move over time.

The user can also interact with the map:

* zoom in and out using the mouse wheel;
* drag the map with the mouse;
* pause and resume the simulation;
* step through turns manually.

This helps during debugging and evaluation because it becomes easier to understand why a drone waits, why it chooses a specific path, or where a capacity bottleneck happens.

## Project Structure

Example structure:

```txt
.
├── simulator.py
├── map_parser.py
├── pathfinder.py
├── models.py
├── visualizer.py
├── Makefile
├── assets/
│   ├── map.png
│   ├── zone.png
│   ├── drone.png
│   └── connection.png
└── config.txt
```

Main files:

* `simulator.py`: coordinates parsing, pathfinding, output, and visualization.
* `map_parser.py`: reads and validates the map file.
* `pathfinder.py`: calculates safe drone paths.
* `models.py`: contains the main data classes.
* `visualizer.py`: renders the simulation with Pygame.
* `Makefile`: provides simple commands to run, debug, clean, and lint the project.

## Example Output

Example terminal output:

```txt
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

Each line represents one simulation turn.

A movement has this format:

```txt
D<drone_id>-<zone_name>
```

For restricted movements, a drone can also appear on a connection before arriving.

Example:

```txt
D1-waypoint1-waypoint2
```

This means the drone is currently travelling between two zones.

## Resources

Useful resources used during the project:

* Python documentation: https://docs.python.org/3/
* Pygame documentation: https://www.pygame.org/docs/
* Python `heapq` documentation: https://docs.python.org/3/library/heapq.html
* Python typing documentation: https://docs.python.org/3/library/typing.html
* Dijkstra algorithm overview: https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
* A* search algorithm overview: https://en.wikipedia.org/wiki/A*_search_algorithm

## AI Usage

AI was used as a support tool during development.

It helped with:

* explaining Python concepts in simpler terms;
* reviewing parser edge cases;
* improving error messages;
* explaining the pathfinding algorithm;
* simplifying parts of the visualizer;
* helping document the project;
* suggesting debugging strategies.

AI was not used as an automatic replacement for implementation. The project logic, tests, debugging decisions, and final integration were reviewed and adapted manually by me.

The main parts where AI assistance was useful were:

* understanding the time-space pathfinding approach;
* explaining the reservation dictionaries;
* improving the README wording;
* making the Pygame visualizer easier to understand and maintain.

## Notes

This project is designed for learning purposes. The implementation focuses on clarity, validation, and explainability, while still providing a working simulation and visual representation of drone routing constraints.
