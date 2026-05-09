import { describe, it, expect } from 'vitest'
import type { UserSettings } from '@/types'
import {
  calculateAge,
  calculateBMR,
  calculateTDEE,
  calculateExerciseBurn,
  calculateTotalBurn,
  calculateDailyDeficit,
  calculateDailyCalorieTarget,
  analyzeTargetFeasibility,
} from './suggestions'

function makeSettings(overrides: Partial<UserSettings> = {}): UserSettings {
  const base: UserSettings = {
    userId: 'test-user',
    gender: 'male',
    birthDate: '1995-01-01',
    height: 175,
    currentWeight: 80,
    targetWeight: 70,
    activityLevel: 1.55,
    targetDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    treadmillMinutes: 60,
    dailyCalorieTarget: 0,
    dailyProteinTarget: 0,
  }
  return { ...base, ...overrides }
}

describe('calculateAge', () => {
  it('computes age for 30-year-old', () => {
    const birth = new Date()
    birth.setFullYear(birth.getFullYear() - 30)
    const age = calculateAge(birth.toISOString().split('T')[0])
    expect(age).toBe(30)
  })

  it('subtracts 1 year when birthday has not occurred yet', () => {
    const today = new Date()
    const birthDate = `${today.getFullYear() - 25}-${String(today.getMonth() + 2).padStart(2, '0')}-01`
    const age = calculateAge(birthDate)
    expect(age).toBe(24)
  })
})

describe('calculateBMR', () => {
  it('male formula: 10w + 6.25h - 5a + 5', () => {
    const s = makeSettings({ gender: 'male', birthDate: '1995-06-01', height: 175, currentWeight: 80 })
    const age = calculateAge(s.birthDate)
    const expected = 10 * 80 + 6.25 * 175 - 5 * age + 5
    expect(calculateBMR(s)).toBe(expected)
  })

  it('female formula: 10w + 6.25h - 5a - 161', () => {
    const s = makeSettings({ gender: 'female', birthDate: '1995-06-01', height: 165, currentWeight: 60 })
    const age = calculateAge(s.birthDate)
    const expected = 10 * 60 + 6.25 * 165 - 5 * age - 161
    expect(calculateBMR(s)).toBe(expected)
  })

  it('female BMR is lower than male with same height/weight', () => {
    const male = makeSettings({ gender: 'male', birthDate: '1995-01-01', height: 170, currentWeight: 70 })
    const female = makeSettings({ gender: 'female', birthDate: '1995-01-01', height: 170, currentWeight: 70 })
    expect(calculateBMR(female)).toBeLessThan(calculateBMR(male))
  })
})

describe('calculateTDEE', () => {
  it('TDEE = round(BMR * activityLevel)', () => {
    const s = makeSettings({ activityLevel: 1.55 })
    const bmr = calculateBMR(s)
    expect(calculateTDEE(s)).toBe(Math.round(bmr * 1.55))
  })

  it('sedentary (1.2) TDEE is lower than highly active (1.725)', () => {
    const sedentary = makeSettings({ activityLevel: 1.2 })
    const active = makeSettings({ activityLevel: 1.725 })
    expect(calculateTDEE(sedentary)).toBeLessThan(calculateTDEE(active))
  })
})

describe('calculateExerciseBurn', () => {
  it('60min * 80kg = round(10 * 80 * 1) = 800', () => {
    const s = makeSettings({ currentWeight: 80, treadmillMinutes: 60 })
    expect(calculateExerciseBurn(s)).toBe(800)
  })

  it('30min * 80kg = round(10 * 80 * 0.5) = 400', () => {
    const s = makeSettings({ currentWeight: 80, treadmillMinutes: 30 })
    expect(calculateExerciseBurn(s)).toBe(400)
  })

  it('60min * 60kg = round(10 * 60 * 1) = 600', () => {
    const s = makeSettings({ currentWeight: 60, treadmillMinutes: 60 })
    expect(calculateExerciseBurn(s)).toBe(600)
  })

  it('heavier weight burns more at same duration', () => {
    const light = makeSettings({ currentWeight: 60, treadmillMinutes: 60 })
    const heavy = makeSettings({ currentWeight: 90, treadmillMinutes: 60 })
    expect(calculateExerciseBurn(heavy)).toBeGreaterThan(calculateExerciseBurn(light))
  })

  it('longer duration burns more at same weight', () => {
    const short = makeSettings({ currentWeight: 80, treadmillMinutes: 30 })
    const long = makeSettings({ currentWeight: 80, treadmillMinutes: 90 })
    expect(calculateExerciseBurn(long)).toBeGreaterThan(calculateExerciseBurn(short))
  })
})

