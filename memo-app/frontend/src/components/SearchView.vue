<template>
  <div class="search-view">
    <el-card shadow="never" class="search-card">
      <div class="search-bar">
        <el-input
          v-model="keyword"
          placeholder="搜索摘抄原文或个人想法..."
          clearable
          size="large"
          :prefix-icon="Search"
          @keyup.enter="doSearch"
          @clear="doSearch"
        >
          <template #append>
            <el-button type="primary" :icon="Search" :loading="loading" @click="doSearch">
              搜索
            </el-button>
          </template>
        </el-input>
      </div>

      <div class="search-filters">
        <div class="filter-row">
          <span class="filter-label">书籍：</span>
          <el-select
            v-model="bookId"
            clearable
            filterable
            placeholder="全部书籍"
            size="small"
            style="width: 220px"
            @change="doSearch"
          >
            <el-option
              v-for="b in books"
              :key="b.id"
              :label="b.title + (b.author ? ' — ' + b.author : '')"
              :value="b.id"
            />
          </el-select>
          <el-checkbox
            v-model="favoritesOnly"
            @change="doSearch"
            border
            size="small"
            style="margin-left: 12px"
          >
            <el-icon><StarFilled /></el-icon> 仅收藏
          </el-checkbox>
        </div>
      </div>

      <div v-if="tags.length" class="tag-filter">
        <span class="tag-filter-label">标签：</span>
        <el-checkbox-group v-model="selectedTagIds" @change="doSearch">
          <el-checkbox v-for="tag in tags" :key="tag.id" :value="tag.id" class="tag-checkbox">
            <el-tag :color="tag.color" effect="dark" size="small">{{ tag.name }}</el-tag>
          </el-checkbox>
        </el-checkbox-group>
        <el-button type="primary" link size="small" @click="tagManageVisible = true" style="margin-left: 8px">
          管理标签
        </el-button>
      </div>
    </el-card>

    <div v-if="!loading" class="result-summary">
      共找到 <strong>{{ total }}</strong> 条摘抄
      <span v-if="items.length" class="result-range">
        · 第 {{ (page - 1) * pageSize + 1 }}–{{ Math.min(page * pageSize, total) }} 条
      </span>
    </div>

    <div v-loading="loading" class="result-list">
      <el-empty v-if="!loading && items.length === 0" description="无匹配结果">
        <el-button type="primary" @click="clearFilters">清除筛选条件</el-button>
      </el-empty>

      <transition-group name="card-list" tag="div">
        <div v-for="item in items" :key="item.id" class="result-card">
          <!-- 书名 -->
          <div class="result-book" v-if="item.book">
            <el-icon><Reading /></el-icon>
            {{ item.book.title }}
            <span v-if="item.book.author" class="result-book-author">/ {{ item.book.author }}</span>
          </div>

          <!-- 摘抄原文 -->
          <div class="result-excerpt" v-if="item.content">
            <div class="result-label">摘抄</div>
            <div class="result-text" v-html="highlight(item.content)"></div>
          </div>

          <!-- 个人想法 -->
          <div class="result-insights" v-if="item.insights">
            <div class="result-label insights">想法</div>
            <div class="result-text-insights" v-html="highlight(item.insights)"></div>
          </div>

          <!-- 标签 -->
          <div v-if="item.tags.length" class="result-tags">
            <el-tag
              v-for="tag in item.tags"
              :key="tag.id"
              :color="tag.color"
              effect="dark"
              size="small"
              style="margin-right: 6px"
            >
              {{ tag.name }}
            </el-tag>
          </div>

          <!-- 链接 & 图片 -->
          <div v-if="item.links.length" class="result-links">
            <a v-for="(link, i) in item.links" :key="i" :href="link" target="_blank" rel="noopener noreferrer" class="result-link">
              <el-icon><Link /></el-icon> {{ truncate(link, 50) }}
            </a>
          </div>

          <div v-if="item.images.length" class="result-images">
            <el-image
              v-for="(img, i) in item.images"
              :key="i"
              :src="img"
              fit="cover"
              style="width: 60px; height: 60px; border-radius: 4px; margin-right: 4px; cursor: pointer"
              :preview-src-list="item.images"
              :initial-index="i"
            />
          </div>

          <div class="result-time">
            <el-button
              :type="item.is_favorite ? 'warning' : 'default'"
              :icon="item.is_favorite ? StarFilled : Star"
              text
              size="small"
              @click="handleToggleFavorite(item)"
            />
            {{ item.updated_at?.slice(0, 16)?.replace('T', ' ') }}
          </div>
        </div>
      </transition-group>

      <div v-if="total > pageSize" class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          background
          @current-change="doSearch"
        />
      </div>
    </div>

    <!-- 标签管理 -->
    <TagManager
      v-model="tagManageVisible"
      :tags="tags"
      @tag-added="onTagAdded"
      @tag-updated="onTagUpdated"
      @tag-deleted="onTagDeleted"
    />

    <el-backtop :right="24" :bottom="60" target=".app-container" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Reading, Link, Star, StarFilled } from '@element-plus/icons-vue'
