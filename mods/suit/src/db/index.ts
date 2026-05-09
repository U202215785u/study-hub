import Dexie, { type EntityTable } from 'dexie';
import type { FoodItem, UserSettings, GeneratedPlan } from '@/types';

const db = new Dexie('CoachDB') as Dexie & {
  foodItem: EntityTable<FoodItem, 'id'>;
  userSettings: EntityTable<UserSettings, 'id'>;
  generatedPlan: EntityTable<GeneratedPlan, 'id'>;
};

db.version(3).stores({
  foodItem: '++id, name, category',
  userSettings: '++id, userId',
  // treadmillMinutes added to userSettings schema implicitly via Dexie dynamic schema
  generatedPlan: '++id, userId, startDate',
});

export default db;
