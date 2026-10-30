<template>
  <div class="template-modal-overlay" :class="{ active: modelValue }" @click.self="closeModal">
    <div class="template-modal">

      <!-- 头部：标题 + 筛选 -->
      <div class="template-header">
        <h2 class="template-title">选择背景模板</h2>
        <div class="template-filter-container">
          <span class="template-filter-label">模板场景：</span>
          <button v-for="scene in sceneFilters" :key="scene.value"
            class="template-filter-btn"
            :class="{ active: selectedScene === scene.value }"
            @click="selectedScene = scene.value">
            {{ scene.label }}
          </button>
        </div>
      </div>

      <!-- AI生成海报选项 -->
      <div class="ai-generate-section" v-if="selectedScene === 'ai'">
        <div class="ai-generate-card">
          <div class="ai-icon">🤖</div>
          <div class="ai-content">
            <h3 class="ai-title">Doubao-Seedream 4.0 AI 生成</h3>
            <p class="ai-desc">输入文字描述，AI将根据您的需求智能生成海报背景</p>
            <textarea 
              v-model="aiPrompt" 
              class="ai-prompt-input"
              placeholder="描述您想要的海报风格，例如：清新自然风格，绿色渐变背景，适合农产品宣传..."
              rows="3"></textarea>
            <div class="ai-preset-tags">
              <span v-for="preset in aiPresets" :key="preset" 
                class="ai-preset-tag"
                @click="applyPreset(preset)">{{ preset }}</span>
            </div>
          </div>
          <button class="ai-generate-btn" 
            @click="generateWithAI"
            :disabled="!aiPrompt.trim() || isAIGenerating">
            <span v-if="isAIGenerating" class="loading-spinner-sm"></span>
            <span v-else>✨ 生成海报</span>
          </button>
        </div>
      </div>

      <!-- 内容：左缩略图 + 右预览 -->
      <div class="template-content">

        <!-- 左侧缩略图列表 -->
        <div class="template-thumbnail-container">
          <div v-if="loading" class="loading-grid">
            <div v-for="n in 6" :key="n" class="skeleton-thumb"></div>
          </div>
          <div v-else class="template-thumbnail-grid">
            <div v-for="tpl in filteredTemplates" :key="tpl.id"
              class="template-thumbnail"
              :class="{ selected: selectedTemplateId === tpl.id }"
              @click="selectTemplate(tpl)">
              <!-- 真实缩略图 or 占位色块 -->
              <img v-if="tpl.thumbnail" :src="tpl.thumbnail" class="thumb-img" :alt="tpl.name" />
              <div v-else class="thumb-placeholder" :style="{ background: tpl.color || '#f0f5e6' }"></div>
              <!-- 悬浮遮罩 -->
              <div class="template-thumbnail-overlay">{{ tpl.name }}</div>
              <!-- 删除按钮（AI生成和自定义模板可删除） -->
              <button v-if="tpl.type === 'ai' || tpl.type === 'file'"
                class="thumb-delete-btn"
                @click.stop="deleteTemplate(tpl)"
                title="删除此模板">×</button>
            </div>
            <div v-if="filteredTemplates.length === 0" class="no-results">没有匹配的模板</div>
          </div>
        </div>

        <!-- 右侧预览区 -->
        <div class="template-preview-container">
          <!-- 大预览 -->
          <div class="template-preview-main">
            <img v-if="selectedTemplate?.thumbnail" :src="selectedTemplate.thumbnail" class="preview-img" :alt="selectedTemplate.name" />
            <div v-else class="preview-placeholder">
              <span>{{ selectedTemplate ? selectedTemplate.name : '选择左侧模板预览' }}</span>
            </div>
          </div>

          <!-- 颜色变体（内置模板显示色调对比，文件模板显示滤镜预览）-->
          <div class="template-variants" v-if="selectedTemplate">
            <div class="variant-label">色调参考</div>
            <div class="variant-row">
              <div v-for="(swatch, i) in colorSwatches" :key="i"
                class="color-swatch"
                :style="{ background: swatch.color }"
                :title="swatch.name">
                <span class="swatch-name">{{ swatch.name }}</span>
              </div>
            </div>
          </div>

          <!-- 描述 -->
          <div class="template-description" v-if="selectedTemplate">
            <div class="desc-title">{{ selectedTemplate.name }}</div>
            <div class="desc-body" v-html="selectedTemplate.description || '适合农产品宣传使用，搭配产品图效果更佳。'"></div>
            <div class="desc-type-badge" :class="selectedTemplate.type">
              {{ selectedTemplate.type === 'file' ? '📁 自定义模板' : '🎨 内置模板' }}
            </div>
          </div>
        </div>
      </div>

      <!-- 底部按钮 -->
      <div class="template-actions">
        <button class="template-action-btn template-cancel-btn" @click="closeModal">取消</button>
        <button class="template-action-btn template-select-btn"
          :disabled="!selectedTemplate"
          @click="confirmSelect">
          {{ selectedTemplate ? `选择「${selectedTemplate.name}」` : '请先选择模板' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({ modelValue: Boolean })
const emit  = defineEmits(['update:modelValue', 'select'])

const IMG_API = import.meta.env.VITE_IMG_API || 'http://localhost:5003'

// ===== 状态 =====
const loading           = ref(false)
const allTemplates      = ref([])
const selectedTemplateId = ref(null)
const selectedScene     = ref('all')

// ===== 场景筛选定义 =====
const sceneFilters = [
  { value: 'all',      label: '全部' },
  { value: 'builtin',  label: '内置渐变' },
  { value: 'file',     label: '自定义图片' },
  { value: 'ai',       label: 'AI生成海报' },
]

// ===== AI生成相关状态 =====
const aiPrompt = ref('')
const isAIGenerating = ref(false)
const aiGeneratedImage = ref('')

// AI预设标签
const aiPresets = [
  '清新自然',
  '复古田园',
  '现代简约',
  '节日氛围',
  '高端质感',
  '手绘插画',
]

// ===== 计算 =====
const selectedTemplate = computed(() =>
  allTemplates.value.find(t => t.id === selectedTemplateId.value) || null
)

const filteredTemplates = computed(() => {
  if (selectedScene.value === 'all') return allTemplates.value
  return allTemplates.value.filter(t => t.type === selectedScene.value)
})

// 色块参考（用于视觉展示）
const colorSwatches = computed(() => {
  if (!selectedTemplate.value) return []
  // 内置模板有颜色信息，文件模板随机展示滤镜色调
  const presets = [
    { name: '原色', color: '#f5f5f0' },
    { name: '暖调', color: '#fff3e0' },
    { name: '冷调', color: '#e3f2fd' },
    { name: '复古', color: '#f3e5d8' },
  ]
  return presets
})

// ===== 加载模板（从 image_service 拉取）=====
const loadTemplates = async () => {
  loading.value = true
  try {
    const res = await fetch(`${IMG_API}/api/templates`)
    const data = await res.json()
    if (data.templates) {
      allTemplates.value = data.templates
      // 默认选第一个
      if (data.templates.length > 0) {
        selectedTemplateId.value = data.templates[0].id
      }
    }
  } catch (e) {
    console.warn('模板服务未启动，使用本地占位模板', e)
    // 后端未启动时的占位数据
    allTemplates.value = [
      { id: 'green_gradient', name: '清新绿渐变',   type: 'builtin', thumbnail: null, color: 'linear-gradient(160deg,#d0ead0,#f0faf0)' },
      { id: 'warm_yellow',    name: '丰收暖黄',     type: 'builtin', thumbnail: null, color: 'linear-gradient(160deg,#fff3b9,#ffffd7)' },
      { id: 'earth_brown',    name: '大地棕',       type: 'builtin', thumbnail: null, color: 'linear-gradient(160deg,#d2bea5,#ebdcc8)' },
      { id: 'sky_blue',       name: '天空蓝',       type: 'builtin', thumbnail: null, color: 'linear-gradient(160deg,#b9dcf5,#d7eeff)' },
      { id: 'sakura_pink',    name: '樱花粉',       type: 'builtin', thumbnail: null, color: 'linear-gradient(160deg,#ffd7d7,#ffebeb)' },
      { id: 'pure_white',     name: '简约白',       type: 'builtin', thumbnail: null, color: 'linear-gradient(160deg,#fafafa,#ffffff)' },
    ]
    selectedTemplateId.value = 'green_gradient'
  } finally {
    loading.value = false
  }
}

// ===== AI生成方法 =====
const applyPreset = (preset) => {
  if (aiPrompt.value) {
    aiPrompt.value += '，' + preset
  } else {
    aiPrompt.value = preset + '风格海报背景'
  }
}

const generateWithAI = async () => {
  if (!aiPrompt.value.trim()) return
  
  isAIGenerating.value = true
  
  try {
    // 调用后端AI生成海报接口
    const res = await fetch(`${IMG_API}/api/ai/generate-poster`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: aiPrompt.value,
        size: '1024x1024',
        style: ''
      })
    })
    
    const data = await res.json()
    
    if (data.success) {
      // 使用后端返回的真实数据
      aiGeneratedImage.value = data.image_url || data.image_base64
      
      // 创建模板对象
      const aiTemplate = {
        id: data.template_id || 'ai_generated_' + Date.now(),
        name: data.name || 'AI生成-' + aiPrompt.value.slice(0, 20),
        type: 'ai',
        thumbnail: data.thumbnail || aiGeneratedImage.value,
        image: aiGeneratedImage.value,
        ai_prompt: aiPrompt.value,
        auto_composition: data.auto_composition || true
      }
      
      // 添加到模板列表并选中
      allTemplates.value.push(aiTemplate)
      selectedTemplateId.value = aiTemplate.id
      
      // 自动切换到全部视图显示
      selectedScene.value = 'all'
      
      // 显示提示信息
      if (data.message) {
        console.log('AI生成提示:', data.message)
      }
      
      alert('AI海报生成成功！' + (data.message ? '（' + data.message + '）' : ''))
    } else {
      console.error('AI生成失败:', data.error)
      alert('AI海报生成失败：' + (data.error || '未知错误'))
    }
  } catch (e) {
    console.error('AI生成海报失败:', e)
    alert('AI海报生成失败：' + e.message)
  } finally {
    isAIGenerating.value = false
  }
}

