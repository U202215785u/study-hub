import type { UserSettings, DailyDiet, DailyMeal, MealItem, DailyWorkout, WorkoutAction, GeneratedPlan } from '@/types';
import db from '@/db';

// ===== 统一热量计算引擎 =====
// 所有热量计算集中在此处，确保各页面数据一致

export function calculateAge(birthDate: string): number {
  const today = new Date();
  const birth = new Date(birthDate);
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return age;
}

/** 基础代谢率 BMR (Mifflin-St Jeor) */
export function calculateBMR(settings: UserSettings): number {
  const age = calculateAge(settings.birthDate);
  const weight = settings.currentWeight;
  const height = settings.height;
  if (settings.gender === 'male') {
    return 10 * weight + 6.25 * height - 5 * age + 5;
  }
  return 10 * weight + 6.25 * height - 5 * age - 161;
}

/**
 * TDEE = 日常总消耗（含工作/走路等日常活动，不含额外跑步机训练）
 * activityLevel: 1.2 久坐 / 1.375 轻度 / 1.55 中度 / 1.725 高度
 */
export function calculateTDEE(settings: UserSettings): number {
  return Math.round(calculateBMR(settings) * settings.activityLevel);
}

/** 计算每日运动消耗（按用户实际体重 + MET值精确计算） */
export function calculateExerciseBurn(settings: UserSettings): number {
  const minutes = settings.treadmillMinutes || 60;
  const weight = settings.currentWeight;
  // 跑步机平均 MET ≈ 10（不同训练模式在 8-12 之间），公式：MET × kg × 小时
  // 按周平均 MET = 10 估算，各天实际按各自MET细分
  const avgMET = 10;
  const hours = minutes / 60;
  return Math.round(avgMET * weight * hours);
}

/** 计算单日总消耗 = TDEE（日常）+ 运动消耗（额外） */
export function calculateTotalBurn(settings: UserSettings): number {
  return calculateTDEE(settings) + calculateExerciseBurn(settings);
}

