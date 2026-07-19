<template>
  <div class="progress-card" v-if="visible">
    <!-- 标题行 -->
    <div class="progress-header">
      <span class="progress-icon">🎨</span>
      <span class="progress-title">AI 正在处理图片</span>
      <span class="progress-pct">{{ progress }}%</span>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar-track">
      <div class="progress-bar-fill" :style="{ width: progress + '%' }">
        <div class="progress-shimmer"></div>
      </div>
    </div>

    <!-- 步骤描述 -->
    <div class="progress-step">
      <span class="step-dot" :class="stepClass"></span>
      {{ step || '处理中…' }}
    </div>

    <!-- 步骤气泡（可视化各阶段）-->
    <div class="step-bubbles">
      <div v-for="s in steps" :key="s.label"
        class="step-bubble"
        :class="{
          done:   progress >= s.end,
          active: progress >= s.start && progress < s.end,
          wait:   progress < s.start
        }">
        <span class="bubble-icon">{{ s.icon }}</span>
        <span class="bubble-label">{{ s.label }}</span>
      </div>
    </div>

    <!-- 提示语 -->
    <div class="progress-tip">{{ randomTip }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

const props = defineProps({
  visible:  { type: Boolean, default: false },
  progress: { type: Number,  default: 0 },
  step:     { type: String,  default: '' },
})

const steps = [
  { icon: '✂️', label: '智能抠图',  start: 0,  end: 50 },
  { icon: '🖼️', label: '合成海报',  start: 50, end: 65 },
  { icon: '🎨', label: '生成滤镜',  start: 65, end: 100 },
]

const stepClass = computed(() => {
  if (props.progress < 50)  return 'dot-blue'
  if (props.progress < 65)  return 'dot-orange'
  if (props.progress < 100) return 'dot-purple'
  return 'dot-green'
})

const tips = [
  '💡 小技巧：产品图背景越简单，抠图效果越好',
  '🌿 我们使用 AI 模型自动识别产品主体',
  '📐 建议上传正方形图片，合成效果最佳',
  '🎯 抠图完成后可选择 4 种滤镜风格',
  '✨ 暖调滤镜最适合农产品宣传哦',
]
const randomTip = ref(tips[Math.floor(Math.random() * tips.length)])
onMounted(() => {
  // 每5秒换一条提示
  setInterval(() => {
    randomTip.value = tips[Math.floor(Math.random() * tips.length)]
  }, 5000)
})
</script>

<style scoped>
.progress-card {
  background: linear-gradient(135deg, #f0f7e6 0%, #e8f5e9 100%);
  border: 1px solid #c5e1a5;
  border-radius: 16px;
  padding: 18px 20px;
  margin-bottom: 16px;
}

.progress-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 12px;
}
.progress-icon  { font-size: 18px; }
.progress-title { font-size: 15px; font-weight: 600; color: #2e7d32; flex: 1; }
.progress-pct   { font-size: 20px; font-weight: 700; color: #7dba28; min-width: 48px; text-align: right; }

/* 进度条 */
.progress-bar-track {
  height: 10px; background: rgba(255,255,255,0.7);
  border-radius: 10px; overflow: hidden; margin-bottom: 10px;
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
}
.progress-bar-fill {
  height: 100%; border-radius: 10px; position: relative; overflow: hidden;
  background: linear-gradient(90deg, #7dba28, #a5d633);
  transition: width 0.4s ease;
}
.progress-shimmer {
  position: absolute; inset: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.4) 50%, transparent 100%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }

/* 步骤文字 */
.progress-step {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: #555; margin-bottom: 14px;
}
.step-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
  animation: pulse 1s ease-in-out infinite;
}
.dot-blue   { background: #2196f3; }
.dot-orange { background: #ff9800; }
.dot-purple { background: #9c27b0; }
.dot-green  { background: #7dba28; animation: none; }
@keyframes pulse { 0%,100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(1.3); } }

/* 步骤气泡 */
.step-bubbles {
  display: flex; gap: 8px; margin-bottom: 12px;
}
.step-bubble {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 8px 6px; border-radius: 10px;
  font-size: 11px; transition: all 0.3s;
  border: 1px solid transparent;
}
.step-bubble.wait   { background: rgba(255,255,255,0.4); color: #aaa; }
.step-bubble.active { background: white; border-color: #7dba28; color: #2e7d32; font-weight: 600;
                      box-shadow: 0 2px 8px rgba(125,186,40,0.25); }
.step-bubble.done   { background: rgba(125,186,40,0.12); color: #51830a; }
.bubble-icon  { font-size: 18px; }
.bubble-label { white-space: nowrap; }

/* 提示 */
.progress-tip {
  font-size: 12px; color: #7dba28; text-align: center;
  padding: 6px 10px; background: rgba(255,255,255,0.5);
  border-radius: 8px; font-style: italic;
  transition: opacity 0.5s;
}
</style>
