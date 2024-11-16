def calc_square_foot(size, damage):
    mults = [0.1,0.3,0.5,0.7,0.9]
    if size == 1:
        return (2300 * mults[int(damage)])
    if size == 2:
        return ((25000 * 5)*mults[int(damage)])
    if size == 3:
        
        return ((25000 * 15)*mults[int(damage)])

def order_rebuild(buildings, total_resource):
    current_use = 0
    order_repair = []
    for i in range(buildings.shape[0]):
        square_foot = calc_square_foot(buildings[i,4],buildings[i,1]) 
        if(square_foot+ current_use < total_resource):
            order_repair.append(buildings[i,:])
            current_use += square_foot
        if(square_foot > (10*(total_resource - current_use)) ): #add or statement with score ==0 
            return current_use, order_repair
        else:
            continue
    return current_use, order_repair