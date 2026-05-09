export interface FoodItem {
  id?: number;
  name: string;
  caloriesPerServing: number;  // 每份热量（老乡鸡按份卖）
  proteinPerServing: number;   // 每份蛋白质(g)
  carbsPerServing: number;     // 每份碳水(g)
  fatPerServing: number;       // 每份脂肪(g)
  category?: string;
  source?: string;
  createdAt?: string;
}

export interface UserSettings {
  id?: number;
  userId: string;
  gender: 'male' | 'female';
  birthDate: string;
  height: number;
  currentWeight: number;
  targetWeight: number;
  bodyFatPct?: number;
  activityLevel: number;
  dailyCalorieTarget: number;
  dailyProteinTarget: number;
  targetDate: string;
  treadmillMinutes: number;
  createdAt?: string;
  updatedAt?: string;
}

export interface MealItem {
  foodName: string;
  quantity: number;
  unit: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
}

export interface DailyMeal {
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  mealName: string;
  items: MealItem[];
  totalCalories: number;
  totalProtein: number;
  totalCarbs: number;
  totalFat: number;
}

export interface DailyDiet {
  dayIndex: number;
  dayName: string;
  meals: DailyMeal[];
  dailyCalories: number;
  dailyProtein: number;
  dailyCarbs: number;
  dailyFat: number;
}

export interface WorkoutAction {
  exerciseName: string;
  sets: number;
  reps: number;
  restSeconds: number;
  targetMuscles: string;
  caloriesBurned: number;
}

export interface DailyWorkout {
  dayIndex: number;
  dayName: string;
  focus: string;
  actions: WorkoutAction[];
  estimatedMinutes: number;
}

export interface GeneratedPlan {
  id?: number;
  userId: string;
  startDate: string;
  weeklyDiet: DailyDiet[];
  weeklyWorkout: DailyWorkout[];
  createdAt: string;
}

export interface TodaySuggestion {
  date: string;
  daysUntilTarget: number;
  progressPercent: number;
  currentWeight: number;
  targetWeight: number;
  diet: DailyDiet;
  workout: DailyWorkout;
  coachTip: string;
}