/** 计算达到目标所需每日赤字 */
export function calculateDailyDeficit(settings: UserSettings): { deficit: number; daysUntilTarget: number } {
  const weightDiff = Math.max(0, settings.currentWeight - settings.targetWeight);
  const daysUntilTarget = Math.max(1, Math.ceil(
    (new Date(settings.targetDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
  ));
  const deficit = Math.round((weightDiff * 7700) / daysUntilTarget);
  return { deficit, daysUntilTarget };
}

/** 
 * 计算每日饮食热量目标。
 * 极限模式：饮食目标 = 总消耗 - 理论赤字（运动消耗用来"填"赤字，让你可以多吃）
 * 不设安全下限。如果结果为负，说明即使绝食也达不到目标，需要更多运动或更长时间。
 */
export function calculateDailyCalorieTarget(settings: UserSettings): number {
  const totalBurn = calculateTotalBurn(settings);
  const { deficit } = calculateDailyDeficit(settings);
  return Math.round(totalBurn - deficit);
}

/** 分析目标在当前参数下是否可行 */
export function analyzeTargetFeasibility(settings: UserSettings) {
  const tdee = calculateTDEE(settings);
  const exerciseBurn = calculateExerciseBurn(settings);
  const totalBurn = tdee + exerciseBurn;
  const { deficit, daysUntilTarget } = calculateDailyDeficit(settings);
  const dietTarget = calculateDailyCalorieTarget(settings);
  const netDeficit = totalBurn - dietTarget; // 理论上等于 deficit

  // BMR 安全参考线
  const bmr = calculateBMR(settings);
  const safeMin = Math.round(bmr * 0.6);

  // 如果不运动，纯靠饮食需要吃多少
  const sedentaryDietTarget = Math.round(tdee - deficit);

  // 达成目标所需的最低运动时长（如果当前不运动就无法达成）
  let minMinutesNeeded = 0;
  if (tdee < deficit) {
    const neededBurn = deficit - tdee;
    minMinutesNeeded = Math.ceil(neededBurn / (10 * settings.currentWeight / 60));
  }

  // 当前计划30天实际能减多少（按净赤字算）
  const actualWeightLoss = (netDeficit * daysUntilTarget) / 7700;

  return {
    feasible: dietTarget >= 0, // 饮食目标是否为正
    dietTarget,
    netDeficit,
    deficit,
    tdee,
    exerciseBurn,
    totalBurn,
    safeMin,
    sedentaryDietTarget,
    minMinutesNeeded,
    actualWeightLoss,
    daysUntilTarget,
  };
}

// ===== 极限模式计划生成（无安全限制）=====
export async function generatePlan(settings: UserSettings): Promise<GeneratedPlan> {
  const dailyCalories = calculateDailyCalorieTarget(settings);

  // 营养素目标（极限模式）
  const proteinTarget = Math.round(settings.currentWeight * 2.2);

  // 获取老乡鸡菜品库
  const foods = await db.foodItem.toArray();

  // 按类别分组
  const byCategory: Record<string, typeof foods> = {};
  for (const f of foods) {
    const cat = f.category || '其他';
    if (!byCategory[cat]) byCategory[cat] = [];
    byCategory[cat].push(f);
  }

  const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

  // 生成一周食谱
  const weeklyDiet: DailyDiet[] = weekDays.map((dayName, dayIndex) => {
    const meals = generateLaoxiangjiMeals(dailyCalories, proteinTarget, byCategory, dayIndex);
    const totals = meals.reduce(
      (s, m) => ({
        calories: s.calories + m.totalCalories,
        protein: s.protein + m.totalProtein,
        carbs: s.carbs + m.totalCarbs,
        fat: s.fat + m.totalFat,
      }),
      { calories: 0, protein: 0, carbs: 0, fat: 0 }
    );
    return {
      dayIndex,
      dayName,
      meals,
      dailyCalories: totals.calories,
      dailyProtein: totals.protein,
      dailyCarbs: totals.carbs,
      dailyFat: totals.fat,
    };
  });

  // 生成一周训练（按用户设定时长和体重精确计算消耗）
  const weeklyWorkout = generateWeeklyWorkout(settings.treadmillMinutes || 60, settings.currentWeight);

  return {
    userId: settings.userId,
    startDate: new Date().toISOString().split('T')[0],
    weeklyDiet,
    weeklyWorkout,
    createdAt: new Date().toISOString(),
  };
}

// ===== 老乡鸡精确热量匹配食谱生成 =====
function generateLaoxiangjiMeals(
  targetCalories: number,
  targetProtein: number,
  byCategory: Record<string, any[]>,
  dayIndex: number
): DailyMeal[] {
  const meats = byCategory['荤菜'] || [];
  const vegs = byCategory['素菜'] || [];
  const staples = byCategory['主食'] || [];

  const meals: DailyMeal[] = [];

  // 午餐55%，晚餐45%
  const lunchTarget = Math.round(targetCalories * 0.55);
  const dinnerTarget = Math.round(targetCalories * 0.45);
  const lunchProtein = Math.round(targetProtein * 0.55);
  const dinnerProtein = Math.round(targetProtein * 0.45);

  // 生成午餐（无汤）
  const lunch = buildMeal('lunch', '午餐', staples, meats, vegs, lunchTarget, lunchProtein, dayIndex);
  meals.push(lunch);

  // 生成晚餐
  const dinner = buildMeal('dinner', '晚餐', staples, meats, vegs, dinnerTarget, dinnerProtein, dayIndex + 7);
  meals.push(dinner);

  return meals;
}

function buildMeal(
  type: 'lunch' | 'dinner',
  name: string,
  staples: any[],
  meats: any[],
  vegs: any[],
  targetCal: number,
  _targetPro: number,
  seed: number
): DailyMeal {
  const items: MealItem[] = [];

  // 点餐逻辑：每种菜只选1个品种，各1份。靠「选什么菜」来匹配热量，不靠堆份数。
  // 只有主食可以加到2份（确实会吃两碗饭），荤菜/素菜固定1份。

  // 1. 选荤菜（固定1份，按蛋白/热量比排序后轮流选）
  const sortedMeats = [...meats].sort((a, b) =>
    (b.proteinPerServing / b.caloriesPerServing) - (a.proteinPerServing / a.caloriesPerServing)
  );
  const meatFood = pickOne(sortedMeats, seed);
  if (meatFood) {
    items.push(makeItem(meatFood, 1));
  }

  // 2. 选素菜（固定1份，按热量从低到高排序后轮流选）
  const sortedVegs = [...vegs].sort((a, b) => a.caloriesPerServing - b.caloriesPerServing);
  const vegFood = pickOne(sortedVegs, seed + 1);
  if (vegFood) {
    items.push(makeItem(vegFood, 1));
  }

  // 3. 选主食（1-2份，根据剩余热量决定）
  const usedCal = items.reduce((s, it) => s + it.calories, 0);
  const stapleTarget = targetCal - usedCal;
  // 找热量最接近 stapleTarget 的主食，尽量1份搞定，不够才2份
  const stapleFood = pickOneSortedByCalorie(staples, stapleTarget, seed);
  let stapleItem: MealItem | null = null;
  if (stapleFood) {
    const perServing = stapleFood.caloriesPerServing;
    let servings = 1;
    if (stapleTarget > perServing * 1.5) servings = 2;
    if (stapleTarget < perServing * 0.5 && perServing > 200) servings = 1; // 再少也得吃1份
    stapleItem = makeItem(stapleFood, servings);
    items.push(stapleItem);
  }

  // 4. === 热量校准 ===
  // 只调主食份数（±1份），不碰荤菜/素菜的品种和份数
  const currentMeal = makeMeal(type, name, items);
  const calDiff = targetCal - currentMeal.totalCalories;
  if (stapleItem && stapleFood && Math.abs(calDiff) >= 10) {
    const adjust = calDiff > 0 ? 1 : -1; // 差太多就加/减1份主食
    const newQty = clamp(stapleItem.quantity + adjust, 1, 2);
    if (newQty !== stapleItem.quantity) {
      const idx = items.findIndex(i => i.foodName === stapleItem!.foodName);
      if (idx >= 0) items[idx] = makeItem(stapleFood, newQty);
    }
  }

  return makeMeal(type, name, items);
}

function pickOneSortedByCalorie(arr: any[], targetCal: number, seed: number): any | null {
  if (!arr || arr.length === 0) return null;
  // 找热量最接近 targetCal 的（按每份估算）
  const sorted = [...arr].sort((a, b) => {
    const aDiff = Math.abs(a.caloriesPerServing - targetCal);
    const bDiff = Math.abs(b.caloriesPerServing - targetCal);
    return aDiff - bDiff;
  });
  return sorted[seed % sorted.length];
}

function pickOne(arr: any[], seed: number): any | null {
  if (!arr || arr.length === 0) return null;
  return arr[seed % arr.length];
}

function clamp(val: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, val));
}

