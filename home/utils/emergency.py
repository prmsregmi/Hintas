
import numpy as np

EARTH_RADIUS_MILES = 3958.8  # Average radius of the Earth in miles

def haversine_distance(coord1, coord2):
    print(coord1, coord2)
    lat1, lon1 = np.radians(coord1)
    lat2, lon2 = np.radians(coord2)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    return EARTH_RADIUS_MILES * c

# Filter Dataset Based on Distance from Starting Point
def filter_within_range(lat, lon, starting_point, max_distance_miles):
    # print(lat, lon, starting_point)
    distance = haversine_distance(starting_point, (lat, lon))
    return False if distance > max_distance_miles else True

def calc_distance(dataset, starting_point):
    distances = np.zeros(dataset.shape[0])
    for i in range(dataset.shape[0]):
        distances[i] = haversine_distance(starting_point, [dataset[i,2],dataset[i,3]])
    return distances

def sort_by_distance(houses, start):
    distances = calc_distance(houses, start[:2])
    sorted_indices = np.argsort(distances)
    return houses[sorted_indices].tolist()

def emergency_sort(dataset, loc1, loc2, max_mile, number_teams):
    # First call filter within range func on dataset with given num miles
    # houses_in_area, distances = filter_within_range(dataset[dataset[:, 1] > 1], [loc1, loc2], max_mile)
    
    houses_in_area = dataset
    if houses_in_area.shape[0] == 0:
        return []  # No houses in the specified range
    
    # Initialize team routes and remaining houses
    team_routes = [[] for _ in range(number_teams)]
    remaining_houses = houses_in_area.tolist()
    
    # Assign starting points for each team
    starting_points = []
    for _ in range(number_teams):
        # Filter for priority houses (e.g., type 3)
        priority = np.array([house for house in remaining_houses if house[1] == 2])
        
        if priority.shape[0] == 0:  # If no priority houses, take from all remaining
            priority = np.array(remaining_houses)
        
        if priority.shape[0] == 0:  # If still no houses, stop assigning starting points
            break
        
        # Calculate distances from the current location
        small_dist = calc_distance(priority, [loc1, loc2])
        
        # Find the closest starting point
        min_index = np.argmin(small_dist)
        
        start = priority[min_index]
        
        starting_points.append(start)
        remaining_houses.remove(start.tolist())  # Remove from remaining
    
    # Assign houses to teams based on starting points
    for team_index, start in enumerate(starting_points):
        # Group houses within a smaller range for this team
        
        group_list, group_distances = filter_within_range(
            np.array(remaining_houses), start[:2], max_mile / number_teams
        )
        
        # Assign houses to the team
        team_routes[team_index] = sort_by_distance(group_list, start)
        
        # Remove assigned houses from remaining list
        for house in group_list.tolist():
            if house in remaining_houses:
                remaining_houses.remove(house)
    
    # Handle leftover houses
    while remaining_houses:
        # Find the team with the fewest houses
        smallest_team = min(team_routes, key=len)
        team_index = team_routes.index(smallest_team)
        
        # Find the nearest house to the last house in the team's route
        last_house = team_routes[team_index][-1] if team_routes[team_index] else starting_points[team_index]
        small_dist = calc_distance(np.array(remaining_houses), last_house[:2])
        min_index = np.argmin(small_dist)
        closest_house = remaining_houses.pop(min_index)
        
        # Assign the house to the team
        team_routes[team_index].append(closest_house)
    
    return team_routes
