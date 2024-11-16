from .emergency import filter_within_range

def estimate_living(build):
    if build == 1:
        return 4 # Assuming single family home
    if build == 2:
        return 100
    if build == 3:
        return 400
    else:
        return 0

def displaced(dataset, loc1, loc2, max_mile = 9999999999):
    in_range, distances = filter_within_range(dataset[dataset[:, 1] > 1], [loc1, loc2], max_mile)
    total = 0
    for i in range(in_range.shape[0]):
        total += estimate_living(int(in_range[i,4]))
    return total