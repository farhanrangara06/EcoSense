const { Redis } = require('@upstash/redis');

let memoryState = null;

function createMemoryStore() {
  return {
    async get(key) {
      if (key === 'app-data') return memoryState;
      return null;
    },
    async setJSON(key, value) {
      if (key === 'app-data') memoryState = value;
    },
  };
}

function createStore() {
  if (process.env.UPSTASH_REDIS_REST_URL && process.env.UPSTASH_REDIS_REST_TOKEN) {
    const redis = Redis.fromEnv();
    return {
      async get(key) {
        return redis.get(key);
      },
      async setJSON(key, value) {
        await redis.set(key, value);
      },
    };
  }
  return createMemoryStore();
}

module.exports = { createStore };
