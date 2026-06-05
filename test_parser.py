from parser import MapParser

def test_easy_map():
    # 1. Initialize the parser with the easy map
    parser = MapParser("maps/hard/03_ultimate_challenge.txt")
    
    # 2. Parse the file into the SimulationMap object
    my_map = parser.parse()

    # 3. Print out the parsed data to verify
    print("=== MAP PARSING SUCCESSFUL ===")
    print(f"Total Drones: {my_map.nb_drones}") 
    
    if my_map.start_zone and my_map.end_zone:
        print(f"Start Zone: {my_map.start_zone.name}")
        print(f"End Zone: {my_map.end_zone.name}")
    
    print("\n--- Zones Parsed ---")
    for name, zone in my_map.zones.items():
        print(f"Zone: {name} | Type: {zone.zone_type} | Cap: {zone.max_drones} | Color: {zone.color}")

    print("\n--- Connections Parsed ---")
    for conn in my_map.connections:
        print(f"Link: {conn.zone1.name} <-> {conn.zone2.name} | Max Traffic: {conn.max_link_capacity}")

if __name__ == "__main__":
    test_easy_map()