describe('calculateTotalBurn', () => {
  it('total burn = TDEE + exercise burn', () => {
    const s = makeSettings()
    expect(calculateTotalBurn(s)).toBe(calculateTDEE(s) + calculateExerciseBurn(s))
  })
})

describe('calculateDailyDeficit', () => {
  it('30 days to lose 10kg = round(10 * 7700 / 30) = 2567', () => {
    const s = makeSettings({ currentWeight: 80, targetWeight: 70, targetDate: daysFromNow(30) })
    const result = calculateDailyDeficit(s)
    expect(result.deficit).toBe(2567)
    expect(result.daysUntilTarget).toBe(30)
  })

  it('60 days to lose 10kg = round(77000 / 60) = 1283', () => {
    const s = makeSettings({ currentWeight: 80, targetWeight: 70, targetDate: daysFromNow(60) })
    const result = calculateDailyDeficit(s)
    expect(result.deficit).toBe(1283)
  })

  it('returns 0 deficit when target is above current weight', () => {
    const s = makeSettings({ currentWeight: 70, targetWeight: 80 })
    const result = calculateDailyDeficit(s)
    expect(result.deficit).toBe(0)
  })

  it('returns at least 1 day for expired targets', () => {
    const s = makeSettings({ targetDate: daysFromNow(-5) })
    const result = calculateDailyDeficit(s)
    expect(result.daysUntilTarget).toBe(1)
  })
})

describe('calculateDailyCalorieTarget', () => {
  it('diet target = total burn - theoretical deficit', () => {
    const s = makeSettings()
    const totalBurn = calculateTotalBurn(s)
    const { deficit } = calculateDailyDeficit(s)
    expect(calculateDailyCalorieTarget(s)).toBe(totalBurn - deficit)
  })

  it('more exercise allows higher diet target', () => {
    const lowExercise = makeSettings({ treadmillMinutes: 30 })
    const highExercise = makeSettings({ treadmillMinutes: 90 })
    expect(calculateDailyCalorieTarget(highExercise)).toBeGreaterThan(calculateDailyCalorieTarget(lowExercise))
  })

  it('longer deadline increases diet target (lower deficit)', () => {
    const short = makeSettings({ targetDate: daysFromNow(30) })
    const long = makeSettings({ targetDate: daysFromNow(60) })
    expect(calculateDailyCalorieTarget(long)).toBeGreaterThan(calculateDailyCalorieTarget(short))
  })
})

describe('analyzeTargetFeasibility', () => {
  it('feasible: enough exercise, positive diet target', () => {
    const s = makeSettings({ currentWeight: 80, targetWeight: 70, targetDate: daysFromNow(30), treadmillMinutes: 60 })
    const a = analyzeTargetFeasibility(s)
    expect(a.feasible).toBe(true)
    expect(a.dietTarget).toBeGreaterThanOrEqual(0)
    expect(a.netDeficit).toBe(a.deficit)
  })

  it('infeasible: TDEE < deficit, impossible even with zero intake', () => {
    // 80kg -> 60kg (lose 20kg), 30 days, 0 exercise: deficit=5133, TDEE ~2703
    const s = makeSettings({ currentWeight: 80, targetWeight: 60, targetDate: daysFromNow(30), treadmillMinutes: 0 })
    const a = analyzeTargetFeasibility(s)
    expect(a.feasible).toBe(false)
    expect(a.dietTarget).toBeLessThan(0)
    expect(a.minMinutesNeeded).toBeGreaterThan(0)
    // Even fasting can only deficit TDEE, cannot lose 20kg
    expect(a.actualWeightLoss).toBeLessThan(20)
  })

  it('actual weight loss equals target when feasible', () => {
    const s = makeSettings({ currentWeight: 80, targetWeight: 70, targetDate: daysFromNow(30), treadmillMinutes: 60 })
    const a = analyzeTargetFeasibility(s)
    expect(a.actualWeightLoss).toBeCloseTo(10, 0)
  })

  it('safeMin reference = BMR * 0.6', () => {
    const s = makeSettings()
    const a = analyzeTargetFeasibility(s)
    const bmr = calculateBMR(s)
    expect(a.safeMin).toBe(Math.round(bmr * 0.6))
  })
})

function daysFromNow(days: number): string {
  return new Date(Date.now() + days * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
}
