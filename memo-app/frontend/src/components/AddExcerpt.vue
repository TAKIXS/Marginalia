<template>
  <div class="add-excerpt">
    <el-card shadow="never">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleSubmit"
      >
        <!-- 选择/创建书籍 -->
        <el-form-item label="所属书籍" prop="book_id">
          <el-select
            v-model="form.book_id"
            filterable
            placeholder="选择书籍..."
            style="width: 100%"
          >
            <el-option
              v-for="b in books"
              :key="b.id"
              :label="b.title + (b.author ? ' — ' + b.author : '')"
              :value="b.id"
            />
          </el-select>
        </el-form-item>

        <!-- 摘抄原文 -->
        <el-form-item label="摘抄原文">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="6"
            placeholder="粘贴或输入书中的原文摘抄..."
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>

        <!-- 个人想法 -->
        <el-form-item>
          <template #label>
            <div class="tag-label-row">
              <span>个人想法</span>
              <el-button type="primary" link size="small" :loading="aiLoading" @click="handleGenerateInsights">
                <el-icon><MagicStick /></el-icon> AI 帮写感悟
              </el-button>
            </div>
          </template>
          <el-input
            v-model="form.insights"
            type="textarea"
            :rows="3"
            placeholder="写下你对这段原文的思考、评论或联想..."
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>

        <!-- 相关链接 -->
        <el-form-item label="相关链接">
          <div class="link-list">
            <div v-for="(link, idx) in form.links" :key="idx" class="link-row">
              <el-input v-model="form.links[idx]" placeholder="https://..." clearable />
              <el-button type="danger" :icon="Close" circle size="small" @click="form.links.splice(idx, 1)" />
            </div>
          </div>
          <el-button type="primary" :icon="Plus" size="small" @click="form.links.push('')">添加链接</el-button>
        </el-form-item>

        <!-- 图片上传 -->
        <el-form-item label="图片">
          <div class="image-upload-area">
            <div v-for="(img, idx) in form.images" :key="idx" class="image-preview-item">
              <el-image :src="img" fit="cover" style="width: 100px; height: 100px; border-radius: 6px" :preview-src-list="[img]" />
              <el-button class="image-remove-btn" type="danger" :icon="Close" circle size="small" @click="form.images.splice(idx, 1)" />
            </div>
            <el-upload
              :before-upload="handleImageUpload"
              :show-file-list="false"
              accept="image/*"
              class="image-upload-trigger"
            >
              <div class="upload-placeholder">
                <el-icon><Plus /></el-icon>
                <span>上传</span>
              </div>
            </el-upload>
          </div>
        </el-form-item>

        <!-- 标签 -->
        <el-form-item>
          <template #label>
            <div class="tag-label-row">
              <span>标签</span>
              <el-button type="primary" link size="small" @click="tagManageVisible = true">管理标签</el-button>
            </div>
          </template>
          <div class="tag-section">
            <el-select
              v-model="form.tag_ids"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="选择或创建标签..."
              style="width: 100%"
              @change="onTagChange"
            >
              <el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.id">
                <span class="tag-option">
                  <span class="tag-dot" :style="{ background: tag.color }"></span>
                  {{ tag.name }}
                </span>
              </el-option>
            </el-select>
            <div v-if="selectedTagObjs.length" class="selected-tags">
              <el-tag
                v-for="tag in selectedTagObjs"
                :key="tag.id"
                :color="tag.color"
                closable
                size="small"
                effect="dark"
                @close="form.tag_ids = form.tag_ids.filter((id) => id !== tag.id)"
                style="margin: 4px 4px 0 0"
              >
                {{ tag.name }}
              </el-tag>
            </div>
          </div>
        </el-form-item>

        <!-- 标签管理弹窗 -->
        <TagManager
          v-model="tagManageVisible"
          :tags="tags"
          @tag-added="onTagAdded"
          @tag-updated="onTagUpdated"
          @tag-deleted="onTagDeleted"
        />

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit" size="large">
            保存摘抄
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Close, MagicStick } from '@element-plus/icons-vue'
import { createExcerpt, getBooks, getTags, createTag, uploadImage, generateInsights } from '../api/index.js'
import TagManager from './TagManager.vue'

