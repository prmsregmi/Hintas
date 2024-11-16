def square_foot(size, damage):
    mults = [0.1,0.3,0.5,0.7,0.9]
    if size == 1:
        return (2300 * mults[int(damage)])/25000
    if size == 2:
        return ((25000 * 5)*mults[int(damage)])/25000
    if size == 3:
        
        return ((25000 * 15)*mults[int(damage)])/25000

def rebuild_class(damage_class):
    
    if damage_class == 2:
        return 0.2
    elif damage_class == 3:
        return 0.8
    elif damage_class == 4:
        return 0.2
    elif damage_class == 1:
        return 0.05
    else:
        return 0



def size_impact(size):
    if size == 1:
        return 0.2
    if size == 2:
        return 0.6
    if size == 3:
        return 0.8



def rebuild_score(damage_category, size):
    # if(haversine_distance([lat1,lon1], [lat2,lon2]) > max_mile):
    #     return 0
    # Taking into account estimated building materials (based on building size and perentage damaged)
    W1 = 0.7
    W2 = 0.25
    W3 = 0.05
    
    if damage_category == 0:
        return 0
    else:
       
        return W1 * rebuild_class(damage_category) + W2*size_impact(size) + W3* square_foot(size, damage_category)


