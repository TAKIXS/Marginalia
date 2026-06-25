<template>
  <div class="book-list" v-loading="loading">
    <!-- 随机摘抄卡片 -->
    <div v-if="randomExcerpt" class="random-card" @click="randomExcerpt = null">
      <div class="random-header">
        <span class="random-badge">📖 今日摘抄</span>
        <el-button :icon="Refresh" text size="small" @click.stop="fetchRandom">换一条</el-button>
      </div>
      <div class="random-content">{{ randomExcerpt.content }}</div>
      <div class="random-meta">
        <span v-if="randomExcerpt.book">{{ randomExcerpt.book.title }}</span>
        <span v-if="randomExcerpt.insights" class="random-insights">{{ randomExcerpt.insights }}</span>
      </div>
    </div>

    <!-- 顶部操作栏 -->
    <div class="shelf-toolbar">
      <div class="shelf-add-btn" @click="bookDialogVisible = true">
        <el-icon :size="20"><Plus /></el-icon>
      </div>
      <el-button text size="small" @click="handleExport" :loading="exporting">
        <el-icon><Download /></el-icon> 导出
      </el-button>
    </div>

    <el-empty v-if="!loading && groups.length === 0" description="书架空空如也">
      <template #extra>
        <el-button type="primary" @click="bookDialogVisible = true">
          <el-icon><Plus /></el-icon> 添加第一本书
        </el-button>
      </template>
    </el-empty>

    <div v-for="group in groups" :key="group.book.id" class="book-group">
      <!-- 书名头部（可折叠） -->
      <div class="book-header" @click="toggleBook(group.book.id)">
        <div class="book-header-left">
          <el-icon class="collapse-icon" :class="{ expanded: isExpanded(group.book.id) }">
            <ArrowRight />
          </el-icon>
          <span class="book-title">{{ group.book.title }}</span>
          <span v-if="group.book.author" class="book-author">— {{ group.book.author }}</span>
          <el-tag size="small" round effect="plain" class="book-count">
            {{ group.excerpts.length }}
          </el-tag>
        </div>
        <div class="book-header-right">
          <el-button
            type="primary"
            :icon="Plus"
            text
            size="small"
            @click.stop="openAddExcerpt(group.book)"
          >
            摘抄
          </el-button>
          <el-button
            type="warning"
            :icon="Edit"
            text
            size="small"
            @click.stop="openEditBook(group.book)"
          />
          <el-button
            type="danger"
            :icon="Delete"
            text
            size="small"
            @click.stop="handleDeleteBook(group.book)"
          />
        </div>
      </div>

      <!-- 摘抄列表 -->
      <transition name="collapse">
        <div v-show="isExpanded(group.book.id)" class="book-excerpts">
          <div
            v-for="excerpt in group.excerpts"
            :key="excerpt.id"
            class="excerpt-card"
          >
            <!-- 三列核心区：摘抄 | 想法 | 标签 -->
            <div class="excerpt-row">
              <div class="excerpt-col" v-if="excerpt.content">
                <div class="excerpt-label">摘抄</div>
                <div class="excerpt-text">{{ excerpt.content }}</div>
              </div>

              <div class="excerpt-col insight-col" v-if="excerpt.insights">
                <div class="insights-label">我的想法</div>
                <div class="insights-text">{{ excerpt.insights }}</div>
              </div>

              <div class="excerpt-col tags-col" v-if="excerpt.tags.length">
                <div class="excerpt-label">标签</div>
                <div class="excerpt-tags">
                  <el-tag
                    v-for="tag in excerpt.tags"
                    :key="tag.id"
                    :color="tag.color"
                    effect="dark"
                    size="small"
                  >
                    {{ tag.name }}
                  </el-tag>
                </div>
              </div>
            </div>

            <!-- 链接 -->
            <div v-if="excerpt.links.length" class="excerpt-links">
              <a
                v-for="(link, i) in excerpt.links"
                :key="i"
                :href="link"
                target="_blank"
                rel="noopener noreferrer"
                class="excerpt-link"
              >
                <el-icon><Link /></el-icon> {{ truncate(link, 50) }}
              </a>
            </div>

            <!-- 图片 -->
            <div v-if="excerpt.images.length" class="excerpt-images">
              <el-image
                v-for="(img, i) in excerpt.images"
                :key="i"
                :src="img"
                fit="cover"
                style="width: 80px; height: 80px; border-radius: 4px; margin-right: 6px; cursor: pointer"
                :preview-src-list="excerpt.images"
                :initial-index="i"
              />
            </div>

            <!-- 时间和操作 -->
            <div class="excerpt-footer">
              <span class="excerpt-time">{{
                excerpt.updated_at?.slice(0, 16)?.replace('T', ' ')
              }}</span>
              <div class="excerpt-actions">
                <el-button
                  :type="excerpt.is_favorite ? 'warning' : 'default'"
                  :icon="excerpt.is_favorite ? StarFilled : Star"
                  text
                  size="small"
                  @click="handleToggleFavorite(excerpt)"
                />
                <el-button type="primary" :icon="Edit" text size="small" @click="openEdit(excerpt)">
                  编辑
                </el-button>
                <el-popconfirm
                  title="确定删除此摘抄？"
                  @confirm="handleDeleteExcerpt(excerpt.id)"
                >
                  <template #reference>
                    <el-button type="danger" text size="small">删除</el-button>
                  </template>
                </el-popconfirm>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog
      v-model="editVisible"
      title="编辑摘抄"
      width="600px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-position="top" v-if="editVisible">
        <el-form-item label="所属书籍">
          <el-select v-model="editForm.book_id" filterable placeholder="选择书籍" style="width: 100%">
            <el-option
              v-for="b in allBooks"
              :key="b.id"
              :label="b.title + (b.author ? ' — ' + b.author : '')"
              :value="b.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="摘抄原文">
          <el-input v-model="editForm.content" type="textarea" :rows="5" maxlength="5000" show-word-limit />
        </el-form-item>

        <el-form-item label="个人想法">
          <el-input v-model="editForm.insights" type="textarea" :rows="3" maxlength="5000" show-word-limit placeholder="写下你的思考..." />
        </el-form-item>

        <el-form-item label="相关链接">
          <div class="mini-link-list">
            <div v-for="(link, idx) in editForm.links" :key="idx" class="mini-link-row">
              <el-input v-model="editForm.links[idx]" placeholder="https://..." />
              <el-button type="danger" :icon="Close" circle size="small" @click="editForm.links.splice(idx, 1)" />
            </div>
          </div>
          <el-button type="primary" :icon="Plus" size="small" @click="editForm.links.push('')">添加链接</el-button>
        </el-form-item>

        <el-form-item label="标签">
          <el-select v-model="editForm.tag_ids" multiple filterable placeholder="选择标签..." style="width: 100%">
            <el-option v-for="tag in allTags" :key="tag.id" :label="tag.name" :value="tag.id" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleEditSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加摘抄弹窗 -->
    <el-dialog
      v-model="excerptDialogVisible"
      :title="'添加摘抄 — ' + (selectedBook ? selectedBook.title : '')"
      width="680px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <AddExcerpt
        v-if="excerptDialogVisible"
        :preset-book-id="selectedBook?.id"
        @saved="onExcerptSaved"
      />
    </el-dialog>

    <!-- 添加书籍弹窗 -->
    <el-dialog v-model="bookDialogVisible" title="添加书籍" width="400px" :close-on-click-modal="false">
      <el-form ref="bookFormRef" :model="bookForm" :rules="bookRules" label-position="top">
        <el-form-item label="书名" prop="title">
          <el-input v-model="bookForm.title" placeholder="输入书名" maxlength="255" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="bookForm.author" placeholder="作者（选填）" maxlength="255" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bookDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="bookSaving" @click="handleAddBook">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑书籍弹窗 -->
    <el-dialog v-model="editBookVisible" title="编辑书籍" width="400px" :close-on-click-modal="false">
      <el-form ref="editBookFormRef" :model="editBookForm" :rules="bookRules" label-position="top">
        <el-form-item label="书名" prop="title">
          <el-input v-model="editBookForm.title" placeholder="输入书名" maxlength="255" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="editBookForm.author" placeholder="作者（选填）" maxlength="255" />
        </el-form-item>
        <el-form-item label="封面URL">
          <el-input v-model="editBookForm.cover" placeholder="封面图片链接（选填）" maxlength="500" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editBookVisible = false">取消</el-button>
        <el-button type="primary" :loading="editBookSaving" @click="handleEditBookSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowRight, Delete, Edit, Close, Plus, Link, Star, StarFilled, Download, Refresh } from '@element-plus/icons-vue'
