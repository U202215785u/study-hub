const board = (content) => `
  <section style="box-sizing:border-box;min-height:620px;padding:32px;background:var(--ui-color-canvas);color:var(--ui-color-text);font-family:var(--ui-font-sans)">
    ${content}
  </section>
`

const title = (name, description) => `
  <header style="max-width:820px;margin-bottom:28px">
    <h1 style="margin:0 0 10px;color:var(--ui-color-text-strong);font-size:30px;letter-spacing:0">${name}</h1>
    <p style="margin:0;color:var(--ui-color-text-muted);font-size:14px;line-height:1.7">${description}</p>
  </header>
`

export default {
  title: '设计语言/Study UI',
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Study Hub 首页实际使用的设计语言。所有示例直接读取语义 Token，不维护第二套视觉常量。',
      },
    },
  },
}

export const Overview = {
  name: '总览',
  render: () => ({
    template: board(`${title('Study UI', '安静、紧凑、工作导向的深色仪表盘语言。荧光绿只用于主要动作与当前状态，内容色和系统状态色保持独立。')}
      <div style="display:grid;max-width:920px;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px">
        <div v-for="(item,index) in levels" :key="item" style="display:grid;min-height:88px;place-items:center;border:1px solid var(--ui-color-border);border-radius:var(--ui-radius-md);padding:12px;background:var(--ui-color-surface);text-align:center">
          <strong style="color:var(--ui-color-text-strong);font-size:12px">{{ item }}</strong>
          <span v-if="index < levels.length - 1" style="color:var(--ui-color-action)">→</span>
        </div>
      </div>`),
    setup: () => ({ levels: ['Foundations', 'Atoms', 'Molecules', 'Organisms', 'Widgets', 'Pages'] }),
  }),
}

export const ColorsAndStatus = {
  name: '颜色与状态',
  render: () => ({
    template: board(`${title('颜色与状态', '中性色承担界面层级；内容分类色与成功、警告、错误等运行状态不能混用。')}
      <div style="display:grid;max-width:980px;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px">
        <article v-for="item in colors" :key="item.token" style="overflow:hidden;border:1px solid var(--ui-color-border);border-radius:var(--ui-radius-md);background:var(--ui-color-surface)">
          <div :style="{ height: '76px', background: 'var(' + item.token + ')' }" />
          <div style="display:grid;gap:4px;padding:12px"><strong style="color:var(--ui-color-text-strong);font-size:12px">{{ item.name }}</strong><code style="color:var(--ui-color-text-muted);font-size:10px">{{ item.token }}</code></div>
        </article>
      </div>`),
    setup: () => ({ colors: [
      { name: 'Canvas', token: '--ui-color-canvas' }, { name: 'Surface', token: '--ui-color-surface' },
      { name: 'Action', token: '--ui-color-action' }, { name: 'Text', token: '--ui-color-text-strong' },
      { name: 'Success', token: '--ui-color-success' }, { name: 'Warning', token: '--ui-color-warning' },
      { name: 'Danger', token: '--ui-color-danger' }, { name: 'Info', token: '--ui-color-info' },
    ] }),
  }),
}

export const TypographyAndDensity = {
  name: '字体与密度',
  render: () => ({
    template: board(`${title('字体与密度', '首页以固定层级和紧凑控制维持信息密度，字号不随视口宽度任意缩放。')}
      <div style="display:grid;max-width:820px;gap:18px">
        <div v-for="item in type" :key="item.name" style="display:grid;grid-template-columns:150px 1fr;align-items:baseline;border-bottom:1px solid var(--ui-color-border);padding-bottom:14px">
          <span style="color:var(--ui-color-text-muted);font-size:11px">{{ item.name }}</span>
          <strong :style="{color:'var(--ui-color-text-strong)',fontSize:item.size,fontWeight:item.weight}">Study Hub 学习工作台</strong>
        </div>
      </div>`),
    setup: () => ({ type: [
      { name: '页面标题 30', size: '30px', weight: 700 }, { name: '时间强调 28', size: '28px', weight: 700 },
      { name: '模块标题 18', size: '18px', weight: 700 }, { name: '正文 13', size: '13px', weight: 500 },
      { name: '辅助文字 10', size: '10px', weight: 500 },
    ] }),
  }),
}

export const SpacingAndRadius = {
  name: '间距与圆角',
  render: () => ({
    template: board(`${title('间距与圆角', '4px 间距阶梯服务于紧凑排布；16px 是模块卡片统一内容边距，22px 是模块卡片固定圆角。')}
      <div style="display:grid;max-width:900px;gap:22px">
        <div style="display:flex;align-items:end;gap:16px"><div v-for="space in spaces" :key="space" :style="{ width: 'var(--ui-space-' + space + ')', height: 'var(--ui-space-' + space + ')', minWidth: '4px', minHeight: '4px', background: 'var(--ui-color-action)' }" /><span style="color:var(--ui-color-text-muted);font-size:11px">space 1 / 2 / 3 / 4 / 6 / 8 / 12</span></div>
        <div style="display:flex;gap:16px"><div v-for="radius in radii" :key="radius" :style="{ width: '120px', height: '80px', border: '1px solid var(--ui-color-border-strong)', borderRadius: 'var(' + radius + ')', background: 'var(--ui-color-surface)' }" /></div>
      </div>`),
    setup: () => ({ spaces: ['1', '2', '3', '4', '6', '8', '12'], radii: ['--ui-radius-sm', '--ui-radius-md', '--ui-radius-lg', '--ui-radius-widget'] }),
  }),
}

export const ShadowAndMotion = {
  name: '阴影与动效',
  render: () => ({
    template: board(`${title('阴影与动效', '卡片阴影只建立信息层级，交互动效保持快速，并自动服从系统的减少动效设置。')}
      <div style="display:flex;max-width:760px;gap:24px">
        <article style="width:280px;height:160px;border:1px solid var(--ui-color-border);border-radius:var(--ui-radius-widget);padding:20px;background:var(--ui-color-surface);box-shadow:var(--ui-shadow-widget)"><strong>Widget shadow</strong><p style="color:var(--ui-color-text-muted)">常驻模块层级</p></article>
        <article style="width:280px;height:160px;border:1px solid var(--ui-color-border);border-radius:var(--ui-radius-lg);padding:20px;background:var(--ui-color-surface-raised);box-shadow:var(--ui-shadow-overlay)"><strong>Overlay shadow</strong><p style="color:var(--ui-color-text-muted)">对话框与抽屉层级</p></article>
      </div>
      <p style="margin-top:28px;color:var(--ui-color-text-muted);font-size:12px">fast 120ms · normal 180ms · slow 260ms · standard easing</p>`),
  }),
}