const props = defineProps({
  presetBookId: { type: Number, default: null },
})

const emit = defineEmits(['saved'])

const formRef = ref(null)
const submitting = ref(false)
const aiLoading = ref(false)
const books = ref([])
const tags = ref([])
const tagManageVisible = ref(false)

const form = reactive({
  book_id: null,
  content: '',
  insights: '',
  links: [],
  images: [],
  tag_ids: [],
})

const rules = {
  book_id: [{ required: true, message: '请选择一本书', trigger: 'change' }],
}

const selectedTagObjs = computed(() => tags.value.filter((t) => form.tag_ids.includes(t.id)))

async function fetchMeta() {
  try {
    const [bookRes, tagRes] = await Promise.all([getBooks(), getTags()])
    books.value = bookRes.data
    tags.value = tagRes.data
  } catch (e) {
    console.error('加载元数据失败', e)
  }
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
  form.tag_ids = form.tag_ids.filter((id) => id !== tagId)
}

async function onTagChange(ids) {
  for (const id of ids) {
    if (typeof id === 'string' && !tags.value.find((t) => t.name === id)) {
      try {
        const { data } = await createTag({ name: id, color: randomColor() })
        const idx = form.tag_ids.indexOf(id)
        form.tag_ids.splice(idx, 1, data.id)
        tags.value.push(data)
      } catch (e) {
        ElMessage.warning('标签创建失败')
      }
    }
  }
}

function randomColor() {
  const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#9254DE', '#FF9800', '#00BCD4']
  return colors[Math.floor(Math.random() * colors.length)]
}

async function handleImageUpload(file) {
  try {
    const { data } = await uploadImage(file)
    form.images.push(data.url)
    ElMessage.success('上传成功')
  } catch (e) {
    ElMessage.error('上传失败')
  }
  return false
}

async function handleGenerateInsights() {
  if (!form.content.trim()) {
    ElMessage.warning('请先填写摘抄原文')
    return
  }
  aiLoading.value = true
  try {
    const { data } = await generateInsights({ content: form.content, book_id: form.book_id })
    form.insights = data.insights
    ElMessage.success('感悟已生成')
  } catch (e) {
    ElMessage.error('生成失败: ' + (e.response?.data?.detail || '请检查 API Key 配置'))
  } finally {
    aiLoading.value = false
  }
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await createExcerpt({
      book_id: form.book_id,
      content: form.content,
      insights: form.insights,
      links: form.links.filter(Boolean),
      images: form.images,
      tag_ids: form.tag_ids,
    })
    ElMessage.success('摘抄保存成功')
    resetForm()
    emit('saved')
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  form.book_id = null
  form.content = ''
  form.insights = ''
  form.links = []
  form.images = []
  form.tag_ids = []
  formRef.value?.resetFields()
}

watch(() => props.presetBookId, (id) => {
  if (id) form.book_id = id
}, { immediate: true })

onMounted(fetchMeta)
</script>

<style scoped>
.add-excerpt {
  max-width: 680px;
  margin: 0 auto;
}

.link-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 8px;
}

.link-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.link-row .el-input {
  flex: 1;
}

.image-upload-area {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.image-preview-item {
  position: relative;
  width: 100px;
  height: 100px;
}

.image-remove-btn {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 20px;
  height: 20px;
}

.upload-placeholder {
  width: 100px;
  height: 100px;
  border: 2px dashed #dcdfe6;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.upload-placeholder:hover {
  border-color: #409eff;
}

.upload-placeholder .el-icon {
  font-size: 22px;
  margin-bottom: 2px;
}

.tag-option {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.tag-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.selected-tags {
  margin-top: 8px;
}

.tag-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
</style>
