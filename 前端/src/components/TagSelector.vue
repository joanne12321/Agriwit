<template>
  <div class="view-18" role="group" aria-label="已选择的标签">
    <!-- 平台 -->
    <div class="tag-button-container">
      <button class="view-24 tag-button" :data-tag-type="'platform'" @click.stop="toggleMenu('platform')">
        <span>{{ platformDisplay }}</span>
        <div class="selected-tags">{{ localSelected.platform.length }}</div>
      </button>
      <div class="tag-dropdown-popup" :class="{ active: activeMenu === 'platform' }">
        <div class="tag-dropdown-header">选择平台 (可多选)</div>
        <div class="tag-dropdown-options">
          <div v-for="opt in platformOptions" :key="opt.value" class="tag-dropdown-option" :class="{ selected: localSelected.platform.includes(opt.value) }" @click.stop="togglePlatform(opt.value)">
            <div class="checkbox"></div><span>{{ opt.label }}</span>
          </div>
        </div>
      </div>
    </div>
    <!-- 风格 -->
    <div class="tag-button-container">
      <button class="view-23 tag-button" :data-tag-type="'style'" @click.stop="toggleMenu('style')">
        <span>{{ getSingleDisplay('style') }}</span>
        <div class="selected-tags">{{ localSelected.style ? 1 : 0 }}</div>
      </button>
      <div class="tag-dropdown-popup" :class="{ active: activeMenu === 'style' }">
        <div class="tag-dropdown-header">选择风格</div>
        <div class="tag-dropdown-options">
          <div v-for="opt in styleOptions" :key="opt.value" class="tag-dropdown-option" :class="{ selected: localSelected.style === opt.value }" @click.stop="selectSingle('style', opt.value)">
            <div class="checkbox"></div><span>{{ opt.label }}</span>
          </div>
        </div>
      </div>
    </div>
    <!-- 节日 -->
    <div class="tag-button-container">
      <button class="view-22 tag-button" :data-tag-type="'festival'" @click.stop="toggleMenu('festival')">
        <span>{{ getSingleDisplay('festival') }}</span>
        <div class="selected-tags">{{ localSelected.festival ? 1 : 0 }}</div>
      </button>
      <div class="tag-dropdown-popup" :class="{ active: activeMenu === 'festival' }">
        <div class="tag-dropdown-header">选择节日</div>
        <div class="tag-dropdown-options">
          <div v-for="opt in festivalOptions" :key="opt.value" class="tag-dropdown-option" :class="{ selected: localSelected.festival === opt.value }" @click.stop="selectSingle('festival', opt.value)">
            <div class="checkbox"></div><span>{{ opt.label }}</span>
          </div>
        </div>
      </div>
    </div>
    <!-- 产品类型 -->
    <div class="tag-button-container">
      <button class="view-21 tag-button" :data-tag-type="'product-type'" @click.stop="toggleMenu('product-type')">
        <span>{{ getSingleDisplay('product-type') }}</span>
        <div class="selected-tags">{{ localSelected['product-type'] ? 1 : 0 }}</div>
      </button>
      <div class="tag-dropdown-popup" :class="{ active: activeMenu === 'product-type' }">
        <div class="tag-dropdown-header">选择产品类型</div>
        <div class="tag-dropdown-options">
          <div v-for="opt in productTypeOptions" :key="opt.value" class="tag-dropdown-option" :class="{ selected: localSelected['product-type'] === opt.value }" @click.stop="selectSingle('product-type', opt.value)">
            <div class="checkbox"></div><span>{{ opt.label }}</span>
          </div>
        </div>
      </div>
    </div>
    <!-- 目标用户 -->
    <div class="tag-button-container">
      <button class="view-20 tag-button" :data-tag-type="'target-user'" @click.stop="toggleMenu('target-user')">
        <span>{{ getSingleDisplay('target-user') }}</span>
        <div class="selected-tags">{{ localSelected['target-user'] ? 1 : 0 }}</div>
      </button>
      <div class="tag-dropdown-popup" :class="{ active: activeMenu === 'target-user' }">
        <div class="tag-dropdown-header">选择目标用户</div>
        <div class="tag-dropdown-options">
          <div v-for="opt in targetUserOptions" :key="opt.value" class="tag-dropdown-option" :class="{ selected: localSelected['target-user'] === opt.value }" @click.stop="selectSingle('target-user', opt.value)">
            <div class="checkbox"></div><span>{{ opt.label }}</span>
          </div>
        </div>
      </div>
    </div>
    <!-- 宣传场景 -->
    <div class="tag-button-container">
      <button class="view-19 tag-button" :data-tag-type="'promotion-scene'" @click.stop="toggleMenu('promotion-scene')">
        <span>{{ getSingleDisplay('promotion-scene') }}</span>
        <div class="selected-tags">{{ localSelected['promotion-scene'] ? 1 : 0 }}</div>
      </button>
      <div class="tag-dropdown-popup" :class="{ active: activeMenu === 'promotion-scene' }">
        <div class="tag-dropdown-header">选择宣传场景</div>
        <div class="tag-dropdown-options">
          <div v-for="opt in promotionSceneOptions" :key="opt.value" class="tag-dropdown-option" :class="{ selected: localSelected['promotion-scene'] === opt.value }" @click.stop="selectSingle('promotion-scene', opt.value)">
            <div class="checkbox"></div><span>{{ opt.label }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: Object
})
const emit = defineEmits(['update:modelValue'])

