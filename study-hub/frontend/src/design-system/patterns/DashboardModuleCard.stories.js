import DashboardModuleCard from './DashboardModuleCard.vue'
import { ref } from 'vue'

export default {
  title: '数据展示/DashboardModuleCard 模块卡片',
  component: DashboardModuleCard,
  tags: ['autodocs'],
  args: { title: '模块标题' },
  parameters: { docs: { description: { component: '首页九个业务组件共享的固定边界和状态优先级，对应 Figma Frame 349:96。' } } },
  decorators: [() => ({ template: '<div style="width:331px;height:321px"><story /></div>' })],
}

export const Default = { render: (args) => ({ components: { DashboardModuleCard }, setup: () => ({ args }), template: '<DashboardModuleCard v-bind="args"><div>模块内容</div></DashboardModuleCard>' }) }
export const Loading = { args: { loading: true } }
export const Empty = { args: { empty: true, emptyText: '暂无真实数据' } }
export const Error = { args: { error: '加载失败' } }
export const InteractiveStates = {
  render: () => ({
    components: { DashboardModuleCard },
    setup() {
      const state = ref('loading')
      const states = ['loading', 'error', 'empty', 'content']
      return { state, states }
    },
    template: '<div><div style="display:flex;gap:8px;margin-bottom:12px"><button v-for="item in states" :key="item" type="button" @click="state = item">{{ item }}</button></div><DashboardModuleCard title="交互状态" :loading="state === \'loading\'" :error="state === \'error\' ? \'加载失败\' : \'\'" :empty="state === \'empty\'"><div>模块内容</div></DashboardModuleCard></div>',
  }),
}