// ===== 操作 =====
const selectTemplate = (tpl) => { selectedTemplateId.value = tpl.id }

const closeModal = () => emit('update:modelValue', false)

const confirmSelect = () => {
  if (selectedTemplate.value) {
    emit('select', selectedTemplate.value)
    closeModal()
  }
}

// ===== 删除模板 =====
const deleteTemplate = async (tpl) => {
  if (!confirm(`确定要删除模板「${tpl.name}」吗？`)) return
  try {
    const res = await fetch(`${IMG_API}/api/templates/${tpl.id}`, { method: 'DELETE' })
    const data = await res.json()
    if (data.success || res.ok) {
      allTemplates.value = allTemplates.value.filter(t => t.id !== tpl.id)
      if (selectedTemplateId.value === tpl.id) {
        selectedTemplateId.value = allTemplates.value[0]?.id || null
      }
    } else {
      alert('删除失败: ' + (data.error || '未知错误'))
    }
  } catch (e) {
    // 后端未响应也从列表中移除
    allTemplates.value = allTemplates.value.filter(t => t.id !== tpl.id)
  }
}

// 打开时加载模板
watch(() => props.modelValue, (open) => {
  if (open && allTemplates.value.length === 0) {
    loadTemplates()
  }
})
</script>

<style scoped>
.template-modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-color: rgba(0,0,0,0.36);
  z-index: 1000; display: none; align-items: center; justify-content: center;
  padding: 20px;
}
.template-modal-overlay.active { display: flex; }

