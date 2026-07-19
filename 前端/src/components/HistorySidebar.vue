<template>
  <div class="history-sidebar" :class="{ active: modelValue }">
    <div class="history-toggle-btn" @click="$emit('update:modelValue', !modelValue)">
      <div class="arrow"></div>
    </div>
    <div class="history-header">
      <button class="new-chat-btn" @click="$emit('new-chat')">新建对话</button>
      <button class="history-close-btn" @click="$emit('update:modelValue', false)">
        <div class="close-icon"></div>返回
      </button>
    </div>
    <div class="history-list-container">
      <div v-for="item in items" :key="item.id" class="history-item" :class="{ active: item.active }">
        <div class="history-item-content" @click="$emit('select', item)">{{ item.name }}</div>
        <button class="history-item-menu" @click.stop="toggleMenu(item)">
          <i data-feather="more-vertical"></i>
        </button>
        <div class="history-item-popup" :class="{ active: item.menuOpen }">
          <div class="history-menu-item" @click.stop="handleRename(item)">
            <i data-feather="edit-2"></i>
            <span>重命名</span>
          </div>
          <div class="history-menu-item" @click.stop="handleDelete(item)">
            <i data-feather="trash-2"></i>
            <span>删除</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'

const props = defineProps({
  modelValue: Boolean,
  items: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue', 'select', 'new-chat', 'rename', 'delete'])

// 切换菜单
const toggleMenu = (item) => {
  // 关闭其他菜单
  props.items.forEach(i => {
    if (i !== item) i.menuOpen = false
  })
  item.menuOpen = !item.menuOpen
  updateIcons()
}

// 重命名
const handleRename = (item) => {
  const newName = prompt('请输入新的名称：', item.name)
  if (newName && newName.trim()) {
    emit('rename', item, newName.trim())
  }
  item.menuOpen = false
  updateIcons()
}

// 删除
const handleDelete = (item) => {
  emit('delete', item)
  item.menuOpen = false
  updateIcons()
}

// 更新图标
const updateIcons = () => {
  nextTick(() => {
    if (window.feather) window.feather.replace()
  })
}

onMounted(() => {
  updateIcons()
})
</script>

<style scoped>
.history-sidebar {
  position: fixed;
  top: 0;
  right: -280px;
  width: 280px;
  height: 100vh;
  background-color: #ffffff;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1);
  z-index: 98;
  transition: right 0.3s;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.history-sidebar.active {
  right: 0;
}

.history-header {
  padding: 24px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.new-chat-btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #7dba28, #51830a);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  margin-bottom: 12px;
  transition: all 0.3s;
}

.new-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(125, 186, 40, 0.3);
}

.history-close-btn {
  width: 100%;
  padding: 10px;
  background-color: transparent;
  border: 1px solid #7dba28;
  border-radius: 8px;
  color: #51830a;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s;
}

.history-close-btn:hover {
  background-color: #f0f5e6;
}

.history-toggle-btn {
  position: absolute;
  top: 50%;
  left: -20px;
  transform: translateY(-50%);
  width: 20px;
  height: 60px;
  background-color: #7dba28;
  border-top-left-radius: 8px;
  border-bottom-left-radius: 8px;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  z-index: 99;
}

.history-toggle-btn:hover {
  background-color: #51830a;
  width: 24px;
}

.history-toggle-btn .arrow {
  width: 8px;
  height: 8px;
  border-left: 2px solid white;
  border-top: 2px solid white;
  transform: rotate(-45deg);
  transition: transform 0.3s;
}

.history-sidebar.active .history-toggle-btn .arrow {
  transform: rotate(135deg);
}

.history-list-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background-color: #f9f9f9;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  border: 1px solid transparent;
}

.history-item:hover {
  background-color: #f0f5e6;
  transform: translateX(-2px);
  border-color: #7dba28;
}

.history-item.active {
  background-color: rgba(125, 186, 40, 0.1);
  border-left: 4px solid #7dba28;
  font-weight: 500;
}

.history-item-content {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.history-item-menu {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.history-item-menu:hover {
  background-color: rgba(125, 186, 40, 0.2);
}

.history-item-menu i {
  width: 18px;
  height: 18px;
  color: #666;
}

.history-item-popup {
  position: absolute;
  right: 45px;
  top: 50%;
  transform: translateY(-50%);
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  padding: 4px 0;
  z-index: 10;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s;
  border: 1px solid #f0f0f0;
}

.history-item-popup.active {
  opacity: 1;
  visibility: visible;
}

.history-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.history-menu-item:hover {
  background-color: #f5f5f5;
  color: #7dba28;
}

.history-menu-item i {
  width: 14px;
  height: 14px;
}
</style>