import contextlib
import threading
from functools import partial, cached_property

import redis

_primary_client = redis.Redis(decode_responses=True)

_local = threading.local()

class RedisMixin:
   @property
   def wclient(self):
      return redis_write_client()

   @property
   def rclient(self):
      return redis_read_client()


class RedisHash(RedisMixin):
   @cached_property
   def decode_field_mappings(self):
      return {y: x for x, y in self.encode_field_mappings.items()}

   @classmethod
   def get_encoded_mapping(cls, instance):
      return {
         encoded_key: getattr(instance, key) for key, encoded_key in cls.encode_field_mappings.items()
      }

   @classmethod
   def set_instance(self, instance):
      self.wclient.hset(self.get_encoded_key(instance), mapping=self.get_encoded_mapping(instance))

class PipelineWrapper:
   def __init__(self, client):
      self.result = None
      self.client = client


@contextlib.contextmanager
def redis_pipeline(write):
   pipe = redis_read_client().pipeline() if not write else \
      redis_write_client().pipeline()
   _local.pipe = pipe
   _local.write = write
   wrapper = PipelineWrapper(pipe)
   try:
      yield wrapper
   finally:
      wrapper.result = _local.pipe.execute()
      _local.pipe = None


redis_read_pipeline = partial(redis_pipeline, write=False)
redis_write_pipeline = partial(redis_pipeline, write=True)


def _select_read_client():
   return _primary_client

def redis_read_client():
   if hasattr(_local, 'pipe'):
      return _local.pipe
   return _select_read_client()

def redis_write_client():
   if hasattr(_local, 'pipe'):
      if not _local.write:
         raise "当前pipeline不支持写"
      return _local.pipe
   else:
      return _primary_client
