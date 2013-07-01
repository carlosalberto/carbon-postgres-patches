"""Copyright 2009 Chris Davis

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
import time
from os.path import exists, dirname

import whisper

from carbon.cache import MetricCache
from carbon.conf import settings
from carbon.storage import getFilesystemPath, loadStorageSchemas, loadAggregationSchemas

class BasePersister(object):
  def get_dbinfo(self, metric):
    return ""

  def pre_get_datapoints_check(self, metric):
    return True

  def create_db(self, metric):
    pass

  def update_many(self, metric, datapoints, dbIdentifier):
    pass

  def flush(self):
    pass


class WhisperPersister(BasePersister):

  def get_dbinfo(self, metric):
    dbFilePath = getFilesystemPath(metric)
    return (dbFilePath, exists(dbFilePath))

  def pre_retrieve_metric_check(self, metric):
    dbinfo = self.get_dbinfo(metric)
    dbFilePath = dbInfo[0]
    dbFileExists = dbInfo[1]

    if not dbFileExists:
      createCount += 1
      now = time.time()

      if now - lastCreateInterval >= 60:
        lastCreateInterval = now
        createCount = 1

      elif createCount >= settings.MAX_CREATES_PER_MINUTE:
        # dropping queued up datapoints for new metrics prevents filling up the entire cache
        # when a bunch of new metrics are received.
        try:
          MetricCache.pop(metric)
        except KeyError:
          pass

        return False

    return True

  def create_db(self, metric):
    archiveConfig = None
    xFilesFactor, aggregationMethod = None, None
    
    for schema in schemas:
      if schema.matches(metric):
        log.creates('new metric %s matched schema %s' % (metric, schema.name))
        archiveConfig = [archive.getTuple() for archive in schema.archives]
        break

    for schema in agg_schemas:
      if schema.matches(metric):
        log.creates('new metric %s matched aggregation schema %s' % (metric, schema.name))
        xFilesFactor, aggregationMethod = schema.archives
        break

    if not archiveConfig:
      raise Exception("No storage schema matched the metric '%s', check your storage-schemas.conf file." % metric)

    dbDir = dirname(dbFilePath)
    os.system("mkdir -p -m 755 '%s'" % dbDir)

    log.creates("creating database file %s (archive=%s xff=%s agg=%s)" % 
                (dbFilePath, archiveConfig, xFilesFactor, aggregationMethod))
    whisper.create(dbFilePath, archiveConfig, xFilesFactor, aggregationMethod, settings.WHISPER_SPARSE_CREATE)
    os.chmod(dbFilePath, 0755)

  def update_many(self, metric, datapoints, dbIdentifier):
    dbFilePath = dbIdentifier
    whisper.update_many(dbFilePath, datapoints)