function makeItem(food: any, servings: number): MealItem {
  return {
    foodName: food.name,
    quantity: servings,
    unit: '份',
    calories: Math.round(food.caloriesPerServing * servings),
    protein: Math.round(food.proteinPerServing * servings * 10) / 10,
    carbs: Math.round(food.carbsPerServing * servings * 10) / 10,
    fat: Math.round(food.fatPerServing * servings * 10) / 10,
  };
}

function makeMeal(type: 'breakfast' | 'lunch' | 'dinner' | 'snack', name: string, items: MealItem[]): DailyMeal {
  const totals = items.reduce(
    (s, it) => ({
      calories: s.calories + it.calories,
      protein: s.protein + it.protein,
      carbs: s.carbs + it.carbs,
      fat: s.fat + it.fat,
    }),
    { calories: 0, protein: 0, carbs: 0, fat: 0 }
  );
  return {
    mealType: type,
    mealName: name,
    items,
    totalCalories: totals.calories,
    totalProtein: totals.protein,
    totalCarbs: totals.carbs,
    totalFat: totals.fat,
  };
}

// ===== 跑步机训练计划（按体重精确计算MET消耗）=====
// MET公式: Calories = MET × 体重(kg) × 时间(小时)
const MET_VALUES: Record<string, { warm: number; main: number; cool: number }> = {
  steady:       { warm: 3.5, main: 11.5, cool: 3.0 },  // 匀速跑
  incline:      { warm: 3.5, main: 9.0,  cool: 3.0 },  // 爬坡走
  interval:     { warm: 3.5, main: 12.0, cool: 3.0 },  // 间歇跑
  long:         { warm: 3.5, main: 9.0,  cool: 3.0 },  // 慢跑
  fartlek:      { warm: 3.5, main: 11.0, cool: 3.0 },  // 变速跑
  'hiit-incline': { warm: 3.5, main: 12.0, cool: 3.0 }, // 高强度爬坡
};

