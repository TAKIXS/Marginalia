<template>
  <el-dialog v-model="visible" title="管理标签" width="420px" :close-on-click-modal="false" @update:model-value="$emit('update:modelValue', $event)">
    <!-- 添加新标签 -->
    <div class="tag-manage-add">
      <el-input
        v-model="newTagName"
        placeholder="输入新标签名"
        size="small"
        style="flex: 1"
        @keyup.enter="handleAddTag"
      />
      <el-color-picker v-model="newTagColor" size="small" />
      <el-button type="primary" size="small" @click="handleAddTag">添加</el-button>
    </div>

    <!-- 已有标签列表 -->
    <div v-if="tags.length === 0" style="text-align: center; color: #909399; padding: 20px">暂无标签</div>
    <div v-else class="tag-manage-list">
      <div v-for="tag in tags" :key="tag.id" class="tag-manage-row">
        <el-color-picker v-model="tag.color" size="small" @change="(c) => handleColorChange(tag, c)" />
        <el-input
          v-model="tag.name"
          size="small"
          style="flex: 1"
          @blur="handleRename(tag)"
          @keyup.enter="handleRename(tag)"
        />
        <el-popconfirm
          :title="'删除标签「' + tag.name + '」？'"
          confirm-button-text="删除"
          @confirm="handleDeleteTag(tag.id)"
        >
          <template #reference>
            <el-button type="danger" :icon="Close" circle size="small" />
          </template>
        </el-popconfirm>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Close } from '@element-plus/icons-vue'
import { createTag, updateTag, deleteTag } from '../api/index.js'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  tags: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue', 'tagAdded', 'tagUpdated', 'tagDeleted'])

const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => { visible.value = v })
watch(visible, (v) => { emit('update:modelValue', v) })

const newTagName = ref('')
const newTagColor = ref('#409EFF')

async function handleAddTag() {
  const name = newTagName.value.trim()
  if (!name) return
  if (props.tags.find((t) => t.name === name)) {
    ElMessage.warning('标签名已存在')
    return
  }
  try {
    const { data } = await createTag({ name, color: newTagColor.value })
    emit('tagAdded', data)
    newTagName.value = ''
    newTagColor.value = '#409EFF'
    ElMessage.success('标签添加成功')
  } catch (e) {
    ElMessage.error('添加失败: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleRename(tag) {
  const name = tag.name.trim()
  if (!name) return
  try {
    await updateTag(tag.id, { name, color: tag.color })
    emit('tagUpdated', tag)
    ElMessage.success('标签已更新')
  } catch (e) {
    ElMessage.error('更新失败: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleColorChange(tag, color) {
  try {
    await updateTag(tag.id, { color })
    emit('tagUpdated', tag)
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

async function handleDeleteTag(id) {
  try {
    await deleteTag(id)
    emit('tagDeleted', id)
    ElMessage.success('标签已删除')
  } catch (e) {
    ElMessage.error('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}
</script>

<style scoped>
.tag-manage-add {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid #ebeef5;
}

.tag-manage-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tag-manage-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 8px;
}
</style>
