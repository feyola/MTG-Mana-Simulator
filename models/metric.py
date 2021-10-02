from statistics import mean, median, mode, variance

class Metric:
    """Computations that can be executed on the amount of mana in a turn (across traces)"""

    mean = None
    median = None
    mode = None
    variance = None
    below_curve = None
    on_curve = None
    above_curve = None

    def __init__(self, name, func):
        self.name = name
        self.func = func
    def compute(self, traces):
        return [self.func(turn+1, manas_by_turn) for turn,manas_by_turn in enumerate(zip(*traces))]

    @staticmethod
    def minimum_mana(min_mana: int):
        return Metric("≥{} mana".format(min_mana), lambda t,ms: sum(m >= min_mana for m in ms)/len(ms))
    @staticmethod
    def percentile(p: float):
        return Metric("{}th percentile".format(p), lambda t,ms: sorted(ms)[round(len(ms)*p)-1])

Metric.mean        = Metric("Mean",         lambda t,ms: mean(ms))
Metric.median      = Metric("Median",       lambda t,ms: int(median(ms)))
Metric.mode        = Metric("Mode",         lambda t,ms: mode(ms))
Metric.variance    = Metric("Variance",     lambda t,ms: variance(ms))
Metric.below_curve = Metric("<'turn' mana", lambda t,ms: sum(m <  t for m in ms)/len(ms))
Metric.on_curve    = Metric("≥'turn' mana", lambda t,ms: sum(m >= t for m in ms)/len(ms))
Metric.above_curve = Metric(">'turn' mana", lambda t,ms: sum(m >  t for m in ms)/len(ms))
