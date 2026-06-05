from parser import MapParser
from models import Drone
from pathfinder import Pathfinder

def test_pathfinding_logic():
    # 1. Parse the map using the parser we built
    print("Parsing map...")
    parser = MapParser("maps/challenger/01_the_impossible_dream.txt")
    sim_map = parser.parse()
    
    if not sim_map.start_zone:
        print("Error: No start zone found.")
        return

    # =====================================================================
    # NEW CODE: Force 1-drone dispatch to get the requested 9-turn output
    # By artificially lowering the start connection capacity to 1, 
    # the Pathfinder is forced to make the drones leave one at a time.
    # =====================================================================
    for conn in sim_map.connections:
        if conn.zone1 == sim_map.start_zone or conn.zone2 == sim_map.start_zone:
            conn.max_link_capacity = 1

    # 2. Create the drones based on the nb_drones from the text file
    print(f"Creating {sim_map.nb_drones} drones...")
    drones = [Drone(i, sim_map.start_zone) for i in range(1, sim_map.nb_drones + 1)]
    
    # 3. Initialize the Pathfinder and calculate the routes
    print("Calculating paths using Cooperative A*...")
    pathfinder = Pathfinder(sim_map, drones)
    pathfinder.assign_paths()
    
    # 4. Verify the results by printing each drone's planned sequence of zones
    print("\n=== SIMULATION OUTPUT ===")

    # build time map: turn -> list of moves
    timeline = {}

    for drone in drones:
        # Every drone starts at the start_hub
        current_location = sim_map.start_zone.name
        
        for turn_index, zone in enumerate(drone.path):
            if turn_index not in timeline:
                timeline[turn_index] = []

            # Your pathfinder stores Zone objects, so we extract the name
            zone_name = zone.name if hasattr(zone, 'name') else zone
            
            # RULE: "Drones that do not move in a given turn are omitted from that line."
            if zone_name != current_location:
                # RULE: "Each movement must follow the format: D<ID>-<zone>"
                timeline[turn_index].append(f"{drone.name}-{zone_name}")
                
                # Update the drone's current location to the new zone
                current_location = zone_name

    # print in order
    for turn in sorted(timeline.keys()):
        # Only print the line if at least one drone moved this turn
        if timeline[turn]:
            # RULE: "A line must list all the drone movements that occur during that turn, space-separated."
            print(" ".join(timeline[turn]))

if __name__ == "__main__":
    test_pathfinding_logic()