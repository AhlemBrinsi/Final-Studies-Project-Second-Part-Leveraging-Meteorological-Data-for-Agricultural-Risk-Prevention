import mongoose from 'mongoose';
import { createLog } from './logger.js';
import Log from '../models/Log.js';


async function test() {
  try {
    await mongoose.connect('mongodb://localhost:27017/users', {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    });

    const mockLog = {
      userId: '64a92c8b123abc456def7890',
      username: 'test_user',
      eventType: 'ARTICLE_CREATE',
      eventCategory: 'Article',
      description: 'Article "Test Article Title" created',
      ipAddress: '127.0.0.1',
      severity: 'INFO',
      relatedEntity: 'Article:64b91a1b123abc456def7890',
    };

    const result = await createLog(mockLog);
    console.log('Log created:', result);
  } catch (err) {
    console.error('Error testing createLog:', err);
  } finally {
    await mongoose.disconnect();
  }
}

test();