function generateWeeklyWorkout(minutes: number = 60, weightKg: number = 75): DailyWorkout[] {
  const weekPlan: { dayName: string; focus: string; type: string }[] = [
    { dayName: '周一', focus: '跑步机 匀速跑', type: 'steady' },
    { dayName: '周二', focus: '跑步机 爬坡走', type: 'incline' },
    { dayName: '周三', focus: '跑步机 间歇跑', type: 'interval' },
    { dayName: '周四', focus: '跑步机 长距离慢跑', type: 'long' },
    { dayName: '周五', focus: '跑步机 变速跑', type: 'fartlek' },
    { dayName: '周六', focus: '跑步机 高强度爬坡', type: 'hiit-incline' },
    { dayName: '周日', focus: '彻底休息', type: 'rest' },
  ];

  return weekPlan.map((day, dayIndex) => {
    if (day.type === 'rest') {
      return {
        dayIndex,
        dayName: day.dayName,
        focus: day.focus,
        actions: [{ exerciseName: '休息日', sets: 1, reps: 0, restSeconds: 0, targetMuscles: '恢复', caloriesBurned: 0 }],
        estimatedMinutes: 0,
      };
    }
    const actions = buildTreadmillActions(minutes, day.type, weightKg);
    return {
      dayIndex,
      dayName: day.dayName,
      focus: day.focus,
      actions,
      estimatedMinutes: actions.reduce((sum, a) => sum + a.reps, 0),
    };
  });
}

function buildTreadmillActions(minutes: number, type: string, weightKg: number): WorkoutAction[] {
  const mets = MET_VALUES[type] || MET_VALUES['steady'];
  const warmMin = Math.max(5, Math.round(minutes * 0.15));
  const coolMin = Math.max(5, Math.round(minutes * 0.10));
  const mainMin = minutes - warmMin - coolMin;

  // 按MET精确计算每段消耗
  const calcBurn = (met: number, min: number) => Math.round(met * weightKg * (min / 60));
  const warmBurn = calcBurn(mets.warm, warmMin);
  const mainBurn = calcBurn(mets.main, mainMin);
  const coolBurn = calcBurn(mets.cool, coolMin);

  switch (type) {
    case 'steady':
      return [
        { exerciseName: `跑步机热身 6km/h`, sets: 1, reps: warmMin, restSeconds: 0, targetMuscles: '热身', caloriesBurned: warmBurn },
        { exerciseName: `跑步机匀速跑 10km/h`, sets: 1, reps: mainMin, restSeconds: 0, targetMuscles: '心肺+脂肪', caloriesBurned: mainBurn },
        { exerciseName: `跑步机缓降步行 4km/h`, sets: 1, reps: coolMin, restSeconds: 0, targetMuscles: '恢复', caloriesBurned: coolBurn },
      ];
    case 'incline':
      return [
        { exerciseName: `跑步机热身 5km/h`, sets: 1, reps: warmMin, restSeconds: 0, targetMuscles: '热身', caloriesBurned: warmBurn },
        { exerciseName: `跑步机爬坡 坡度12% 5.5km/h`, sets: 1, reps: mainMin, restSeconds: 0, targetMuscles: '下肢+脂肪', caloriesBurned: mainBurn },
        { exerciseName: `跑步机缓降步行`, sets: 1, reps: coolMin, restSeconds: 0, targetMuscles: '恢复', caloriesBurned: coolBurn },
      ];
    case 'interval':
      return [
        { exerciseName: `跑步机热身 6km/h`, sets: 1, reps: warmMin, restSeconds: 0, targetMuscles: '热身', caloriesBurned: warmBurn },
        { exerciseName: `跑步机间歇 12km/h冲刺1分钟+6km/h走2分钟`, sets: Math.floor(mainMin / 3), reps: 3, restSeconds: 0, targetMuscles: '心肺+脂肪', caloriesBurned: mainBurn },
        { exerciseName: `跑步机缓降步行`, sets: 1, reps: coolMin, restSeconds: 0, targetMuscles: '恢复', caloriesBurned: coolBurn },
      ];
    case 'long':
      return [
        { exerciseName: `跑步机热身 5km/h`, sets: 1, reps: warmMin, restSeconds: 0, targetMuscles: '热身', caloriesBurned: warmBurn },
        { exerciseName: `跑步机慢跑 8km/h`, sets: 1, reps: mainMin, restSeconds: 0, targetMuscles: '耐力+脂肪', caloriesBurned: mainBurn },
        { exerciseName: `跑步机缓降步行`, sets: 1, reps: coolMin, restSeconds: 0, targetMuscles: '恢复', caloriesBurned: coolBurn },
      ];
    case 'fartlek':
      return [
        { exerciseName: `跑步机热身 6km/h`, sets: 1, reps: warmMin, restSeconds: 0, targetMuscles: '热身', caloriesBurned: warmBurn },
        { exerciseName: `跑步机变速 8km/h慢+11km/h快交替`, sets: Math.floor(mainMin / 10), reps: 10, restSeconds: 0, targetMuscles: '心肺+脂肪', caloriesBurned: mainBurn },
        { exerciseName: `跑步机缓降步行`, sets: 1, reps: coolMin, restSeconds: 0, targetMuscles: '恢复', caloriesBurned: coolBurn },
      ];
    case 'hiit-incline':
      return [
        { exerciseName: `跑步机热身 5km/h`, sets: 1, reps: warmMin, restSeconds: 0, targetMuscles: '热身', caloriesBurned: warmBurn },
        { exerciseName: `跑步机高强度爬坡 坡度15% 6km/h`, sets: 1, reps: mainMin, restSeconds: 0, targetMuscles: '下肢+脂肪', caloriesBurned: mainBurn },
        { exerciseName: `跑步机缓降步行`, sets: 1, reps: coolMin, restSeconds: 0, targetMuscles: '恢复', caloriesBurned: coolBurn },
      ];
    default:
      return [
        { exerciseName: `跑步机热身`, sets: 1, reps: warmMin, restSeconds: 0, targetMuscles: '热身', caloriesBurned: warmBurn },
        { exerciseName: `跑步机匀速跑`, sets: 1, reps: mainMin, restSeconds: 0, targetMuscles: '心肺+脂肪', caloriesBurned: mainBurn },
        { exerciseName: `跑步机缓降`, sets: 1, reps: coolMin, restSeconds: 0, targetMuscles: '恢复', caloriesBurned: coolBurn },
      ];
  }
}

