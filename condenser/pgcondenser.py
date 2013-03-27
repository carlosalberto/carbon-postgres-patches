
import os
import psycopg2

from pgbackendsettings import *
from statshandling import *

DEFAULT_MAX_OLD = '3 months'

def open_connection():
        connection = psycopg2.connect(database=PGBACKEND_SETTINGS['dbname'],
                        host=PGBACKEND_SETTINGS['host'],
                        user=PGBACKEND_SETTINGS['user'],
                        password=PGBACKEND_SETTINGS['password'])
        return connection

'''
Our condense phase consist in retrieving data from our latest_stats table,
which is supposed to be cleaned/consumed by this module hourly, and then
putting those stats in our daily_stats table, which records stats per day.

We keep record of the average, min and max value, as well as special
handling for counters (stats whose first part of the name ends with _counts,
as defined by carbon itself, such 'stats_count.something.else'), and for that
case we keep an extra column, which keeps track of the actual count.

Finally, we clean the latest_stats table.
'''
def condense():
    stats_cache = {}

    try:
        connection = open_connection()

        sql = """
            SELECT
                name,
                tstamp,
                value
            FROM latest_stats
            ORDER BY 2 ASC
        """
        cursor = connection.cursor()
        cursor.execute(sql)
        data = cursor.fetchall()
        for x in data:
            name = x[0].strip()
            tstamp = x[1]
            value = x[2]

            stat_type, stat_key = get_stat_info(name)
            if stat_type == StatObject.IgnoredType:
                continue

            stat_obj = stats_cache.get(stat_key, None)
            if stat_obj == None:
                stat_obj = create_stat_obj(stat_key, stat_type)
                stats_cache[stat_key] = stat_obj

            stat_obj.process_value(name, value, tstamp)

        for stat_key, stat_obj in stats_cache.iteritems():
            stat_obj.evaluate()
            stat_type = stat_obj.stat_type
            if stat_type == StatObject.CounterType:
                name = "counters.%s" % stat_obj.name
            else:
                name = "timers.%s" % stat_obj.name

            for day, value in stat_obj.get_values().iteritems():
                sql_daily = """
                SELECT value
                FROM daily_stats
                WHERE name=%s and day=%s
                """
                cursor2 = connection.cursor()
                cursor2.execute(sql_daily, [name, day])
                daily_data = cursor2.fetchall()

                if len(daily_data) > 0:
                    # Retrieve the our single row.
                    for x in daily_data:
                        stored_value = x[0]
                        
                    if stat_type == StatObject.CounterType:
                        value = value + stored_value
                    elif stat_type == StatObject.TimerType:
                        value = (value + stored_value) / 2.0

                    sql_daily_insert = """
                    UPDATE daily_stats
                    SET value=%s
                    WHERE name=%s AND day=%s
                    """
                    cursor3 = connection.cursor()
                    cursor.execute(sql_daily_insert, [value, name, day])
                else:
                    sql_daily_insert = """
                    INSERT
                    INTO daily_stats(name, day, value)
                    VALUES(%s, %s, %s)
                    """
                    cursor3 = connection.cursor()
                    cursor.execute(sql_daily_insert, [name, day,
                                                      value])

        clear_sql = """
            DELETE FROM latest_stats
        """
        clear_cursor = connection.cursor()
        clear_cursor.execute(clear_sql)

        # Clear anything older than 3 months.
        clear_old_sql = """
            DELETE FROM daily_stats
            WHERE day < now() - interval %s
        """
        clear_cursor2 = connection.cursor()
        clear_cursor2.execute(clear_old_sql, (DEFAULT_MAX_OLD,))

        connection.commit()
    except psycopg2.Warning, e:
        print "Warning while performing the sql operation: %s" % e
    except psycopg2.Error, e:
        print "Error while performing the sql operation: %s" % e

def main():
    condense()

if __name__ == "__main__":
    main()