const localSelected = ref({ ...props.modelValue })
watch(() => props.modelValue, (val) => {
  localSelected.value = { ...val }
}, { deep: true })
watch(localSelected, (val) => {
  emit('update:modelValue', { ...val })
}, { deep: true })

const activeMenu = ref(null)

const platformOptions = [
  { value: 'taobao', label: '淘宝' },
  { value: 'douyin', label: '抖音' },
  { value: 'xiaohongshu', label: '小红书' },
  { value: 'weibo', label: '微博' },
  { value: 'toutiao', label: '头条' }
]
const styleOptions = [
  { value: 'modern', label: '现代科技' },
  { value: 'minimalist', label: '极简主义' },
  { value: 'traditional', label: '传统中式' },
  { value: 'vintage', label: '复古风' },
  { value: 'fresh', label: '清新自然' }
]
const festivalOptions = [
  { value: 'spring-festival', label: '春节' },
  { value: 'mid-autumn', label: '中秋节' },
  { value: 'national-day', label: '国庆节' },
  { value: 'dragon-boat', label: '端午节' },
  { value: 'qixi', label: '七夕节' }
]
const productTypeOptions = [
  { value: 'electronics', label: '电子产品' },
  { value: 'clothing', label: '服装服饰' },
  { value: 'food', label: '食品饮料' },
  { value: 'agricultural', label: '农产品' },
  { value: 'cosmetics', label: '美妆个护' }
]
const targetUserOptions = [
  { value: 'young', label: '年轻人' },
  { value: 'middle-aged', label: '中年人' },
  { value: 'elderly', label: '老年人' },
  { value: 'female', label: '女性用户' },
  { value: 'family', label: '家庭用户' }
]
const promotionSceneOptions = [
  { value: 'launch', label: '新品发布' },
  { value: 'promotion', label: '促销活动' },
  { value: 'brand', label: '品牌宣传' },
  { value: 'festival', label: '节日营销' },
  { value: 'anniversary', label: '周年庆典' }
]

const toggleMenu = (type) => {
  activeMenu.value = activeMenu.value === type ? null : type
}

const togglePlatform = (value) => {
  const idx = localSelected.value.platform.indexOf(value)
  if (idx > -1) localSelected.value.platform.splice(idx, 1)
  else localSelected.value.platform.push(value)
}

const selectSingle = (type, value) => {
  localSelected.value[type] = localSelected.value[type] === value ? '' : value
  activeMenu.value = null
}

const platformDisplay = computed(() => {
  const count = localSelected.value.platform.length
  if (count === 0) return '平台'
  if (count === 1) {
    const opt = platformOptions.find(o => o.value === localSelected.value.platform[0])
    return opt ? opt.label : '平台'
  }
  return `平台 (${count})`
})

