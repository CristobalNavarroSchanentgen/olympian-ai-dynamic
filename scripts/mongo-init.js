// MongoDB initialization script for Olympian AI
// This script runs when MongoDB container starts for the first time

// Switch to the olympian_ai database
db = db.getSiblingDB('olympian_ai');

// Create collections with validation schemas
db.createCollection('conversations', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['userId', 'createdAt', 'messages'],
      properties: {
        userId: {
          bsonType: 'string',
          description: 'User ID who owns this conversation'
        },
        title: {
          bsonType: 'string',
          description: 'Conversation title'
        },
        createdAt: {
          bsonType: 'date',
          description: 'Creation timestamp'
        },
        updatedAt: {
          bsonType: 'date',
          description: 'Last update timestamp'
        },
        messages: {
          bsonType: 'array',
          items: {
            bsonType: 'object',
            required: ['role', 'content', 'timestamp'],
            properties: {
              role: {
                enum: ['user', 'assistant', 'system'],
                description: 'Message role'
              },
              content: {
                bsonType: 'string',
                description: 'Message content'
              },
              timestamp: {
                bsonType: 'date',
                description: 'Message timestamp'
              }
            }
          }
        },
        metadata: {
          bsonType: 'object',
          description: 'Additional metadata'
        }
      }
    }
  }
});

db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['email', 'createdAt'],
      properties: {
        email: {
          bsonType: 'string',
          pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
          description: 'User email address'
        },
        username: {
          bsonType: 'string',
          description: 'Username'
        },
        passwordHash: {
          bsonType: 'string',
          description: 'Hashed password'
        },
        createdAt: {
          bsonType: 'date',
          description: 'Account creation timestamp'
        },
        lastLogin: {
          bsonType: 'date',
          description: 'Last login timestamp'
        },
        preferences: {
          bsonType: 'object',
          description: 'User preferences'
        },
        isActive: {
          bsonType: 'bool',
          description: 'Account active status'
        }
      }
    }
  }
});

db.createCollection('services', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'endpoint', 'status', 'discoveredAt'],
      properties: {
        name: {
          bsonType: 'string',
          description: 'Service name'
        },
        endpoint: {
          bsonType: 'string',
          description: 'Service endpoint URL'
        },
        status: {
          enum: ['active', 'inactive', 'error'],
          description: 'Service status'
        },
        discoveredAt: {
          bsonType: 'date',
          description: 'Discovery timestamp'
        },
        lastChecked: {
          bsonType: 'date',
          description: 'Last health check timestamp'
        },
        capabilities: {
          bsonType: 'array',
          description: 'Service capabilities'
        },
        metadata: {
          bsonType: 'object',
          description: 'Additional service metadata'
        }
      }
    }
  }
});

db.createCollection('models', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'provider', 'addedAt'],
      properties: {
        name: {
          bsonType: 'string',
          description: 'Model name'
        },
        provider: {
          bsonType: 'string',
          description: 'Model provider (e.g., ollama)'
        },
        version: {
          bsonType: 'string',
          description: 'Model version'
        },
        addedAt: {
          bsonType: 'date',
          description: 'When model was added'
        },
        lastUsed: {
          bsonType: 'date',
          description: 'Last usage timestamp'
        },
        config: {
          bsonType: 'object',
          description: 'Model configuration'
        }
      }
    }
  }
});

db.createCollection('api_keys', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['userId', 'keyHash', 'createdAt'],
      properties: {
        userId: {
          bsonType: 'string',
          description: 'User who owns this API key'
        },
        keyHash: {
          bsonType: 'string',
          description: 'Hashed API key'
        },
        name: {
          bsonType: 'string',
          description: 'API key name/description'
        },
        createdAt: {
          bsonType: 'date',
          description: 'Creation timestamp'
        },
        lastUsed: {
          bsonType: 'date',
          description: 'Last usage timestamp'
        },
        expiresAt: {
          bsonType: 'date',
          description: 'Expiration timestamp'
        },
        scopes: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          },
          description: 'API key permissions'
        },
        isActive: {
          bsonType: 'bool',
          description: 'Key active status'
        }
      }
    }
  }
});

// Create indexes for better performance
db.conversations.createIndex({ userId: 1, createdAt: -1 });
db.conversations.createIndex({ updatedAt: -1 });
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ username: 1 }, { unique: true, sparse: true });
db.services.createIndex({ name: 1 }, { unique: true });
db.services.createIndex({ status: 1 });
db.models.createIndex({ name: 1, provider: 1 }, { unique: true });
db.api_keys.createIndex({ userId: 1 });
db.api_keys.createIndex({ keyHash: 1 }, { unique: true });

// Create a read-write user for the application
db.createUser({
  user: 'olympian_app',
  pwd: process.env.MONGODB_APP_PASSWORD || 'change_me_in_production',
  roles: [
    {
      role: 'readWrite',
      db: 'olympian_ai'
    }
  ]
});

print('MongoDB initialization completed successfully!');