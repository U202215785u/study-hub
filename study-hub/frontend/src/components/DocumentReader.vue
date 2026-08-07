<template>
  <div class="document-reader">
    <div class="document-reader__tabs" role="tablist" aria-label="文档内容">
      <button
        type="button"
        role="tab"
        :aria-selected="activeTab === 'summary'"
        :tabindex="activeTab === 'summary' ? 0 : -1"
        @click="selectTab('summary')"
        @keydown.right.prevent="selectTab('tutorial')"
      >
        总结
      </button>
      <button
        v-if="showTutorialTab"
        type="button"
        role="tab"
        :aria-selected="activeTab === 'tutorial'"
        :tabindex="activeTab === 'tutorial' ? 0 : -1"
        @click="selectTab('tutorial')"
        @keydown.left.prevent="selectTab('summary')"
      >
        图文教程
      </button>
    </div>

    <section role="tabpanel" :aria-label="activeTab === 'summary' ? '总结' : '图文教程'">
      <MarkdownRenderer v-if="activeTab === 'summary'" :content="summaryMarkdown" />
      <div v-else class="tutorial-content">
        <MarkdownRenderer v-if="tutorialStatus === 'ready'" :content="tutorialMarkdown" />
        <p v-else class="document-reader__notice" role="status">{{ tutorialReason || defaultTutorialReason }}</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import MarkdownRenderer from './MarkdownRenderer.vue'

const props = defineProps({
  summaryMarkdown: { type: String, default: '' },
  tutorialMarkdown: { type: String, default: '' },
  tutorialStatus: { type: String, default: 'not_requested' },
  tutorialReason: { type: String, default: '' },
})

const emit = defineEmits(['active-content'])
const activeTab = ref('summary')
const showTutorialTab = computed(() => props.tutorialStatus !== 'not_requested')
const defaultTutorialReason = computed(() => props.tutorialStatus === 'failed' ? '图文教程生成失败' : '图文教程暂不可用')

function currentContent(tab = activeTab.value) {
  return tab === 'tutorial' ? props.tutorialMarkdown : props.summaryMarkdown
}

function selectTab(tab) {
  if (tab === 'tutorial' && !showTutorialTab.value) return
  activeTab.value = tab
  emit('active-content', currentContent(tab))
}

watch(() => [props.summaryMarkdown, props.tutorialMarkdown, props.tutorialStatus], () => {
  activeTab.value = 'summary'
  emit('active-content', props.summaryMarkdown)
}, { immediate: true })
</script>
