import Log from '../models/Log.js';

export async function createLog({ userId, username, eventType, eventCategory, description, ipAddress, severity, relatedEntity }) {
  try {
    const logEntry = new Log({
      userId,
      username,
      eventType,
      eventCategory,
      description,
      ipAddress,
      severity,
      relatedEntity,
      timestamp: new Date()
    });

    return await logEntry.save();
    console.log('Log saved:', logEntry);
  } catch (error) {
    console.error('Error saving log:', error);
  }
}