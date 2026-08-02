import WorkbenchFrame from './WorkbenchFrame.vue'

export default {
  title: '布局/WorkbenchFrame 工作台外壳',
  component: WorkbenchFrame,
  tags: ['autodocs'],
  parameters: { layout: 'fullscreen', docs: { description: { component: 'PC 优先的工作台外壳，对应 Figma 首页 Frame 349:96，约束主内容宽度并保留导航、问候和页脚插槽。' } } },
}

export const Default = {
  render: () => ({
    components: { WorkbenchFrame },
    template: '<WorkbenchFrame><template #navigation><div style="padding:24px 42px">导航区域</div></template><template #greeting><div style="min-height:69px">问候区域</div></template><div style="height:321px;border:1px solid var(--ui-color-border);border-radius:22px;padding:20px">工作台内容</div><template #footer><div style="padding:24px 42px">页脚区域</div></template></WorkbenchFrame>',
  }),
}