import { getBookGroups, getBooks, getTags, updateExcerpt, deleteExcerpt, deleteBook, createBook, updateBook, getRandomExcerpt, toggleFavorite, exportExcerpts } from '../api/index.js'
import AddExcerpt from './AddExcerpt.vue'

const loading = ref(false)
const saving = ref(false)
const groups = ref([])
const allBooks = ref([])
const allTags = ref([])
const expanded = ref(new Set())
const editVisible = ref(false)
const editFormRef = ref(null)
const editingId = ref(null)
const editForm = ref({
  book_id: null,
  content: '',
  insights: '',
  links: [],
  tag_ids: [],
})
const editRules = {}

// ── 添加摘抄（per-book） ──────────────────────
const excerptDialogVisible = ref(false)
const selectedBook = ref(null)

function openAddExcerpt(book) {
  selectedBook.value = book
  excerptDialogVisible.value = true
}

function onExcerptSaved() {
  excerptDialogVisible.value = false
  selectedBook.value = null
  fetchData()
}

// ── 添加书籍 ──────────────────────────────────
const bookDialogVisible = ref(false)
const bookSaving = ref(false)
const bookFormRef = ref(null)
const bookForm = ref({ title: '', author: '' })
const bookRules = {
  title: [{ required: true, message: '请输入书名', trigger: 'blur' }],
}