// ===== 极限模式教练提示 =====
export function getCoachTip(settings: UserSettings, daysUntilTarget: number): string {
  const weightDiff = settings.currentWeight - settings.targetWeight;
  if (weightDiff <= 0) return '目标已达成。进入维持期，逐步增加碳水恢复代谢。';

  const { deficit: dailyDeficit } = calculateDailyDeficit(settings);
  const totalBurn = calculateTotalBurn(settings);
  const dietTarget = calculateDailyCalorieTarget(settings);
  const netDeficit = totalBurn - dietTarget; // 实际净赤字 = 总消耗 - 饮食摄入

  if (daysUntilTarget <= 7) {
    return `🔥 最后${daysUntilTarget}天冲刺！每日净赤字 ${netDeficit} kcal（消耗${totalBurn} - 摄入${dietTarget}），严格执行零欺骗餐。`;
  }
  if (dailyDeficit > 1000) {
    return `⚠️ 每日理论赤字 ${dailyDeficit} kcal，实际净赤字 ${netDeficit} kcal（含跑步机额外消耗）。确保睡眠8小时+，必要时补充BCAA防止肌肉分解。`;
  }
  return `📉 每日理论赤字 ${dailyDeficit} kcal，实际净赤字 ${netDeficit} kcal（总消耗${totalBurn} - 摄入${dietTarget}）。严格执行计划，不要偷吃。`;
}

export function getActivityLabel(level: number): string {
  if (level <= 1.2) return '久坐';
  if (level <= 1.375) return '轻度活动';
  if (level <= 1.55) return '中度活动';
  return '高度活动';
}

export function getActivityOptions() {
  return [
    { value: 1.2, label: '久坐 (1.2)' },
    { value: 1.375, label: '轻度活动 (1.375)' },
    { value: 1.55, label: '中度活动 (1.55)' },
    { value: 1.725, label: '高度活动 (1.725)' },
  ];
}
