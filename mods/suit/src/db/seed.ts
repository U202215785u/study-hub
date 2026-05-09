import db from './index';
import type { FoodItem } from '@/types';

// 老乡鸡真实菜品数据（每份热量）
// 来源：老乡鸡官方公开数据 + 薄荷健康 + 大众点评实测 + FatSecret
const laoxiangjiFoods: Omit<FoodItem, 'id'>[] = [
  // === 荤菜 ===
  // 卤鸡腿: FatSecret官方 1份(65g)=129kcal 蛋白质14g 脂肪7g 碳水2g
  { name: '卤鸡腿', caloriesPerServing: 129, proteinPerServing: 14.0, carbsPerServing: 2.0, fatPerServing: 7.0, category: '荤菜', source: '老乡鸡官方/FatSecret' },
  // 葱油鸡: 大众点评实测 366kcal/份（约190g熟鸡）
  { name: '葱油鸡', caloriesPerServing: 366, proteinPerServing: 24.0, carbsPerServing: 3.0, fatPerServing: 26.0, category: '荤菜', source: '大众点评实测' },
  // 豉汁鱼块: 100g=121kcal, 一份约200g
  { name: '豉汁鱼块', caloriesPerServing: 242, proteinPerServing: 25.4, carbsPerServing: 2.4, fatPerServing: 14.6, category: '荤菜', source: 'FatSecret推算' },
  // 香菇滑鸡: 100g≈89kcal, 一份约200g
  { name: '香菇滑鸡', caloriesPerServing: 178, proteinPerServing: 24.0, carbsPerServing: 4.0, fatPerServing: 6.0, category: '荤菜', source: '推算' },
  // 金秋板栗烧鸡: 大众点评实测 400kcal/份
  { name: '金秋板栗烧鸡', caloriesPerServing: 400, proteinPerServing: 22.0, carbsPerServing: 35.0, fatPerServing: 18.0, category: '荤菜', source: '大众点评实测' },
  // 毛豆烧土鸡: 老乡鸡官方"66健康节"公开 443kcal/份
  { name: '毛豆烧土鸡', caloriesPerServing: 443, proteinPerServing: 26.0, carbsPerServing: 38.0, fatPerServing: 20.0, category: '荤菜', source: '老乡鸡官方' },
  // 金汤酸菜鱼: 大众点评实测 270kcal/份
  { name: '金汤酸菜鱼', caloriesPerServing: 270, proteinPerServing: 32.0, carbsPerServing: 12.0, fatPerServing: 10.0, category: '荤菜', source: '大众点评实测' },
  // 肉饼蒸蛋: 大众点评实测 226kcal/份
  { name: '肉饼蒸蛋', caloriesPerServing: 226, proteinPerServing: 16.0, carbsPerServing: 12.0, fatPerServing: 12.0, category: '荤菜', source: '大众点评实测' },
  // 农家小炒肉: 100g=187kcal, 一份约150g
  { name: '农家小炒肉', caloriesPerServing: 280, proteinPerServing: 15.0, carbsPerServing: 8.0, fatPerServing: 20.0, category: '荤菜', source: '推算' },
  // 清蒸小黄鱼: 大众点评实测 417kcal/份
  { name: '清蒸小黄鱼', caloriesPerServing: 417, proteinPerServing: 28.0, carbsPerServing: 5.0, fatPerServing: 28.0, category: '荤菜', source: '大众点评实测' },
  // 蒜蓉粉丝虾: 大众点评实测 213kcal/份
  { name: '蒜蓉粉丝虾', caloriesPerServing: 213, proteinPerServing: 18.0, carbsPerServing: 18.0, fatPerServing: 8.0, category: '荤菜', source: '大众点评实测' },
  // 香辣血旺: 大众点评实测 160kcal/份
  { name: '香辣血旺', caloriesPerServing: 160, proteinPerServing: 8.0, carbsPerServing: 8.0, fatPerServing: 10.0, category: '荤菜', source: '大众点评实测' },

  // === 素菜 ===
  // 葱油菜苔: 老乡鸡官方 141kcal/份
  { name: '葱油菜苔', caloriesPerServing: 141, proteinPerServing: 3.5, carbsPerServing: 6.0, fatPerServing: 9.0, category: '素菜', source: '老乡鸡官方' },
  // 农家蒸蛋: 老乡鸡官方 68kcal/份
  { name: '农家蒸蛋', caloriesPerServing: 68, proteinPerServing: 5.0, carbsPerServing: 3.0, fatPerServing: 4.0, category: '素菜', source: '老乡鸡官方' },
  // 蒸嫩豆腐: 100g=112kcal, 一份约150g
  { name: '蒸嫩豆腐', caloriesPerServing: 168, proteinPerServing: 10.8, carbsPerServing: 15.8, fatPerServing: 6.8, category: '素菜', source: '推算' },
  // 蒜香蒸茄子: 100g=70kcal, 一份约150g
  { name: '蒜香蒸茄子', caloriesPerServing: 105, proteinPerServing: 3.0, carbsPerServing: 12.0, fatPerServing: 4.5, category: '素菜', source: '推算' },
  // 青椒炒豆芽: 100g=45kcal, 一份约150g
  { name: '青椒炒豆芽', caloriesPerServing: 68, proteinPerServing: 4.5, carbsPerServing: 7.5, fatPerServing: 2.3, category: '素菜', source: '推算' },
  // 鸡汁娃娃菜: 100g=55kcal, 一份约150g
  { name: '鸡汁娃娃菜', caloriesPerServing: 83, proteinPerServing: 3.0, carbsPerServing: 9.0, fatPerServing: 3.0, category: '素菜', source: '推算' },
  // 青椒土豆丝: 100g=95kcal, 一份约150g
  { name: '青椒土豆丝', caloriesPerServing: 143, proteinPerServing: 3.0, carbsPerServing: 21.0, fatPerServing: 5.3, category: '素菜', source: '推算' },
  // 红烧茄子: 100g=120kcal, 一份约150g
  { name: '红烧茄子', caloriesPerServing: 180, proteinPerServing: 3.0, carbsPerServing: 21.0, fatPerServing: 9.0, category: '素菜', source: '推算' },
  // 西红柿炒鸡蛋: 100g=110kcal, 一份约150g
  { name: '西红柿炒鸡蛋', caloriesPerServing: 165, proteinPerServing: 7.5, carbsPerServing: 9.0, fatPerServing: 10.5, category: '素菜', source: '推算' },

  // === 主食 ===
  // 白米饭: 百度健康 200g≈230kcal
  { name: '白米饭', caloriesPerServing: 230, proteinPerServing: 5.2, carbsPerServing: 51.8, fatPerServing: 0.6, category: '主食', source: '百度健康' },
  // 三黑元气饭: FatSecret官方 1份=508kcal
  { name: '三黑元气饭', caloriesPerServing: 508, proteinPerServing: 9.0, carbsPerServing: 111.0, fatPerServing: 3.0, category: '主食', source: 'FatSecret官方' },
  // 杂粮饭: 百度健康 200g≈220kcal
  { name: '杂粮饭', caloriesPerServing: 220, proteinPerServing: 5.0, carbsPerServing: 48.0, fatPerServing: 1.0, category: '主食', source: '百度健康' },
  // 鸡汤魔芋面: 100g=17kcal, 一份约300g
  { name: '鸡汤魔芋面', caloriesPerServing: 51, proteinPerServing: 3.0, carbsPerServing: 9.0, fatPerServing: 0, category: '主食', source: '推算' },
];

export async function seedDatabase() {
  const count = await db.foodItem.count();
  if (count === 0) {
    await db.foodItem.bulkAdd(laoxiangjiFoods as any);
  }
}