const getSingleDisplay = (type) => {
  const val = localSelected.value[type]
  if (!val) {
    const map = {
      style: '风格',
      festival: '节日',
      'product-type': '产品类型',
      'target-user': '目标用户',
      'promotion-scene': '宣传场景'
    }
    return map[type]
  }
  let options = []
  if (type === 'style') options = styleOptions
  else if (type === 'festival') options = festivalOptions
  else if (type === 'product-type') options = productTypeOptions
  else if (type === 'target-user') options = targetUserOptions
  else if (type === 'promotion-scene') options = promotionSceneOptions
  const opt = options.find(o => o.value === val)
  return opt ? opt.label : ''
}
</script>

<style scoped>
/* ===== 标签区域样式 (原 .view-18 已在父组件中定位) ===== */
.view-18 {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: visible;
  flex-wrap: nowrap;
}

.tag-button-container {
  position: relative;
  display: inline-block;
  flex-shrink: 0;
}

.view-19, .view-20, .view-21, .view-22, .view-23, .view-24, .tag-button {
  flex-shrink: 0;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f5e6;
  border: none;
  cursor: pointer;
  transition: all 0.3s;
  font-family: "Inter", Helvetica;
  font-weight: 500;
  color: #51830a;
  font-size: 14px;
  border-radius: 8px;
  padding: 0 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  white-space: nowrap;
  position: relative;
  overflow: visible;
}

.view-19:hover, .view-20:hover, .view-21:hover, .view-22:hover, .view-23:hover, .view-24:hover, .tag-button:hover {
  background-color: #7dba28;
  color: #ffffff;
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(125,186,40,0.3);
}

.selected-tags {
  position: absolute;
  top: -6px;
  right: -6px;
  background-color: #7dba28;
  color: white;
  font-size: 10px;
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 3px;
  z-index: 3;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

/* 下拉菜单 */
.tag-dropdown-popup {
  position: absolute;
  bottom: 100%;
  left: 0;
  transform: translateY(-8px);
  width: 190px;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 12px 28px rgba(0,0,0,0.2), 0 4px 10px rgba(0,0,0,0.1);
  padding: 8px 0;
  z-index: 1200;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s, visibility 0.2s;
  border: 1px solid #e0e0e0;
}

.tag-dropdown-popup.active {
  opacity: 1;
  visibility: visible;
}

.tag-dropdown-popup::before {
  content: '';
  position: absolute;
  bottom: -6px;
  left: 20px;
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 6px solid #ffffff;
  z-index: 1201;
  filter: drop-shadow(0 2px 2px rgba(0,0,0,0.1));
}

.tag-dropdown-popup::after {
  content: '';
  position: absolute;
  bottom: -7px;
  left: 19px;
  width: 0;
  height: 0;
  border-left: 7px solid transparent;
  border-right: 7px solid transparent;
  border-top: 7px solid #e0e0e0;
  z-index: 1200;
}

.tag-dropdown-header {
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #888;
  border-bottom: 1px solid #f0f0f0;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.tag-dropdown-options {
  display: flex;
  flex-direction: column;
}

.tag-dropdown-option {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  color: #333;
  border-left: 3px solid transparent;
}

.tag-dropdown-option:hover {
  background-color: rgba(125,186,40,0.08);
  border-left-color: #7dba28;
  padding-left: 19px;
}

.tag-dropdown-option.selected {
  background-color: rgba(125,186,40,0.1);
  color: #51830a;
  font-weight: 500;
  border-left-color: #7dba28;
}

.tag-dropdown-option .checkbox {
  width: 16px;
  height: 16px;
  border: 2px solid #ccc;
  border-radius: 4px;
  margin-right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tag-dropdown-option.selected .checkbox {
  background-color: #7dba28;
  border-color: #7dba28;
}

.tag-dropdown-option.selected .checkbox::after {
  content: '✓';
  color: white;
  font-size: 12px;
  font-weight: bold;
}
</style>