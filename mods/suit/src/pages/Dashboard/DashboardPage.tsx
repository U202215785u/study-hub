import { useState, useEffect } from 'react';
import db from '@/db';
import type { UserSettings, GeneratedPlan } from '@/types';
import { calculateTDEE, calculateExerciseBurn, calculateTotalBurn, calculateDailyDeficit } from '@/utils/suggestions';
import { Flame, Dumbbell, Target, TrendingDown } from 'lucide-react';

const USER_ID = 'user-1';

export default function DashboardPage() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [plan, setPlan] = useState<GeneratedPlan | null>(null);

  useEffect(() => {
    db.userSettings.where('userId').equals(USER_ID).first().then(s => setSettings(s || null));
    db.generatedPlan.where('userId').equals(USER_ID).first().then(p => setPlan(p || null));
  }, []);

  if (!settings || !plan) {
    return (
      <div className="text-center py-12 text-text-muted">
        <Target size={48} className="mx-auto mb-3 opacity-30" />
        <p>请先在「设置」中填写数据并生成计划</p>
      </div>
    );
  }

  const daysUntil = Math.max(0, Math.ceil(
    (new Date(settings.targetDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
  ));
  const totalDays = Math.max(1, Math.ceil(
    (new Date(settings.targetDate).getTime() - new Date(plan.startDate).getTime()) / (1000 * 60 * 60 * 24)
  ));
  const progress = Math.min(100, Math.round(((totalDays - daysUntil) / totalDays) * 100));
  const tdee = calculateTDEE(settings);
  const exerciseBurn = calculateExerciseBurn(settings);
  const totalBurn = calculateTotalBurn(settings);
  const { deficit: dailyDeficit } = calculateDailyDeficit(settings);
  const netDeficit = totalBurn - settings.dailyCalorieTarget;
  const weightDiff = settings.currentWeight - settings.targetWeight;

  const weekCalories = plan.weeklyDiet.map(d => d.dailyCalories);
  const weekBurn = plan.weeklyWorkout.map(d => d.actions.reduce((s, a) => s + a.caloriesBurned, 0));
  // 每天的总消耗 = TDEE + 当天运动消耗
  const weekTotalBurn = weekBurn.map(b => tdee + b);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold flex items-center gap-2">
        <Target size={22} className="text-primary" />
        目标进度
      </h2>

      {/* Main Goal Card */}
      <div className="bg-surface rounded-2xl p-5 shadow-sm border border-border">
        <div className="text-center mb-4">
          <div className="text-sm text-text-muted">目标进度</div>
          <div className="text-4xl font-bold text-primary">{progress}%</div>
          <div className="text-xs text-text-muted mt-1">{daysUntil} 天后达成目标</div>
        </div>
        <div className="w-full bg-bg rounded-full h-3">
          <div className="bg-primary h-3 rounded-full transition-all" style={{ width: `${progress}%` }} />
        </div>
        <div className="flex justify-between mt-3 text-sm">
          <div className="text-center flex-1">
            <div className="font-bold text-lg">{settings.currentWeight}</div>
            <div className="text-xs text-text-muted">当前 kg</div>
          </div>
          <div className="text-center flex-1">
            <div className="font-bold text-lg text-danger">{weightDiff.toFixed(1)}</div>
            <div className="text-xs text-text-muted">需减 kg</div>
          </div>
          <div className="text-center flex-1">
            <div className="font-bold text-lg text-success">{settings.targetWeight}</div>
            <div className="text-xs text-text-muted">目标 kg</div>
          </div>
        </div>
      </div>

      {/* Deficit Card */}
      <div className="bg-danger/5 rounded-xl p-4 border border-danger/20">
        <div className="flex items-center gap-2 mb-2">
          <TrendingDown size={16} className="text-danger" />
          <span className="font-semibold text-danger">每日热量平衡</span>
        </div>
        <div className="grid grid-cols-2 gap-3 text-center">
          <div>
            <div className="text-lg font-bold">{tdee}</div>
            <div className="text-xs text-text-muted">TDEE 日常</div>
          </div>
          <div>
            <div className="text-lg font-bold text-secondary">+{exerciseBurn}</div>
            <div className="text-xs text-text-muted">跑步机额外</div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 text-center mt-2">
          <div>
            <div className="text-lg font-bold">{totalBurn}</div>
            <div className="text-xs text-text-muted">总消耗</div>
          </div>
          <div>
            <div className="text-lg font-bold text-danger">-{dailyDeficit}</div>
            <div className="text-xs text-text-muted">理论赤字</div>
          </div>
        </div>
        <div className="text-center mt-2 pt-2 border-t border-danger/10">
          <div className="text-lg font-bold text-success">净赤字 {netDeficit} kcal</div>
          <div className="text-xs text-text-muted">= 总消耗 {totalBurn} - 摄入 {settings.dailyCalorieTarget}</div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-surface rounded-xl p-4 text-center shadow-sm border border-border">
          <Flame size={20} className="text-danger mx-auto mb-1" />
          <div className="text-xl font-bold">{Math.round(weekCalories.reduce((a, b) => a + b, 0) / 7)}</div>
          <div className="text-xs text-text-muted">平均每日摄入</div>
        </div>
        <div className="bg-surface rounded-xl p-4 text-center shadow-sm border border-border">
          <Dumbbell size={20} className="text-secondary mx-auto mb-1" />
          <div className="text-xl font-bold">{Math.round(weekBurn.reduce((a, b) => a + b, 0) / 7)}</div>
          <div className="text-xs text-text-muted">平均每日运动消耗</div>
        </div>
      </div>

      {/* Workout Calendar */}
      <div className="bg-surface rounded-xl p-4 shadow-sm border border-border">
        <h3 className="font-semibold mb-3 flex items-center gap-2">
          <Dumbbell size={16} className="text-secondary" />
          本周跑步机计划
        </h3>
        <div className="space-y-2">
          {plan.weeklyWorkout.map((day, i) => {
            const isToday = i === (new Date().getDay() === 0 ? 6 : new Date().getDay() - 1);
            const burn = day.actions.reduce((s, a) => s + a.caloriesBurned, 0);
            return (
              <div
                key={i}
                className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-sm ${
                  isToday ? 'bg-secondary/10 border border-secondary/20' : 'bg-bg'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${burn > 0 ? 'bg-danger' : 'bg-text-muted'}`} />
                  <span className={isToday ? 'font-semibold' : ''}>{day.dayName}</span>
                </div>
                <div className="text-text-muted text-xs">
                  {burn > 0 ? `${burn} kcal` : '休息'}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Calorie Distribution */}
      <div className="bg-surface rounded-xl p-4 shadow-sm border border-border">
        <h3 className="font-semibold mb-3 flex items-center gap-2">
          <Flame size={16} className="text-danger" />
          本周摄入 vs 总消耗
        </h3>
        <div className="flex items-end gap-1 h-32">
          {plan.weeklyDiet.map((day, i) => {
            const intake = day.dailyCalories;
            const exerciseBurn = plan.weeklyWorkout[i].actions.reduce((s, a) => s + a.caloriesBurned, 0);
            const totalDayBurn = tdee + exerciseBurn; // 总消耗 = TDEE + 运动
            const maxVal = Math.max(...plan.weeklyDiet.map(d => d.dailyCalories), ...weekTotalBurn);
            const intakeHeight = maxVal > 0 ? (intake / maxVal) * 100 : 0;
            const burnHeight = maxVal > 0 ? (totalDayBurn / maxVal) * 100 : 0;
            const isToday = i === (new Date().getDay() === 0 ? 6 : new Date().getDay() - 1);
            const netDef = totalDayBurn - intake;
            return (
              <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
                <div className="text-[9px] text-success font-semibold">{netDef > 0 ? `-${netDef}` : `+${Math.abs(netDef)}`}</div>
                <div className="w-full flex gap-0.5 items-end" style={{ height: '80px' }}>
                  <div className={`flex-1 rounded-t-sm ${isToday ? 'bg-primary' : 'bg-primary/40'}`} style={{ height: `${intakeHeight}%` }} />
                  <div className={`flex-1 rounded-t-sm ${isToday ? 'bg-danger' : 'bg-danger/40'}`} style={{ height: `${burnHeight}%` }} />
                </div>
                <div className="text-[10px] text-text-muted">{day.dayName.slice(0, 2)}</div>
              </div>
            );
          })}
        </div>
        <div className="flex justify-center gap-4 mt-2 text-xs text-text-muted">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-primary" />摄入</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-danger" />总消耗（TDEE+运动）</span>
        </div>
      </div>
    </div>
  );
}
