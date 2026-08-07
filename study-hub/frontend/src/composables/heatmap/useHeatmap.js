import { computed, ref } from 'vue'

export function toLocalDateKey(value = new Date()) {
  const date = value instanceof Date ? value : new Date(value)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const clone = (value) => JSON.parse(JSON.stringify(value))
const defaults = (style) => Object.fromEntries((style?.settings_schema?.fields || []).map((field) => [field.key, clone(field.default)]))

export function useHeatmap({ apiGet, apiPut = async () => ({}), now = () => new Date(), fixedRangeDays = null } = {}) {
  const catalog = ref(null); const data = ref(null); const styleId = ref('grid'); const settings = ref({}); const error = ref(''); const loading = ref(false); const saving = ref(false); const saved = ref('')
  const currentStyle = computed(() => catalog.value?.styles?.find((style) => style.id === styleId.value) || null)
  const schema = computed(() => currentStyle.value?.settings_schema || null)
  const dirty = computed(() => JSON.stringify({ style: styleId.value, settings: settings.value }) !== saved.value)
  const snapshot = () => { saved.value = JSON.stringify({ style: styleId.value, settings: settings.value }) }
  async function loadData() {
    const params = new URLSearchParams({ range_days: String(fixedRangeDays || settings.value.range_days || 196), sources: (settings.value.sources || []).join(','), metric: 'records', end_date: toLocalDateKey(now()), week_starts_on: String(settings.value.week_starts_on ?? 1) })
    data.value = await apiGet(`/heatmap/data?${params}`)
    return data.value
  }
  async function load() {
    loading.value = true; error.value = ''
    try {
      catalog.value = await apiGet('/heatmap/catalog')
      const available = catalog.value.styles.find((style) => style.status === 'available')
      const preference = await apiGet('/heatmap/preferences')
      styleId.value = preference.style_id === available.id ? preference.style_id : available.id
      settings.value = { ...defaults(available), ...(preference.settings || {}) }
      if (settings.value.cell_shape === 'square') settings.value.cell_radius = 0
      snapshot(); await loadData()
    } catch (cause) { error.value = cause?.message || '热力图数据加载失败'; data.value = null } finally { loading.value = false }
  }
  function update(partial) { settings.value = { ...settings.value, ...partial }; if (settings.value.cell_shape === 'square') settings.value.cell_radius = 0 }
  async function apply() { return loadData() }
  async function save() { saving.value = true; try { const response = await apiPut('/heatmap/preferences', { style_id: styleId.value, settings: settings.value }); settings.value = response.settings; snapshot(); return response } finally { saving.value = false } }
  function reset() { settings.value = defaults(currentStyle.value) }
  return { catalog, data, styleId, settings, schema, error, loading, saving, dirty, load, loadData, update, apply, save, reset }
}
