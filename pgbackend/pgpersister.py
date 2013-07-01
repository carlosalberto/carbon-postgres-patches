"""Copyright 2012 Carlos Alberto Cortez

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License."""

import os
import datetime
import time

from carbon import state
from carbon.cache import MetricCache
from carbon.storage import getFilesystemPath, loadStorageSchemas, loadAggregationSchemas
from carbon.conf import settings
from carbon import log, events, instrumentation
from carbon.persister import BasePersister

from pgbackendsettings import *

import psycopg2

class PostgresqlPersister(BasePersister):
    def __init__ (self):
        self._connection_alive = False
        self._connection = None

    def check_alive(self):
        if self._connection_alive:
            return

        if hasattr(self, '_connection'): #Try to close any previous connection
            try:
                self._connection.close()
            except:
                pass

        connection = psycopg2.connect(database=PGBACKEND_SETTINGS["dbname"],
                        host=PGBACKEND_SETTINGS["host"],
                        user=PGBACKEND_SETTINGS["user"],
                        password=PGBACKEND_SETTINGS["password"])

        self._connection = connection
        self._connection_alive = True

    def mark_dead(self):
        self._connection_alive = False
        self._connection = None

    @property
    def is_alive(self):
        return self._connection_alive

    #Our persister takes for granted the databases are
    #created already (which is different to Whisper, which creates
    #one per Metric, on demand)
    def get_dbinfo(self, metric):
        '''
        Gets the database info related to a metric, as well as whether it
        exists already or not (as a tuple)
        '''
        return ('latest_stats', True)

    def update_one(self, metric, datapoint):
        value = datapoint[1]
        timestamp = datetime.datetime.fromtimestamp(int(datapoint[0]))

        # Don't pollute the database with empty counters (totally useless).
        if metric.startswith('stats_counts') and value == 0:
            return

        log.msg("Updating metric %s using the postgresql persister" % (metric,))

        #log.msg("INSERTING %s" % metric)
        sql_stmt =  """
            INSERT into latest_stats(name, tstamp, value)
            VALUES ('%s', '%s', %f);
        """
        cursor = self._connection.cursor()
        cursor.execute(sql_stmt % (metric, timestamp, value))
        #log.msg("successfully inserted value to metric %s" % (metric,))

    def update_many(self, metric, datapoints, dbIdentifier):
        '''
        Updates the datapoints for a metric.
        'metric' is the name of the param ('my.value')
        'datapoints' is a list of tuples, containing the timestamp and value
        '''

        '''
        Ignore the metrics with _90 for now (not sure what they do,
        besides repeating the info under some scenarios). Do the same
        with *.[upper|lower|mean], as we do not use them for now.
        '''
        if metric.endswith("_90") or metric.endswith(".upper") or \
            metric.endswith(".lower") or metric.endswith("mean"):
            return

        try:
            self.check_alive()

            for datapoint in datapoints:
                self.update_one(metric, datapoint)

        except psycopg2.Warning, e:
            log.msg("Received a warning while inserting values: %s" % (e,))
        except psycopg2.Error, e:
            log.msg("Failed to insert/update stats into postgresql: %s" % (e,))
            log.err()
            self.mark_dead() #Tell to retry/reconnect.

    def flush(self):
        if not self.is_alive:
            log.msg('Not flushing, as the connection is dead!')
            return

        try:
            self._connection.commit()
            log.msg('Flushed metrics.')
        except psycopg2.Warning, e:
            log.msg("Received a warning while flushing values: %s" % (e,))
        except psycopg2.Error, e:
            log.msg("Failed to commit while flushing values: %s" % (e,))
            log.err()
            self.mark_dead()

    def __del__(self):
        if self._connection_alive and hasattr(self, '_connection'):
            self._connection.close()

            self._connection = None
            self._connection_alive = False

