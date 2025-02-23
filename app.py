import streamlit as st
import osmnx as ox
import networkx as nx
import pandas as pd

# Load the graph (assuming you have saved it as 'delhi_ev_graph.graphml')
G = ox.load_graphml('delhi_ev_graph.graphml')

def shortest_path_with_constraints(G, origin, destination, battery_range, charging_time, weight='length'):
    # Find the shortest path between origin and destination
    path = nx.shortest_path(G, origin, destination, weight=weight)

    # Calculate the path length
    path_length = nx.path_weight(G, path, weight=weight)

    # Check if the path length exceeds the battery range
    if path_length > battery_range:
        # Find charging stations on the path
        charging_stations_on_path = [node for node in path if G.nodes[node].get('charging_station', False)]

        # Check if there are charging stations on the path
        if charging_stations_on_path:
            # Find the nearest charging station to the origin
            nearest_charging_station = charging_stations_on_path[0]
            nearest_charging_station_distance = nx.shortest_path_length(G, origin, nearest_charging_station, weight=weight)

            # Compute the remaining battery range after reaching the nearest charging station
            remaining_battery_range = battery_range - nearest_charging_station_distance

            # Recursively compute the shortest path from the nearest charging station to the destination
            sub_path = shortest_path_with_constraints(G, nearest_charging_station, destination, remaining_battery_range + charging_time * 100, charging_time, weight)

            # Combine the sub-path with the current path
            path = path[:path.index(nearest_charging_station) + 1] + sub_path[1:]

    return path


# Define a function to compute the battery range gained by charging for a specified time
def compute_battery_range(charging_time):
    # Compute the battery range gained by charging for the specified time
    battery_range_gained = charging_time * 60  # Assume 60 km of range gained per hour of charging
    
    return battery_range_gained

# Streamlit app layout
st.title("EV Routing Application")

start_address = st.text_input("Enter starting address:", value="")
end_address = st.text_input("Enter destination address:", value="")
battery_charge = st.number_input("Enter current battery charge (in kilometers):", value=0)
charging_time = st.number_input("Enter charging time (in hours):", value=0)

if start_address and end_address and battery_charge is not None and charging_time is not None:
    # Geocode the addresses to get coordinates
    start_location = ox.geocode(start_address)
    end_location = ox.geocode(end_address) 

    # Find the nearest nodes to the starting and ending points
    start_node = ox.distance.nearest_nodes(G, X=[start_location[1]], Y=[start_location[0]], return_dist=False)[0]
    end_node = ox.distance.nearest_nodes(G, X=[end_location[1]], Y=[end_location[0]], return_dist=False)[0]

    # Compute the battery range gained by charging for the specified time
    battery_range_gained = compute_battery_range(charging_time)

    # Compute the battery range considering the current battery charge and charging time
    battery_range = battery_charge + battery_range_gained

    # Compute the shortest path using Dijkstra's algorithm based on distance and battery constraints
    shortest_path = shortest_path_with_constraints(G, start_node, end_node, battery_range, charging_time, weight='length')
    shortest_path_distance = nx.shortest_path_length(G, source=start_node, target=end_node, weight='length', method='dijkstra')
    # Get the route geometry
    route_edges = ox.utils_graph.get_route_edge_attributes(G, shortest_path, attribute='geometry')
    route_geometry = [item for sublist in route_edges for item in sublist]
    
    # Plot the route
    fig, ax = ox.plot_graph_route(G, route=shortest_path, route_linewidth=6, node_size=0, bgcolor='k', edge_color='gray', edge_alpha=0.2, route_color='b')

# Plot the origin and destination nodes
    orig_node_geom = G.nodes[start_node]['route_geometry']
    dest_node_geom = G.nodes[end_node]['route_geometry']
    ax.scatter(orig_node_geom.x, orig_node_geom.y, c='r', s=100, zorder=3)
    ax.scatter(dest_node_geom.x, dest_node_geom.y, c='r', s=100, zorder=3)
    
#  # Plot the route
#     fig, ax = ox.plot_graph_route(G, route=route_geometry, route_linewidth=6, node_size=0, bgcolor='k', edge_color='gray', edge_alpha=0.2, orig_dest_node_color='r', route_color='b')

# # Show the route map
#     st.pyplot(route_map)

# Display the route distance
    st.write(f"Shortest path distance: {shortest_path_distance} meters")
