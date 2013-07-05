
import os, datetime

def get_stat_type(name):
    """
    Get the stat type based/infered on its name.
    """
    if name.startswith("stats_counts"):
        return StatObject.CounterType

    if name.startswith("stats.timers") and \
       (name.endswith(".count") or name.endswith(".sum")):
        return StatObject.TimerType

    return StatObject.IgnoredType

def get_stat_info(name):
    '''
    Get a tuple containing the type of stat, as well as its
    corresponding key (canonical name, we could think of).
    '''

    stat_type = get_stat_type(name)
    if stat_type == StatObject.IgnoredType:
        return (StatObject.IgnoredType, None)

    ''' substring, just everything after stats_counts '''
    if stat_type == StatObject.CounterType:
        return (StatObject.CounterType, name[13:])

    if stat_type == StatObject.TimerType:
        retval = name[13:]

        if retval.endswith(".count"):
            retval = retval[:-6]
        else:
            retval = retval[:-4]

        return (StatObject.TimerType, retval)

    '''if name.startswith("carbon.agents"):
        return (StatObject.CarbonType, "")'''

    raise Exception("Unrecognized metric: %s" % name)


def create_stat_obj(name, stat_type):
    if stat_type == StatObject.CounterType:
        return CounterObject(name)
    if stat_type == StatObject.TimerType:
        return TimerObject(name)

    ''' Anything else is not supported now '''
    return None

class StatObject(object):

    CarbonType = 0
    CounterType = 1
    TimerType = 2
    LastValueType = 3
    IgnoredType = 99

    def __init__(self, name):
        self.name = name

    @property
    def stat_type(self):
        raise Exception("StatObject cannot be used. Use a derived class instead.")

    def get_values(self):
        '''
        Returns list of tuples containing
        a datetime (for a day) and its value.
        '''
        return None

    def process_value(self, value_name, value, tstamp):
        '''
        Process a specific metric corresponding to a
        specific stat (such my.timer.sum or my.timer.low, for
        the metric my.timer), with its corresponding timestamp
        '''
        pass

    def evaluate(self):
        '''
        Evaluates all the values for this metric,
        so a list of generated values can be ready
        '''
        pass

class CounterObject(StatObject):

    def __init__(self, name):
        StatObject.__init__(self, name)

        self.day_counters = {}

    @property
    def stat_type(self):
        return StatObject.CounterType

    def process_value(self, value_name, value, tstamp):
        value_date = tstamp.date()
        day_value = self.day_counters.get(value_date, None)
        if day_value == None:
            self.day_counters[value_date] = value
        else:
            self.day_counters[value_date] = day_value + value

    def get_values(self):
        ''' No post-evaluation needed here. '''
        return self.day_counters
    
class TimerInfo(object):
    def __init__(self):
        self.count = -1
        self.sum = -1

    @property
    def is_complete(self):
        return self.count > -1 and self.sum > -1

class TimerObject(StatObject):

    def __init__(self, name):
        StatObject.__init__(self, name)

        self.day_timers = {}
        self.is_evaluted = False

    @property
    def stat_type(self):
        return StatObject.TimerType

    def process_value(self, value_name, value, tstamp):
        if not value_name.endswith("count") and not value_name.endswith("sum"):
            raise Exception("Invalid metric. It should end with 'count' or 'sum':%s" % value_name)

        value_date = tstamp.date()
        stat_list = self.day_timers.get(value_date, None)
        if stat_list == None:
            stat_list = {}
            self.day_timers[value_date] = stat_list

        stat_info = stat_list.get(tstamp, None)
        if stat_info == None:
            stat_info = TimerInfo()
            stat_list[tstamp] = stat_info

        if value_name.endswith(".count"):
            stat_info.count = value
        else:
            stat_info.sum = value

    def evaluate(self):
        values = {}
        for stat_day, stat_list in self.day_timers.iteritems():

            count = sum = 0
            for stat_tstamp, stat_info in stat_list.iteritems():
                if not stat_info.is_complete:
                    print 'Stat %s is incomplete!' % self.name
                    ''' Discard incomplete stats '''
                    continue

                count = count + stat_info.count
                sum = sum + stat_info.sum

            values[stat_day] = sum / count

        self.values = values
        self.is_evaluated = True

    def get_values(self):
        if not self.is_evaluated:
            '''
            Force a call to evaluate() in case we haven't computed the
            values
            '''
            self.evaluate()

        return self.values