async function handleAddBook() {
  const valid = await bookFormRef.value.validate().catch(() => false)
  if (!valid) return
  bookSaving.value = true
  try {
    await createBook({ title: bookForm.value.title, author: bookForm.value.author })
    ElMessage.success('书籍添加成功')
    bookDialogVisible.value = false
    bookForm.value = { title: '', author: '' }
    fetchData()
  } catch (e) {
    if (e.response?.status === 400) {
      ElMessage.warning('该书籍已存在')
    } else {
      ElMessage.error('添加失败')
    }
  } finally {
    bookSaving.value = false
  }
}

function isExpanded(bookId) {
  return expanded.value.has(bookId)
}

function toggleBook(bookId) {
  const s = new Set(expanded.value)
  if (s.has(bookId)) s.delete(bookId)
  else s.add(bookId)
  expanded.value = s
}

async function fetchData() {
  loading.value = true
  try {
    const [groupRes, booksRes, tagsRes] = await Promise.all([
      getBookGroups(),
      getBooks(),
      getTags(),
    ])
    groups.value = groupRes.data
    allBooks.value = booksRes.data
    allTags.value = tagsRes.data
    // auto expand all
    const s = new Set()
    groupRes.data.forEach((g) => s.add(g.book.id))
    expanded.value = s
  } catch (e) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

async function handleDeleteExcerpt(id) {
  try {
    await deleteExcerpt(id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

async function handleDeleteBook(book) {
  try {
    await ElMessageBox.confirm(
      `确定删除《${book.title}》及其全部 ${book.excerpt_count || ''} 条摘抄？`,
      '删除书籍',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteBook(book.id)
    ElMessage.success('已删除')
    fetchData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

function openEdit(excerpt) {
  editingId.value = excerpt.id
  editForm.value = {
    book_id: excerpt.book_id,
    content: excerpt.content || '',
    insights: excerpt.insights || '',
    links: [...(excerpt.links || [])],
    tag_ids: excerpt.tags.map((t) => t.id),
  }
  editVisible.value = true
}

// ── 编辑书籍 ─────────────────────────────────
const editBookVisible = ref(false)
const editBookSaving = ref(false)
const editBookFormRef = ref(null)
const editingBookId = ref(null)
const editBookForm = ref({ title: '', author: '', cover: '' })

function openEditBook(book) {
  editingBookId.value = book.id
  editBookForm.value = {
    title: book.title,
    author: book.author,
    cover: book.cover || '',
  }
  editBookVisible.value = true
}

async function handleEditBookSave() {
  const valid = await editBookFormRef.value.validate().catch(() => false)
  if (!valid) return
  editBookSaving.value = true
  try {
    await updateBook(editingBookId.value, {
      title: editBookForm.value.title,
      author: editBookForm.value.author,
      cover: editBookForm.value.cover,
    })
    ElMessage.success('书籍更新成功')
    editBookVisible.value = false
    fetchData()
  } catch (e) {
    ElMessage.error('更新失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    editBookSaving.value = false
  }
}

async function handleEditSave() {
  saving.value = true
  try {
    await updateExcerpt(editingId.value, {
      book_id: editForm.value.book_id,
      content: editForm.value.content,
      insights: editForm.value.insights,
      links: editForm.value.links.filter(Boolean),
      tag_ids: editForm.value.tag_ids,
    })
    ElMessage.success('更新成功')
    editVisible.value = false
    fetchData()
  } catch (e) {
    ElMessage.error('更新失败')
  } finally {
    saving.value = false
  }
}

function truncate(text, max) {
  if (!text) return ''
  return text.length > max ? text.slice(0, max) + '...' : text
}

// ── Random excerpt ─────────────────────────────
const randomExcerpt = ref(null)

async function fetchRandom() {
  try {
    const { data } = await getRandomExcerpt()
    randomExcerpt.value = data
  } catch (e) {
    // silently ignore — no excerpts available
  }
}

// ── Favorite toggle ────────────────────────────
async function handleToggleFavorite(excerpt) {
  try {
    const { data } = await toggleFavorite(excerpt.id)
    excerpt.is_favorite = data.is_favorite
    ElMessage.success(data.is_favorite ? '已收藏' : '已取消收藏')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

// ── Export ──────────────────────────────────────
const exporting = ref(false)
async function handleExport() {
  exporting.value = true
  try {
    const { data } = await exportExcerpts({})
    const blob = new Blob([data], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `excerpts_${new Date().toISOString().slice(0,10)}.md`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

function refresh() {
  fetchData()
}

defineExpose({ refresh })
onMounted(() => {
  fetchData()
  fetchRandom()
})
</script>

<style scoped>
/* Random excerpt card */
.random-card {
  background: linear-gradient(135deg, #fff8e1, #fff3e0);
  border-radius: 12px;
  padding: 18px 20px;
  margin-bottom: 16px;
  cursor: pointer;
  box-shadow: 0 2px 12px rgba(255, 152, 0, 0.12);
  transition: opacity 0.3s;
}
.random-card:hover {
  opacity: 0.85;
}
.random-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.random-badge {
  font-size: 13px;
  font-weight: 600;
  color: #e65100;
  letter-spacing: 1px;
}
.random-content {
  font-size: 15px;
  line-height: 1.8;
  color: #3d3226;
  padding-left: 12px;
  border-left: 3px solid #ff9800;
  white-space: pre-wrap;
}
.random-meta {
  margin-top: 10px;
  font-size: 12px;
  color: #a0917e;
  display: flex;
  gap: 16px;
}
.random-insights {
  color: #6a8fbf;
  font-style: italic;
}

.shelf-toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.shelf-add-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #5c4a32;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(92, 74, 50, 0.3);
  transition: transform 0.15s, box-shadow 0.15s;
}

.shelf-add-btn:hover {
  transform: scale(1.08);
  box-shadow: 0 4px 14px rgba(92, 74, 50, 0.4);
}

.book-header-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  margin-left: 12px;
}

.book-group {
  margin-bottom: 16px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.book-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}

.book-header:hover {
  background: #faf8f5;
}

.book-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.collapse-icon {
  font-size: 14px;
  color: #a0917e;
  transition: transform 0.25s;
}

.collapse-icon.expanded {
  transform: rotate(90deg);
}

.book-title {
  font-size: 17px;
  font-weight: 600;
  color: #3d3226;
}

.book-author {
  font-size: 13px;
  color: #a0917e;
}

.book-count {
  font-size: 11px;
  margin-left: 4px;
}

.book-excerpts {
  border-top: 1px solid #f0ebe0;
  padding: 12px 18px 16px;
  background: #fdfcfa;
}

.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
}

.collapse-enter-to,
.collapse-leave-from {
  max-height: 2000px;
}

/* Excerpt Card */
.excerpt-card {
  padding: 14px 0;
  border-bottom: 1px dashed #e8e0d3;
}

.excerpt-card:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

/* Three-column row */
.excerpt-row {
  display: flex;
  gap: 16px;
}

.excerpt-col {
  flex: 1;
  min-width: 0;
}

.insight-col {
  flex: 1;
}

.tags-col {
  flex: 0 0 auto;
  max-width: 140px;
}

.excerpt-label,
.insights-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
  margin-bottom: 6px;
}

.excerpt-label {
  color: #b8956a;
}

.insights-label {
  color: #6a8fbf;
}

.excerpt-text {
  font-size: 14px;
  color: #3d3226;
  line-height: 1.7;
  padding-left: 10px;
  border-left: 3px solid #e8d5b0;
  white-space: pre-wrap;
  word-break: break-word;
}

.insights-text {
  font-size: 13px;
  color: #556677;
  line-height: 1.6;
  padding-left: 10px;
  border-left: 3px solid #b8cce8;
  white-space: pre-wrap;
  word-break: break-word;
}

.excerpt-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.excerpt-links {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.excerpt-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #8b7e6e;
  text-decoration: none;
}

.excerpt-link:hover {
  color: #5c4a32;
  text-decoration: underline;
}

.excerpt-images {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
}

.excerpt-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.excerpt-time {
  font-size: 11px;
  color: #c5b8a6;
}

.excerpt-actions {
  display: flex;
  gap: 4px;
}

/* Mini form styles for edit dialog */
.mini-link-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 6px;
}

.mini-link-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.mini-link-row .el-input {
  flex: 1;
}
</style>
