import sets



list1 = [[0,0,0,0,1,1,1,0,1,1,0,0],
         [0,0,0,1,1,0,1,1,1,0,0,0],
         [0,0,0,0,1,1,1,1,1,1,0,0]]


class Safe_zone:
    delay_index
    is_safe_haven = False
    distance_from_low_edge
    distance_from_high_edge

    def __init__(self, refclk_index, sclk_index, start_index):
        self.delay_index = (refclk_index, sclk_index)
        self.distance_from_low_edge = sclk_index - start_index

    def __lt__(self, other):
        #safe_haven status takes priority
        if self.is_safe_haven and not other.is_safe_haven:
            return False
        elif not self.is_safe_haven and other.is_safe_haven:
            return True
        #with equal safe_haven status, edge distance decides ordering,
        #and the product of edge distances divided by their sum 
        #makes for a nice weighting metric: ab/(a+b) = 1/(1/a+1/b)
        else:
            my_distance_metric = 1.0 / ( 1.0/self.distance_from_low_edge + 1.0/self.distance_from_high_edge )
            their_distance_metric = 1.0 / ( 1.0/other.distance_from_low_edge + 1.0/other.distance_from_high_edge )
            return my_distance_metric < their_distance_metric
             


def search_sclk_delay_list(refclk_index, sclk_delay_list, safe_zones, dead_zones):
    max_bad_zones = 3
    start_index = 0
    stop_index = -1
    indices_since_last_safe_zone = 0
    in_safe_region = False
    temporary_safe_zone_list = []
    for sclk_index, test_was_succesful in enumerate(sclk_delay_list):
        if in_safe_region: 
            if test_was_succesful:
                temporary_safe_zone_list.append( Safe_zone(refclk_index,sclk_index,start_index) )
                indices_since_last_safe_zone = 0
            else:
                if indices_since_last_safe_zone >= max_bad_zones:
                    dead_zones = dead_zones[:-max_bad_zones]
                    stop_index = index - indices_since_last_safe_zone
                    break
                else:
                    dead_zones.append( (refclk_index, sclk_index) )
                    indices_since_last_safe_zone += 1
        elif test_was_succesful:
            start_index = index
            in_safe_region = True
    if stop_index == -1:
        dead_zones = dead_zones[:-indices_since_last_safe_zone]
        stop_index = len(sclk_delay_list) - indices_since_last_safe_zone

    for zone in temporary_safe_zone_list:
        zone.distance_from_high_edge = stop_index - zone.delay_index[1]
        safe_zones[zone.delay_index] = zone



def remove_dead_zones(safe_zones, dead_refclk_index, dead_sclk_index):
    adjacent_dead_index = (dead_refclk_index, dead_sclk_index)
    if adjacent_dead_index in safe_zones:
        del safe_zones[adjacent_dead_index]



def sanctify_haven(save_zones, haven_refclk_index, haven_sclk_index):
    haven_index = (haven_refclk_index, haven_sclk_index)
    if haven_index in safe_zones:
        safe_zone[haven_index].is_safe_haven = True



#As defined by Tiankuan Liu:
#   Adjacent dead zones are any indices that are: 
#       1 down, 2 to the right of a dead zone,
#       or 1 up, 2 to the left of a dead zone
#   Havens are any indices that are:
#       1 up, 1 right of a dead zone,
#       or 1 down, 1 left of a dead zone
def process_dead_zone(dead_zone, safe_zones):
    remove_dead_zones(safe_zones, dead_zone[0]-1, dead_zone[1]+2)
    remove_dead_zones(safe_zones, dead_zone[0]+1, dead_zone[1]-2)
    sanctify_haven(save_zones, dead_zone[0]+1, dead_zone[1]+1)
    sanctify_haven(save_zones, dead_zone[0]-1, dead_zone[1]-1)



def select(delay_list):
    safe_zones = {}
    dead_zones = []
    for refclk_index, sclk_delay_list in enumerate(delay_list):
        search_sclk_delay_list(refclk_index, sclk_delay_list, safe_zones, dead_zones)
    for dead_zone in dead_zones:
        process_dead_zone(dead_zone, safe_zones)
    optimal_safe_zone = sorted( list(safe_zones.values()) )[0]
    return optimal_safe_zone.delay_index
