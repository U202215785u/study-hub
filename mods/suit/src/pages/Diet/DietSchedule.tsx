import { useState, useEffect } from 'react';
import db from '@/db';
import type { GeneratedPlan } from '@/types';
import { UtensilsCrossed, Flame } from 'lucide-react';

const USER_ID = 'user-1';

export default function DietSchedule() {
  const [plan, setPlan] = useState<GeneratedPlan | null>(null);
  const [activeDay, setActiveDay] = useState(0);

  useEffect(() => {
    db.generatedPlan.where('userId').equals(USER_ID).first().then(p => setPlan(p || null));
    setActiveDay(new Date().getDay() === 0 ? 6 : new Date().getDay() - 1);
  }, []);

  if (!plan) {
    return (
      <div className="text-center py-12 text-text-muted">
        <UtensilsCrossed size={48} className="mx-auto mb-3 opacity-30" />
        <p>请先在「设置」中生成你的饮食计划</p>
      </div>
    );
  }

  const day = plan.weeklyDiet[activeDay];

  return (
    <div className="space-y-5">
      <h2 className="text-xl font-bold flex items-center gap-2">
        <UtensilsCrossed size={22} className="text-danger" />
        老乡鸡食谱
      </h2>

      {/* Day selector */}
      <div className="flex gap-1 overflow-x-auto pb-1">
        {plan.weeklyDiet.map((d, i) => (
          <button
            key={i}
            onClick={() => setActiveDay(i)}
            className={`flex-shrink-0 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeDay === i ? 'bg-danger text-white' : 'bg-surface text-text-muted border border-border'
            }`}
          >
            {d.dayName}
          </button>
        ))}
      </div>

      {/* Day summary */}
      <div className="bg-surface rounded-xl p-4 shadow-sm border border-border">
        <div className="flex items-center justify-between mb-2">
          <div className="font-semibold">{day.dayName} 营养汇总</div>
          <div className="flex items-center gap-1 text-sm text-danger">
            <Flame size={14} />
            {day.dailyCalories} kcal
          </div>
        </div>
        <div className="grid grid-cols-3 gap-2 text-center text-sm">
          <div className="bg-bg rounded-lg py-2">
            <div className="font-bold">{day.dailyProtein.toFixed(0)}g</div>
            <div className="text-xs text-text-muted">蛋白质</div>
          </div>
          <div className="bg-bg rounded-lg py-2">
            <div className="font-bold">{day.dailyCarbs.toFixed(0)}g</div>
            <div className="text-xs text-text-muted">碳水</div>
          </div>
          <div className="bg-bg rounded-lg py-2">
            <div className="font-bold">{day.dailyFat.toFixed(0)}g</div>
            <div className="text-xs text-text-muted">脂肪</div>
          </div>
        </div>
      </div>

      {/* Meals - 仅展示午餐和晚餐 */}
      <div className="space-y-3">
        {day.meals.map(meal => (
          <div key={meal.mealType} className="bg-surface rounded-xl shadow-sm border border-border overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <span className="font-semibold">{meal.mealName}</span>
              <span className="text-xs text-text-muted">{meal.totalCalories} kcal · P{meal.totalProtein}g</span>
            </div>
            <div className="divide-y divide-border">
              {meal.items.map((item, i) => (
                <div key={i} className="flex items-center justify-between px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{item.foodName}</span>
                    <span className="text-xs text-text-muted">{item.quantity}{item.unit}</span>
                  </div>
                  <div className="text-xs text-text-muted">
                    {item.calories} kcal
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