import { getExcerpts, getTags, getBooks, toggleFavorite } from '../api/index.js'
import TagManager from './TagManager.vue'
import { truncate } from '../utils.js'

const loading = ref(false)
const keyword = ref('')
const selectedTagIds = ref([])
const tags = ref([])
const books = ref([])
const bookId = ref(null)
const favoritesOnly = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const tagManageVisible = ref(false)

async function fetchMeta() {
  try {
    const [tagRes, bookRes] = await Promise.all([getTags(), getBooks()])
    tags.value = tagRes.data
    books.value = bookRes.data
  } catch (e) {
    console.error('加载元数据失败', e)
  }
}

async function doSearch() {
  loading.value = true
  try {
    const params = {
      keyword: keyword.value,
      tag_ids: selectedTagIds.value.join(','),
      page: page.value,
      page_size: pageSize.value,
    }
    if (bookId.value) params.book_id = bookId.value
    if (favoritesOnly.value) params.favorites = true
    const { data } = await getExcerpts(params)
    items.value = data.items
    total.value = data.total
  } catch (e) {
    ElMessage.error('搜索失败')
  } finally {
    loading.value = false
  }
}

// Debounced search on keyword input
let debounceTimer = null
watch(keyword, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 1
    doSearch()
  }, 300)
})

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }
  return text.replace(/[&<>"']/g, (c) => map[c])
}

function highlight(text) {
  if (!text) return ''
  const escaped = escapeHtml(text)
  const kw = keyword.value.trim()
  if (!kw) return escaped
  const escapedKw = escapeHtml(kw)
  const regex = new RegExp(`(${escapedKw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return escaped.replace(regex, '<mark style="background:#ffeaa7;padding:0 2px;border-radius:2px">$1</mark>')
}

async function handleToggleFavorite(excerpt) {
  try {
    const { data } = await toggleFavorite(excerpt.id)
    excerpt.is_favorite = data.is_favorite
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

function clearFilters() {
  keyword.value = ''
  selectedTagIds.value = []
  bookId.value = null
  favoritesOnly.value = false
  page.value = 1
  doSearch()
}

function onTagAdded(newTag) {
  tags.value.push(newTag)
}

function onTagUpdated(updatedTag) {
  const idx = tags.value.findIndex((t) => t.id === updatedTag.id)
  if (idx >= 0) tags.value[idx] = updatedTag
}

function onTagDeleted(tagId) {
  tags.value = tags.value.filter((t) => t.id !== tagId)
  selectedTagIds.value = selectedTagIds.value.filter((id) => id !== tagId)
  doSearch()
}

function refresh() {
  page.value = 1
  fetchMeta()
  doSearch()
}

defineExpose({ refresh })
onMounted(() => {
  refresh()
})
</script>

<style scoped>
.search-card {
  margin-bottom: 16px;
}

.search-bar {
  margin-bottom: 12px;
}

.search-filters {
  margin-bottom: 10px;
}

.filter-row {
  display: flex;
  align-items: center;
}

.filter-label {
  font-size: 13px;
  color: #909399;
  margin-right: 4px;
  flex-shrink: 0;
}

.tag-filter {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 2px;
}

.tag-filter-label {
  font-size: 13px;
  color: #909399;
  margin-right: 4px;
}

.tag-checkbox {
  margin-right: 4px;
}

.tag-checkbox .el-checkbox__label {
  padding-left: 4px;
}

.result-summary {
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
}

.result-range {
  color: #b5a894;
}

.result-card {
  background: #fff;
  border-radius: 10px;
  padding: 16px 18px;
  margin-bottom: 12px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.05);
}

.result-book {
  font-size: 14px;
  font-weight: 600;
  color: #8b7e6e;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 10px;
}

.result-book-author {
  font-weight: 400;
  font-size: 12px;
  color: #b5a894;
}

.result-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  margin-bottom: 4px;
  color: #b8956a;
  text-transform: uppercase;
}

.result-label.insights {
  color: #6a8fbf;
  margin-top: 8px;
}

.result-text {
  font-size: 14px;
  color: #3d3226;
  line-height: 1.8;
  padding-left: 10px;
  border-left: 3px solid #e8d5b0;
  white-space: pre-wrap;
  word-break: break-word;
}

.result-text-insights {
  font-size: 13px;
  color: #556677;
  line-height: 1.7;
  padding-left: 10px;
  border-left: 3px solid #b8cce8;
  white-space: pre-wrap;
  word-break: break-word;
}

.result-tags {
  margin-top: 10px;
}

.result-links {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.result-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #8b7e6e;
  text-decoration: none;
}

.result-link:hover {
  color: #5c4a32;
  text-decoration: underline;
}

.result-images {
  margin-top: 8px;
  display: flex;
}

.result-time {
  margin-top: 10px;
  font-size: 11px;
  color: #c5b8a6;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.card-list-enter-active {
  transition: all 0.4s ease;
}

.card-list-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.card-list-leave-active {
  transition: all 0.3s ease;
  position: absolute;
}

.card-list-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

.card-list-move {
  transition: transform 0.3s ease;
}
</style>
