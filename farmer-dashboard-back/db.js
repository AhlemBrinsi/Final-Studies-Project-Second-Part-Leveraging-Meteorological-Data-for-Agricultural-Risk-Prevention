import { MongoClient } from 'mongodb';
import dotenv from 'dotenv';

dotenv.config();

const uri = process.env.MONGODB_URI;

const client = new MongoClient(uri, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

let db;

export async function getDB() {
  if (!db) {
    await client.connect();
    db = client.db('dashboard'); 
  }
  return db;
}
