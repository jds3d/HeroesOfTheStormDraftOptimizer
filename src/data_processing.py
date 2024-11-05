import constants

def compute_map_adjusted_win_rate(map_win_rate, general_win_rate):
    return (constants.MAP_WEIGHT * map_win_rate +
            constants.GENERAL_WEIGHT * general_win_rate)

def apply_exponential_decay(win_rate, days_since_last_patch):
    return win_rate * (constants.DECAY_CONSTANT ** days_since_last_patch)