.template-modal {
  width: 1100px;
  max-height: 88vh;
  background: white;
  border-radius: 24px;
  transform: scale(0.92);
  opacity: 0;
  transition: all 0.3s;
  box-shadow: 0 24px 64px rgba(0,0,0,0.28);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.template-modal-overlay.active .template-modal { transform: scale(1); opacity: 1; }

/* ===== 头部 ===== */
.template-header {
  padding: 24px 40px 20px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}
.template-title { font-size: 28px; font-weight: 500; margin-bottom: 16px; color: #2c3e2f; }

/* ===== AI生成海报区域 ===== */
.ai-generate-section {
  padding: 20px 40px;
  background: linear-gradient(135deg, #e8f5e9 0%, #f0f7e6 100%);
  border-bottom: 1px solid #c5e1a5;
}

.ai-generate-card {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.ai-icon {
  font-size: 48px;
  flex-shrink: 0;
}

.ai-content {
  flex: 1;
}

.ai-title {
  font-size: 20px;
  font-weight: 600;
  color: #2e7d32;
  margin-bottom: 8px;
}

.ai-desc {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
}

.ai-prompt-input {
  width: 100%;
  padding: 14px 16px;
  border: 1.5px solid #c5e1a5;
  border-radius: 12px;
  font-size: 14px;
  resize: vertical;
  background: white;
  color: #333;
  margin-bottom: 12px;
}

.ai-prompt-input:focus {
  outline: none;
  border-color: #8bc34a;
  box-shadow: 0 0 0 3px rgba(139, 195, 74, 0.15);
}

.ai-preset-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ai-preset-tag {
  padding: 6px 14px;
  background: white;
  border: 1px solid #8bc34a;
  border-radius: 20px;
  font-size: 13px;
  color: #6a994e;
  cursor: pointer;
  transition: all 0.2s;
}

.ai-preset-tag:hover {
  background: #8bc34a;
  color: white;
}

.ai-generate-btn {
  padding: 14px 32px;
  background: linear-gradient(135deg, #8bc34a, #6a994e);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(139, 195, 74, 0.3);
}

.ai-generate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(139, 195, 74, 0.4);
}

.ai-generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner-sm {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.template-filter-container {
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
}
.template-filter-label { font-size: 14px; color: #888; white-space: nowrap; }
.template-filter-btn {
  height: 32px; padding: 0 16px; background: #f5f5f5; border: 1px solid #e0e0e0;
  border-radius: 20px; cursor: pointer; font-size: 13px; transition: all 0.2s;
}
.template-filter-btn:hover { background: #f0f5e6; border-color: #8bc34a; }
.template-filter-btn.active { background: #8bc34a; color: white; border-color: #8bc34a; }

/* ===== 内容区 ===== */
.template-content {
  flex: 1; display: flex; gap: 28px; padding: 20px 40px; overflow: hidden; min-height: 0;
}

/* 左：缩略图 */
.template-thumbnail-container {
  width: 340px; overflow-y: auto; flex-shrink: 0;
  border: 1px solid #e0e0e0; border-radius: 16px;
  padding: 16px; background: #fafafa;
}
.template-thumbnail-container::-webkit-scrollbar { width: 4px; }
.template-thumbnail-container::-webkit-scrollbar-thumb { background: #c5e1a5; border-radius: 4px; }

.template-thumbnail-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;
}

.loading-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;
}
.skeleton-thumb {
  width: 100%; height: 100px; border-radius: 10px;
  background: linear-gradient(90deg,#f0f0f0 25%,#e8e8e8 50%,#f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

.template-thumbnail {
  position: relative;
  width: 100%; height: 100px;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s;
  border: 2px solid transparent;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.template-thumbnail:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.12); }
.template-thumbnail.selected { border-color: #8bc34a; box-shadow: 0 0 0 3px rgba(139,195,74,0.25); }

.thumb-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.thumb-placeholder { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }

/* 删除按钮 */
.thumb-delete-btn {
  position: absolute; top: 4px; right: 4px; z-index: 10;
  width: 22px; height: 22px; border-radius: 50%;
  background: rgba(220,50,50,0.85); color: white;
  border: none; cursor: pointer; font-size: 14px; line-height: 1;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity 0.2s;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
}
.template-thumbnail:hover .thumb-delete-btn { opacity: 1; }
.thumb-delete-btn:hover { background: rgba(200,30,30,1); transform: scale(1.1); }

.template-thumbnail-overlay {
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
  color: white; font-size: 13px; font-weight: 500;
  opacity: 0; transition: opacity 0.2s;
}
.template-thumbnail:hover .template-thumbnail-overlay,
.template-thumbnail.selected .template-thumbnail-overlay { opacity: 1; }

.no-results { grid-column: 1/-1; text-align: center; padding: 40px; color: #888; }

/* 右：预览区 */
.template-preview-container {
  flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 16px;
}

.template-preview-main {
  width: 100%; height: 320px; border-radius: 16px; overflow: hidden;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12); flex-shrink: 0;
  background: #f5f5f5; position: relative;
}
.preview-img { width: 100%; height: 100%; object-fit: cover; }
.preview-placeholder {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
  color: #aaa; font-size: 16px;
}

/* 色块变体 */
.template-variants { background: #f9fafb; border-radius: 12px; padding: 14px; }
.variant-label { font-size: 12px; font-weight: 600; color: #888; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }
.variant-row { display: flex; gap: 8px; flex-wrap: wrap; }
.color-swatch {
  width: 52px; height: 36px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1); cursor: pointer; position: relative;
  overflow: hidden;
}
.swatch-name { font-size: 10px; color: rgba(0,0,0,0.5); font-weight: 600; }

/* 描述 */
.template-description { background: #f9fafb; border-radius: 12px; padding: 16px; }
.desc-title { font-size: 18px; font-weight: 600; color: #2c3e2f; margin-bottom: 8px; }
.desc-body { font-size: 14px; color: #555; line-height: 1.6; margin-bottom: 10px; }
.desc-type-badge {
  display: inline-block;
  padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500;
}
.desc-type-badge.builtin { background: #e8f5e9; color: #2e7d32; }
.desc-type-badge.file    { background: #e3f2fd; color: #1565c0; }

/* ===== 底部 ===== */
.template-actions {
  height: 80px; display: flex; align-items: center; justify-content: center;
  gap: 20px; border-top: 1px solid #f0f0f0; flex-shrink: 0;
}
.template-action-btn {
  height: 46px; padding: 0 32px; border-radius: 12px;
  border: none; cursor: pointer; font-size: 16px; font-weight: 500; transition: all 0.25s;
}
.template-cancel-btn { background: #e0e0e0; color: #666; }
.template-cancel-btn:hover { background: #c8c8c8; transform: translateY(-2px); }
.template-select-btn { background: linear-gradient(135deg,#8bc34a,#6a994e); color: white; min-width: 180px; box-shadow: 0 4px 12px rgba(139,195,74,0.3); }
.template-select-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(139,195,74,0.4); }
.template-select-btn:disabled { background: #c8d8b0; cursor: not-allowed; transform: none; box-shadow: none; }
</style>
