import { useState, useEffect } from 'react';
import db from '@/db';
import type { GeneratedPlan } from '@/types';
import { Dumbbell, Flame, Clock } from 'lucide-react';

const USER_ID = 'user-1';

export default function WorkoutSchedule() {
  const [plan, setPlan] = useState<GeneratedPlan | null>(null);
  const [activeDay, setActiveDay] = useState(0);

  useEffect(() => {
    db.generatedPlan.where('userId').equals(USER_ID).first().then(p => setPlan(p || null));
    setActiveDay(new Date().getDay() === 0 ? 6 : new Date().getDay() - 1);
  }, []);

  if (!plan) {
    return (
      <div className="text-center py-12 text-text-muted">
        <Dumbbell size={48} className="mx-auto mb-3 opacity-30" />
        <p>请先在「设置」中生成你的训练计划</p>
      </div>
    );
  }

  const day = plan.weeklyWorkout[activeDay];
  const totalBurn = day.actions.reduce((s, a) => s + a.caloriesBurned, 0);

  return (
    <div className="space-y-5">
      <h2 className="text-xl font-bold flex items-center gap-2">
        <Dumbbell size={22} className="text-secondary" />
        跑步机计划
      </h2>

      {/* Day selector */}
      <div className="flex gap-1 overflow-x-auto pb-1">
        {plan.weeklyWorkout.map((d, i) => (
          <button
            key={i}
            onClick={() => setActiveDay(i)}
            className={`flex-shrink-0 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeDay === i ? 'bg-secondary text-white' : 'bg-surface text-text-muted border border-border'
            }`}
          >
            {d.dayName}
          </button>
        ))}
      </div>

      {/* Day detail */}
      <div className="bg-surface rounded-xl p-4 shadow-sm border border-border">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="font-semibold text-lg">{day.dayName}</div>
            <div className="text-sm text-text-muted">{day.focus}</div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-1 text-sm text-danger justify-end">
              <Flame size={14} />
              -{totalBurn} kcal
            </div>
            <div className="flex items-center gap-1 text-xs text-text-muted justify-end">
              <Clock size={12} />
              {day.estimatedMinutes} 分钟
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {day.actions.map((action, i) => (
          <div key={i} className={`bg-surface rounded-xl p-4 flex items-center justify-between shadow-sm border ${action.caloriesBurned > 0 ? 'border-border' : 'border-border opacity-50'}`}>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-secondary/10 flex items-center justify-center text-sm font-bold text-secondary">
                {i + 1}
              </div>
              <div>
                <div className="font-medium">{action.exerciseName}</div>
                <div className="text-xs text-text-muted">{action.targetMuscles}</div>
              </div>
            </div>
            <div className="text-right text-sm">
              <div className="text-text-muted">{action.reps} 分钟</div>
              {action.caloriesBurned > 0 && (
                <div className="text-danger font-medium">-{action.caloriesBurned} kcal</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
