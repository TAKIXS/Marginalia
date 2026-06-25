<template>
  <div class="app-container" :class="{ 'dark-mode': isDark }">
    <header class="app-header">
      <div class="header-top">
        <el-button
          circle
          text
          size="small"
          @click="toggleDark"
          class="dark-toggle"
          :title="isDark ? '切换到亮色模式' : '切换到暗色模式'"
        >
          <el-icon :size="18">
            <Sunny v-if="isDark" />
            <Moon v-else />
          </el-icon>
        </el-button>
        <div>
          <h1>读书摘抄</h1>
          <span class="app-subtitle">记录原文 · 写下见解 · 标签检索</span>
        </div>
        <div style="width: 32px"></div>
      </div>
    </header>

    <el-tabs v-model="activeTab" class="main-tabs">
      <el-tab-pane label="书架" name="shelf">
        <BookList ref="bookListRef" />
      </el-tab-pane>
      <el-tab-pane label="检索" name="search">
        <SearchView ref="searchViewRef" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { Sunny, Moon } from '@element-plus/icons-vue'
import BookList from './components/BookList.vue'
import SearchView from './components/SearchView.vue'

const activeTab = ref('shelf')
const bookListRef = ref(null)
const searchViewRef = ref(null)
const isDark = ref(false)

watch(activeTab, (tab) => {
  if (tab === 'shelf') bookListRef.value?.refresh()
  if (tab === 'search') searchViewRef.value?.refresh()
})

function toggleDark() {
  isDark.value = !isDark.value
  localStorage.setItem('dark-mode', isDark.value ? '1' : '0')
}

// Ctrl+K: jump to search
function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    activeTab.value = 'search'
  }
}

onMounted(() => {
  isDark.value = localStorage.getItem('dark-mode') === '1'
  window.addEventListener('keydown', onKeydown)
})
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', Arial, sans-serif;
  background: #f5f0eb;
  color: #3d3226;
}

.app-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 16px 80px;
}

.header-top {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 4px;
}

.dark-toggle {
  flex-shrink: 0;
}

.app-header {
  text-align: center;
  margin-bottom: 20px;
}

.app-header h1 {
  font-size: 26px;
  font-weight: 700;
  color: #3d3226;
  letter-spacing: 4px;
}

.app-subtitle {
  font-size: 13px;
  color: #a0917e;
  letter-spacing: 2px;
}

.main-tabs > .el-tabs__header {
  background: #fff;
  border-radius: 10px;
  padding: 0 16px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.05);
}

.main-tabs > .el-tabs__header .el-tabs__nav-wrap::after {
  display: none;
}

.main-tabs > .el-tabs__header .el-tabs__item {
  font-size: 15px;
  font-weight: 500;
  height: 46px;
  line-height: 46px;
  color: #8b7e6e;
}

.main-tabs > .el-tabs__header .el-tabs__item.is-active {
  color: #5c4a32;
}

.main-tabs > .el-tabs__content {
  margin-top: 12px;
}

/* ── Dark Mode ──────────────────────────── */
.dark-mode body,
.app-container.dark-mode {
  background: #1a1a2e;
  color: #e0d7c8;
}

.dark-mode .app-header h1 {
  color: #e0d7c8;
}

.dark-mode .app-subtitle {
  color: #8b7e6e;
}

.dark-mode .main-tabs > .el-tabs__header {
  background: #252536;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.3);
}

.dark-mode .main-tabs > .el-tabs__header .el-tabs__item {
  color: #8b7e6e;
}

.dark-mode .main-tabs > .el-tabs__header .el-tabs__item.is-active {
  color: #d4b896;
}

.dark-mode .book-group,
.dark-mode .result-card,
.dark-mode .search-card .el-card,
.dark-mode .el-card {
  background: #252536 !important;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.3);
  border-color: #333;
}

.dark-mode .book-header:hover {
  background: #2a2a3d !important;
}

.dark-mode .book-excerpts {
  background: #1e1e30;
  border-top-color: #333;
}

.dark-mode .book-title {
  color: #e0d7c8;
}

.dark-mode .book-author {
  color: #8b7e6e;
}

.dark-mode .excerpt-text {
  color: #ccc;
  border-left-color: #6a5a3a;
}

.dark-mode .insights-text {
  color: #aabbcc;
  border-left-color: #4a6080;
}

.dark-mode .excerpt-card {
  border-bottom-color: #333;
}

.dark-mode .excerpt-time {
  color: #6a6a7a;
}

.dark-mode .excerpt-label {
  color: #b8956a;
}

.dark-mode .insights-label {
  color: #6a8fbf;
}

.dark-mode .el-empty__description {
  color: #8b7e6e;
}

.dark-mode input,
.dark-mode textarea,
.dark-mode .el-input__inner,
.dark-mode .el-input__wrapper,
.dark-mode .el-textarea__inner,
.dark-mode .el-select .el-input__wrapper {
  background: #333344 !important;
  color: #e0d7c8 !important;
  border-color: #444 !important;
}

.dark-mode .el-select-dropdown,
.dark-mode .el-picker-panel,
.dark-mode .el-dialog,
.dark-mode .el-popper {
  background: #252536 !important;
  color: #e0d7c8 !important;
}

.dark-mode .el-select-dropdown__item {
  color: #e0d7c8 !important;
}

.dark-mode .el-select-dropdown__item.hover,
.dark-mode .el-select-dropdown__item:hover {
  background: #333344 !important;
}

.dark-mode .el-pagination button,
.dark-mode .el-pager li {
  background: #333344 !important;
  color: #e0d7c8 !important;
}

.dark-mode .el-pager li.active {
  background: #5c4a32 !important;
}

.dark-mode .el-dialog {
  background: #252536 !important;
}

.dark-mode .el-form-item__label {
  color: #b5a894 !important;
}

.dark-mode .result-book {
  color: #b5a894;
}

.dark-mode .result-link {
  color: #8b7e6e;
}

.dark-mode .random-card {
  background: linear-gradient(135deg, #2a2a15, #2a2520);
  box-shadow: 0 2px 12px rgba(255, 152, 0, 0.08);
}

.dark-mode .random-content {
  color: #e0d7c8;
}

.dark-mode .random-badge {
  color: #ffb74d;
}

/* Responsive */
@media (max-width: 600px) {
  .app-container {
    padding: 12px 8px 60px;
  }

  .excerpt-row {
    flex-direction: column;
  }

  .tags-col {
    max-width: none !important;
  }
}
</style>
