import { useState, useEffect } from 'react';
import db from '@/db';
import type { UserSettings, GeneratedPlan, TodaySuggestion } from '@/types';
import { getCoachTip, calculateTotalBurn, calculateDailyCalorieTarget, calculateDailyDeficit } from '@/utils/suggestions';
import { Dumbbell, UtensilsCrossed, Scale, Flame, TrendingDown } from 'lucide-react';

const USER_ID = 'user-1';

export default function TodayPage() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [plan, setPlan] = useState<GeneratedPlan | null>(null);
  const [today, setToday] = useState<TodaySuggestion | null>(null);
  const [weightInput, setWeightInput] = useState('');
  const [showWeightInput, setShowWeightInput] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const [s, p] = await Promise.all([
      db.userSettings.where('userId').equals(USER_ID).first(),
      db.generatedPlan.where('userId').equals(USER_ID).first(),
    ]);
    setSettings(s || null);
    setPlan(p || null);

    if (s && p) {
      const todayIdx = new Date().getDay() === 0 ? 6 : new Date().getDay() - 1;
      const diet = p.weeklyDiet[todayIdx];
      const workout = p.weeklyWorkout[todayIdx];
      const daysUntil = Math.max(0, Math.ceil(
        (new Date(s.targetDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
      ));
      const totalDays = Math.max(1, Math.ceil(
        (new Date(s.targetDate).getTime() - new Date(p.startDate).getTime()) / (1000 * 60 * 60 * 24)
      ));
      const progress = Math.min(100, Math.round(((totalDays - daysUntil) / totalDays) * 100));

      setToday({
        date: new Date().toISOString().split('T')[0],
        daysUntilTarget: daysUntil,
        progressPercent: progress,
        currentWeight: s.currentWeight,
        targetWeight: s.targetWeight,
        diet,
        workout,
        coachTip: getCoachTip(s, daysUntil),
      });
    }
  };

  const saveWeight = async () => {
    const w = parseFloat(weightInput);
    if (!w || !settings) return;
    await db.userSettings.where('userId').equals(USER_ID).modify({ currentWeight: w });
    setSettings({ ...settings, currentWeight: w });
    setShowWeightInput(false);
    loadData();
  };

  if (!settings) {
    return (
      <div className="text-center py-12 text-text-muted">
        <Scale size={48} className="mx-auto mb-3 opacity-30" />
        <p>请先前往「设置」填写身体数据和目标</p>
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="text-center py-12 text-text-muted">
        <Flame size={48} className="mx-auto mb-3 opacity-30" />
        <p>请前往「设置」生成你的极限计划</p>
      </div>
    );
  }

  if (!today) return null;

  const weightDiff = today.currentWeight - today.targetWeight;
  const totalBurn = settings ? calculateTotalBurn(settings) : 0;
  const dietTarget = settings ? calculateDailyCalorieTarget(settings) : 0;
  const netDeficit = totalBurn - dietTarget; // 实际净赤字 = 总消耗 - 饮食摄入
  const { deficit: theoreticalDeficit } = settings ? calculateDailyDeficit(settings) : { deficit: 0 };

  return (
    <div className="space-y-5">
      {/* Date */}
      <div className="text-center">
        <div className="text-sm text-text-muted">
          {new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' })}
        </div>
      </div>

      {/* Weight & Progress */}
      <div className="bg-surface rounded-2xl p-5 shadow-sm border border-border">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="text-sm text-text-muted">当前体重</div>
            <div className="text-3xl font-bold">{today.currentWeight}<span className="text-sm text-text-muted font-normal ml-1">kg</span></div>
          </div>
          <div className="text-right">
            <div className="text-sm text-text-muted">目标</div>
            <div className="text-xl font-semibold text-success">{today.targetWeight}kg</div>
          </div>
        </div>
        <div className="w-full bg-bg rounded-full h-2.5">
          <div className="bg-primary h-2.5 rounded-full transition-all" style={{ width: `${today.progressPercent}%` }} />
        </div>
        <div className="flex justify-between mt-1 text-xs text-text-muted">
          <span>进度 {today.progressPercent}%</span>
          <span>{today.daysUntilTarget} 天</span>
        </div>
        <button
          onClick={() => setShowWeightInput(true)}
          className="mt-3 w-full py-2 text-sm text-primary bg-primary-light rounded-lg"
        >
          更新体重
        </button>
      </div>

      {/* Deficit Card */}
      <div className="bg-danger/5 rounded-xl p-4 border border-danger/20">
        <div className="flex items-center gap-2 mb-2">
          <TrendingDown size={16} className="text-danger" />
          <span className="font-semibold text-danger">每日净赤字</span>
        </div>
        <div className="text-2xl font-bold text-danger">{netDeficit} kcal</div>
        <div className="text-xs text-text-muted mt-1">
          总消耗 {totalBurn} - 摄入 {dietTarget} = 净赤字 {netDeficit}
        </div>
        <div className="text-xs text-text-muted">
          理论赤字 {theoreticalDeficit} kcal · 还需减 {weightDiff.toFixed(1)} kg · {today.daysUntilTarget} 天
        </div>
      </div>

      {/* Coach Tip */}
      <div className="bg-primary-light rounded-xl p-4 border border-primary/20">
        <div className="text-sm text-text leading-relaxed">{today.coachTip}</div>
      </div>

      {/* Today's Diet */}
      <div className="bg-surface rounded-xl shadow-sm border border-border overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
          <UtensilsCrossed size={18} className="text-danger" />
          <span className="font-semibold">今日老乡鸡食谱</span>
          <span className="text-xs text-text-muted ml-auto">{today.diet.dailyCalories} kcal</span>
        </div>
        <div className="divide-y divide-border">
          {today.diet.meals.map(meal => (
            <div key={meal.mealType} className="px-4 py-3">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-sm">{meal.mealName}</span>
                <span className="text-xs text-text-muted">{meal.totalCalories} kcal</span>
              </div>
              <div className="text-xs text-text-muted">
                {meal.items.map((item, i) => (
                  <span key={i}>
                    {item.foodName} {item.quantity}{item.unit}
                    {i < meal.items.length - 1 ? ' + ' : ''}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Today's Workout */}
      <div className="bg-surface rounded-xl shadow-sm border border-border overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
          <Dumbbell size={18} className="text-secondary" />
          <span className="font-semibold">今日跑步机</span>
          <span className="text-xs text-text-muted ml-auto">
            {today.workout.actions.reduce((s, a) => s + a.caloriesBurned, 0)} kcal
          </span>
        </div>
        <div className="divide-y divide-border">
          {today.workout.actions.map((action, i) => (
            <div key={i} className="px-4 py-3 flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">{action.exerciseName}</div>
                <div className="text-xs text-text-muted">{action.targetMuscles}</div>
              </div>
              <div className="text-xs text-text-muted text-right">
                <div>{action.reps} 分钟</div>
                <div className="text-danger">-{action.caloriesBurned} kcal</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Weight Input Modal */}
      {showWeightInput && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-surface rounded-2xl p-6 w-full max-w-sm">
            <h3 className="text-lg font-bold mb-4">更新体重</h3>
            <input
              type="number"
              step="0.1"
              placeholder={String(today.currentWeight)}
              value={weightInput}
              onChange={e => setWeightInput(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-border bg-bg text-text text-lg text-center focus:outline-none focus:ring-2 focus:ring-primary/50 mb-4"
              autoFocus
            />
            <div className="flex gap-3">
              <button onClick={() => setShowWeightInput(false)} className="flex-1 py-3 rounded-xl bg-bg text-text font-medium">取消</button>
              <button onClick={saveWeight} className="flex-1 py-3 rounded-xl bg-primary text-white font-medium">保存</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
