import { useState, useEffect } from 'react';
import db from '@/db';
import type { UserSettings } from '@/types';
import { generatePlan, analyzeTargetFeasibility } from '@/utils/suggestions';
import { Save, User, Target, Sparkles, Flame, Clock } from 'lucide-react';

const USER_ID = 'user-1';

export default function SettingsPage() {
  const [settings, setSettings] = useState<Partial<UserSettings>>({
    gender: 'male',
    birthDate: '1995-01-01',
    height: 175,
    currentWeight: 80,
    targetWeight: 70,
    bodyFatPct: 15,
    activityLevel: 1.55,
    dailyCalorieTarget: 2000,
    dailyProteinTarget: 176,
    targetDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    treadmillMinutes: 60,
  });
  const [saved, setSaved] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [analysis, setAnalysis] = useState<ReturnType<typeof analyzeTargetFeasibility> | null>(null);

  useEffect(() => {
    db.userSettings.where('userId').equals(USER_ID).first().then((s) => {
      if (s) setSettings(s);
    });
  }, []);

  useEffect(() => {
    if (settings.currentWeight && settings.activityLevel && settings.birthDate && settings.height && settings.gender && settings.targetWeight && settings.targetDate) {
      const mock = { ...settings, userId: USER_ID } as UserSettings;
      const a = analyzeTargetFeasibility(mock);
      const protein = Math.round((settings.currentWeight || 0) * 2.2);
      setAnalysis(a);
      setSettings(prev => ({ ...prev, dailyCalorieTarget: a.dietTarget, dailyProteinTarget: protein }));
    }
  }, [settings.currentWeight, settings.activityLevel, settings.targetWeight, settings.targetDate, settings.gender, settings.birthDate, settings.height, settings.treadmillMinutes]);

  const handleSave = async () => {
    const data = { ...settings, userId: USER_ID, updatedAt: new Date().toISOString() } as UserSettings;
    const existing = await db.userSettings.where('userId').equals(USER_ID).first();
    if (existing?.id) {
      await db.userSettings.update(existing.id, data);
    } else {
      await db.userSettings.add({ ...data, createdAt: new Date().toISOString() });
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleGeneratePlan = async () => {
    setGenerating(true);
    const fullSettings = { ...settings, userId: USER_ID } as UserSettings;
    await handleSave();
    await db.foodItem.clear();
    const { seedDatabase } = await import('@/db/seed');
    await seedDatabase();
    const plan = await generatePlan(fullSettings);
    await db.generatedPlan.where('userId').equals(USER_ID).delete();
    await db.generatedPlan.add(plan);
    setGenerating(false);
    alert('计划已生成！');
  };

  const update = (field: keyof UserSettings, value: any) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold flex items-center gap-2">
        <User size={22} className="text-primary" />
        身体数据
      </h2>

      <div className="bg-surface rounded-xl p-4 space-y-4 shadow-sm border border-border">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-text-muted mb-1">性别</label>
            <select
              value={settings.gender}
              onChange={e => update('gender', e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-border bg-bg text-text focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="male">男</option>
              <option value="female">女</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-text-muted mb-1">出生日期</label>
            <input
              type="date"
              value={settings.birthDate}
              onChange={e => update('birthDate', e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-border bg-bg text-text focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-text-muted mb-1">身高 (cm)</label>
            <input
              type="number"
              value={settings.height}
              onChange={e => update('height', Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-border bg-bg text-text focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
          <div>
            <label className="block text-sm text-text-muted mb-1">体脂率 (%)</label>
            <input
              type="number"
              value={settings.bodyFatPct}
              onChange={e => update('bodyFatPct', Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-border bg-bg text-text focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-text-muted mb-1">当前体重 (kg)</label>
            <input
              type="number"
              step="0.1"
              value={settings.currentWeight}
              onChange={e => update('currentWeight', Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-border bg-bg text-text focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
          <div>
            <label className="block text-sm text-text-muted mb-1">目标体重 (kg)</label>
            <input
              type="number"
              step="0.1"
              value={settings.targetWeight}
              onChange={e => update('targetWeight', Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg border border-border bg-bg text-text focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
        </div>
      </div>

      <h2 className="text-xl font-bold flex items-center gap-2">
        <Target size={22} className="text-secondary" />
        目标设定
      </h2>

      <div className="bg-surface rounded-xl p-4 space-y-4 shadow-sm border border-border">
        <div>
          <label className="block text-sm text-text-muted mb-1">目标达成日期</label>
          <input
            type="date"
            value={settings.targetDate}
            onChange={e => update('targetDate', e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-border bg-bg text-text focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>

        <div>
          <label className="block text-sm text-text-muted mb-1">活动水平</label>
          <select
            value={settings.activityLevel}
            onChange={e => update('activityLevel', Number(e.target.value))}
            className="w-full px-3 py-2 rounded-lg border border-border bg-bg text-text focus:outline-none focus:ring-2 focus:ring-primary/50"
          >
            <option value={1.2}>久坐 (1.2)</option>
            <option value={1.375}>轻度活动 (1.375)</option>
            <option value={1.55}>中度活动 (1.55)</option>
            <option value={1.725}>高度活动 (1.725)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm text-text-muted mb-1 flex items-center gap-1">
            <Clock size={14} />
            每日跑步机时长 (分钟)
          </label>
          <input
            type="range"
            min="20"
            max="120"
            step="5"
            value={settings.treadmillMinutes}
            onChange={e => update('treadmillMinutes', Number(e.target.value))}
            className="w-full"
          />
          <div className="text-center text-sm font-semibold mt-1">{settings.treadmillMinutes} 分钟</div>
        </div>
      </div>

      {/* 极限模式计算预览 */}
      {analysis && (
        <div className={`rounded-xl p-4 border ${analysis.feasible ? 'bg-danger/5 border-danger/20' : 'bg-danger/10 border-danger/40'}`}>
          <h3 className={`font-semibold flex items-center gap-2 mb-3 ${analysis.feasible ? 'text-danger' : 'text-danger'}`}>
            <Flame size={16} />
            {analysis.feasible ? '极限模式计算结果' : '⚠️ 目标不可行'}
          </h3>

          {/* 不可行警告 */}
          {!analysis.feasible && (
            <div className="bg-danger text-white rounded-lg p-3 mb-3 text-sm">
              <div className="font-semibold mb-1">即使绝食也达不到目标</div>
              <div className="text-xs opacity-90">
                你的TDEE日常 {analysis.tdee} kcal，但理论赤字需要 {analysis.deficit} kcal。
                不运动的话每天只能赤字 {analysis.tdee} kcal，缺口 {analysis.deficit - analysis.tdee} kcal。
              </div>
              <div className="text-xs opacity-90 mt-1">
                需要跑步机至少 <span className="font-bold">{analysis.minMinutesNeeded} 分钟/天</span> 才能填补缺口。
              </div>
            </div>
          )}

          {/* 可行但极低警告 */}
          {analysis.feasible && analysis.dietTarget < analysis.safeMin && (
            <div className="bg-orange-500/10 border border-orange-500/30 text-orange-700 rounded-lg p-3 mb-3 text-sm">
              <div className="font-semibold">饮食目标极低（{analysis.dietTarget} kcal）</div>
              <div className="text-xs opacity-80">
                低于安全线 {analysis.safeMin} kcal，执行难度极高。建议延长截止日期或增加运动。
              </div>
            </div>
          )}

          <div className="grid grid-cols-3 gap-3 text-center">
            <div>
              <div className="text-lg font-bold">{analysis.tdee}</div>
              <div className="text-xs text-text-muted">TDEE 日常</div>
            </div>
            <div>
              <div className="text-lg font-bold text-secondary">+{analysis.exerciseBurn}</div>
              <div className="text-xs text-text-muted">跑步机额外</div>
            </div>
            <div>
              <div className="text-lg font-bold">{analysis.totalBurn}</div>
              <div className="text-xs text-text-muted">总消耗</div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3 text-center mt-3">
            <div>
              <div className="text-lg font-bold text-danger">-{analysis.deficit}</div>
              <div className="text-xs text-text-muted">理论赤字</div>
              <div className="text-[10px] text-text-muted/60">{analysis.daysUntilTarget}天减{(settings.currentWeight! - settings.targetWeight!).toFixed(1)}kg</div>
            </div>
            <div>
              <div className={`text-lg font-bold ${analysis.feasible ? 'text-success' : 'text-danger'}`}>
                {analysis.feasible ? analysis.dietTarget : '不可能'}
              </div>
              <div className="text-xs text-text-muted">饮食目标</div>
              <div className="text-[10px] text-text-muted/60">= 总消耗 - 理论赤字</div>
            </div>
            <div>
              <div className="text-lg font-bold text-danger">-{analysis.netDeficit}</div>
              <div className="text-xs text-text-muted">净赤字</div>
              <div className="text-[10px] text-text-muted/60">每天实际缺口</div>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-danger/10">
            <div className="text-sm text-center">
              <span className="text-text-muted">{analysis.daysUntilTarget}天预期减重: </span>
              <span className="font-bold text-danger">{analysis.actualWeightLoss.toFixed(1)} kg</span>
              {Math.abs(analysis.actualWeightLoss - (settings.currentWeight! - settings.targetWeight!)) > 0.5 && (
                <span className="text-xs text-text-muted ml-1">
                  (目标 {(settings.currentWeight! - settings.targetWeight!).toFixed(1)}kg，
                  缺口 {((settings.currentWeight! - settings.targetWeight!) - analysis.actualWeightLoss).toFixed(1)}kg)
                </span>
              )}
            </div>
          </div>

          <div className="mt-2 text-[10px] text-text-muted/70 leading-relaxed">
            饮食目标 = 总消耗({analysis.totalBurn}) - 理论赤字({analysis.deficit}) = {analysis.dietTarget}。
            {!analysis.feasible
              ? `当前运动不够，至少需${analysis.minMinutesNeeded}分钟才能为正。`
              : `执行此计划${analysis.daysUntilTarget}天可减${analysis.actualWeightLoss.toFixed(1)}kg。`
            }
          </div>
        </div>
      )}

      <button
        onClick={handleSave}
        className="w-full py-3 bg-primary text-white rounded-xl font-semibold flex items-center justify-center gap-2"
      >
        <Save size={18} />
        {saved ? '已保存!' : '保存设置'}
      </button>

      <button
        onClick={handleGeneratePlan}
        disabled={generating}
        className="w-full py-3 bg-danger text-white rounded-xl font-semibold flex items-center justify-center gap-2 disabled:opacity-60"
      >
        <Sparkles size={18} />
        {generating ? '生成中...' : '生成极限计划'}
      </button>
    </div>
  );
}
