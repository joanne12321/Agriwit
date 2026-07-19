<template>
  <main class="view-8">
    <!-- 顶部搜索栏 -->
    <div class="top-bar">
      <div class="search-container">
        <div class="search-box">
          <i data-feather="search" class="search-icon"></i>
          <input type="text" class="search-input" placeholder="搜索..." aria-label="搜索" v-model="searchText" @keyup.enter="handleSearch">
        </div>
      </div>
      
      <div class="member-container">
        <div class="member-count">
          <i data-feather="users" class="member-icon"></i>
          <span class="member-text">+10</span>
        </div>
        <!-- 根据登录状态显示不同内容 -->
        <button v-if="!user" class="login-btn" aria-label="登录/注册" @click="openAuthModal">登录/注册</button>
        <div v-else class="user-info">
          <span class="user-id">{{ user.id || user.username || '用户' }}</span>
        </div>
      </div>
    </div>
    
    <!-- 主要内容网格 -->
    <div class="main-grid">
      <!-- 产品输入区域 -->
      <div class="grid-item product-input-container">
        <h2 class="section-title">快速开始</h2>
        
        <div class="input-card" role="button" tabindex="0" @click="inputProduct">
          <div class="input-text">产品输入 > </div>
        </div>
        
        <button class="start-creating-btn" aria-label="进入创作" @click="goToCreation">进入创作</button>
        
        <div class="tags-container">
          <!-- 平台标签 -->
          <div class="tag-header" :class="{ selected: selectedTags.platform.length > 0 }" ref="platformHeader" @click.stop="toggleDropdown('platform')">
            <span ref="platformLabel">平台</span>
            <i data-feather="chevron-down" class="tag-arrow" :style="{ transform: activeDropdown === 'platform' ? 'rotate(180deg)' : 'rotate(0deg)' }"></i>
            <div class="tag-dropdown-menu" :class="{ active: activeDropdown === 'platform' }" ref="platformDropdown">
              <div class="tag-dropdown-header">选择平台 (可多选)</div>
              <div class="tag-dropdown-options">
                <div class="tag-dropdown-option" v-for="opt in platformOptions" :key="opt.value" :class="{ selected: selectedTags.platform.includes(opt.value) }" @click.stop="togglePlatformOption(opt.value)">
                  <div class="checkbox"></div>
                  <span>{{ opt.label }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 风格标签 -->
          <div class="tag-row" :class="{ selected: selectedTags.style }" @click.stop="toggleDropdown('style')">
            <div class="tag-label" ref="styleLabel">风格</div>
            <i data-feather="chevron-right" class="tag-arrow" :style="{ transform: activeDropdown === 'style' ? 'rotate(90deg)' : 'rotate(0deg)' }"></i>
            <div class="tag-dropdown-menu" :class="{ active: activeDropdown === 'style' }" ref="styleDropdown">
              <div class="tag-dropdown-header">选择风格</div>
              <div class="tag-dropdown-options">
                <div class="tag-dropdown-option" v-for="opt in styleOptions" :key="opt.value" :class="{ selected: selectedTags.style === opt.value }" @click.stop="selectSingleTag('style', opt.value)">
                  <div class="checkbox"></div>
                  <span>{{ opt.label }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 节日标签 -->
          <div class="tag-row" :class="{ selected: selectedTags.festival }" @click.stop="toggleDropdown('festival')">
            <div class="tag-label" ref="festivalLabel">节日</div>
            <i data-feather="chevron-right" class="tag-arrow" :style="{ transform: activeDropdown === 'festival' ? 'rotate(90deg)' : 'rotate(0deg)' }"></i>
            <div class="tag-dropdown-menu" :class="{ active: activeDropdown === 'festival' }" ref="festivalDropdown">
              <div class="tag-dropdown-header">选择节日</div>
              <div class="tag-dropdown-options">
                <div class="tag-dropdown-option" v-for="opt in festivalOptions" :key="opt.value" :class="{ selected: selectedTags.festival === opt.value }" @click.stop="selectSingleTag('festival', opt.value)">
                  <div class="checkbox"></div>
                  <span>{{ opt.label }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 产品类型标签 -->
          <div class="tag-row" :class="{ selected: selectedTags.productType }" @click.stop="toggleDropdown('productType')">
            <div class="tag-label" ref="productTypeLabel">产品类型</div>
            <i data-feather="chevron-right" class="tag-arrow" :style="{ transform: activeDropdown === 'productType' ? 'rotate(90deg)' : 'rotate(0deg)' }"></i>
            <div class="tag-dropdown-menu" :class="{ active: activeDropdown === 'productType' }" ref="productTypeDropdown">
              <div class="tag-dropdown-header">选择产品类型</div>
              <div class="tag-dropdown-options">
                <div class="tag-dropdown-option" v-for="opt in productTypeOptions" :key="opt.value" :class="{ selected: selectedTags.productType === opt.value }" @click.stop="selectSingleTag('productType', opt.value)">
                  <div class="checkbox"></div>
                  <span>{{ opt.label }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 目标用户标签 -->
          <div class="tag-row" :class="{ selected: selectedTags.targetUser }" @click.stop="toggleDropdown('targetUser')">
            <div class="tag-label" ref="targetUserLabel">目标用户</div>
            <i data-feather="chevron-right" class="tag-arrow" :style="{ transform: activeDropdown === 'targetUser' ? 'rotate(90deg)' : 'rotate(0deg)' }"></i>
            <div class="tag-dropdown-menu" :class="{ active: activeDropdown === 'targetUser' }" ref="targetUserDropdown">
              <div class="tag-dropdown-header">选择目标用户</div>
              <div class="tag-dropdown-options">
                <div class="tag-dropdown-option" v-for="opt in targetUserOptions" :key="opt.value" :class="{ selected: selectedTags.targetUser === opt.value }" @click.stop="selectSingleTag('targetUser', opt.value)">
                  <div class="checkbox"></div>
                  <span>{{ opt.label }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 宣传场景标签 -->
          <div class="tag-row" :class="{ selected: selectedTags.promotionScene }" @click.stop="toggleDropdown('promotionScene')">
            <div class="tag-label" ref="promotionSceneLabel">宣传场景</div>
            <i data-feather="chevron-right" class="tag-arrow" :style="{ transform: activeDropdown === 'promotionScene' ? 'rotate(90deg)' : 'rotate(0deg)' }"></i>
            <div class="tag-dropdown-menu" :class="{ active: activeDropdown === 'promotionScene' }" ref="promotionSceneDropdown">
              <div class="tag-dropdown-header">选择宣传场景</div>
              <div class="tag-dropdown-options">
                <div class="tag-dropdown-option" v-for="opt in promotionSceneOptions" :key="opt.value" :class="{ selected: selectedTags.promotionScene === opt.value }" @click.stop="selectSingleTag('promotionScene', opt.value)">
                  <div class="checkbox"></div>
                  <span>{{ opt.label }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 轮播图区域 -->
      <div class="grid-item carousel-container">
        <div class="carousel-bg"></div>
        <div class="carousel-content">
          <div>
            <h2 class="carousel-title">{{ slides[currentSlide].title }}</h2>
            <p class="carousel-subtitle">{{ slides[currentSlide].subtitle }}</p>
          </div>
          
          <div class="carousel-feature">
            <h3 class="feature-title">功能轮播</h3>
            <p class="feature-desc">动态播放：展示一些优秀的产品案例或者播放素材库好看的模板</p>
          </div>
        </div>
      </div>
      
      <!-- 营销日历 -->
      <div class="grid-item calendar-container">
        <h2 class="section-title">营销日历</h2>
        <div class="calendar-content">
          <div class="calendar-header">
            <button class="calendar-nav-btn prev-month" aria-label="上个月" @click="prevMonth">
              <i data-feather="chevron-left"></i>
            </button>
            <div class="calendar-month-year">{{ currentYear }}年{{ currentMonth + 1 }}月</div>
            <button class="calendar-nav-btn next-month" aria-label="下个月" @click="nextMonth">
              <i data-feather="chevron-right"></i>
            </button>
          </div>
          
          <div class="calendar-weekdays">
            <div class="calendar-weekday">日</div>
            <div class="calendar-weekday">一</div>
            <div class="calendar-weekday">二</div>
            <div class="calendar-weekday">三</div>
            <div class="calendar-weekday">四</div>
            <div class="calendar-weekday">五</div>
            <div class="calendar-weekday">六</div>
          </div>
          
          <div class="calendar-days">
            <div v-for="(day, index) in calendarDays" :key="index" 
                 class="calendar-day" 
                 :class="{ empty: !day, today: day && isToday(day), selected: selectedDate === day }"
                 @click="selectDate(day)">
              {{ day || '' }}
              <div v-if="day && marketingEvents[`${currentYear}-${currentMonth+1}-${day}`]" class="calendar-marketing-event" :title="marketingEvents[`${currentYear}-${currentMonth+1}-${day}`]"></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 近期热点 -->
      <div class="grid-item hot-news-container">
        <div class="hot-news-header">
          <h2 class="section-title">近期热点</h2>
          <span class="view-more" role="button" tabindex="0" @click="viewMore">查看更多</span>
        </div>
        
        <div class="hot-news-grid">
          <div class="news-card" v-for="(news, idx) in hotNews" :key="idx">
            <div class="placeholder-image" style="height: 106px;">{{ news.imgText }}</div>
            <div class="news-content">
              <p>{{ news.title }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 近期话题榜 -->
      <div class="grid-item topics-container">
        <div class="topics-header">近期话题榜</div>
        <div class="topics-list">
          <div class="topic-item" v-for="(topic, index) in topics" :key="index" :class="`rank-${index+1}`" @click="viewTopic(topic)">
            <div class="topic-rank">{{ index+1 }}</div>
            <div class="topic-content">
              <div class="topic-title">{{ topic.title }}</div>
              <div class="topic-stats">{{ topic.stats }}</div>
            </div>
            <span v-if="topic.tag" class="topic-tag" :class="topic.tagClass">{{ topic.tag }}</span>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick, inject } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
// 注入打开登录模态框的方法
const openAuthModal = inject('openAuthModal')
const user = inject('user')

// 搜索
const searchText = ref('')
const handleSearch = () => {
  if (searchText.value.trim()) {
    alert(`搜索：${searchText.value}`)
  }
}

// 产品输入
const inputProduct = () => {
  const productName = prompt('请输入产品名称：', '新产品')
  if (productName && productName.trim()) {
    alert(`已输入产品：${productName}`)
  }
}

// 进入创作
const goToCreation = () => {
  router.push('/creation')
}

// 标签数据
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

const selectedTags = reactive({
  platform: [],
  style: '',
  festival: '',
  productType: '',
  targetUser: '',
  promotionScene: ''
})

const activeDropdown = ref(null)

// 关闭所有下拉菜单
const closeAllDropdowns = () => {
  activeDropdown.value = null
}

// 切换下拉菜单
const toggleDropdown = (type) => {
  if (activeDropdown.value === type) {
    closeAllDropdowns()
  } else {
    activeDropdown.value = type
  }
}

// 平台多选
const togglePlatformOption = (value) => {
  const index = selectedTags.platform.indexOf(value)
  if (index > -1) {
    selectedTags.platform.splice(index, 1)
  } else {
    selectedTags.platform.push(value)
  }
  updatePlatformLabel()
}

// 单选标签
const selectSingleTag = (type, value) => {
  if (selectedTags[type] === value) {
    selectedTags[type] = ''
  } else {
    selectedTags[type] = value
  }
  closeAllDropdowns()
}

// 更新平台标签显示
const updatePlatformLabel = () => {
  nextTick(() => {
    if (window.feather) window.feather.replace()
  })
}

// 处理文档点击关闭下拉菜单
const handleDocumentClick = (e) => {
  const isTagElement = e.target.closest('.tag-header') || e.target.closest('.tag-row') || e.target.closest('.tag-dropdown-menu')
  if (!isTagElement) {
    closeAllDropdowns()
  }
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
  if (window.feather) window.feather.replace()
})

onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick)
})

// 轮播
const slides = [
  { title: "用AI讲好乡村故事", subtitle: "智能生成农产品文案" },
  { title: "方言智能识别", subtitle: "支持多种方言的智能翻译" },
  { title: "营销素材库", subtitle: "海量模板一键生成" }
]
const currentSlide = ref(0)
let slideInterval
onMounted(() => {
  slideInterval = setInterval(() => {
    currentSlide.value = (currentSlide.value + 1) % slides.length
  }, 5000)
})
onUnmounted(() => {
  clearInterval(slideInterval)
})

// 日历
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth())
const selectedDate = ref(null)

const marketingEvents = {
  '2024-6-10': '端午节营销活动',
  '2024-6-18': '618促销',
  '2024-6-1': '儿童节活动',
  '2024-6-15': '农产品直播'
}

const calendarDays = computed(() => {
  const firstDay = new Date(currentYear.value, currentMonth.value, 1)
  const lastDay = new Date(currentYear.value, currentMonth.value + 1, 0)
  const totalDays = lastDay.getDate()
  const firstDayIndex = firstDay.getDay()
  
  const days = []
  for (let i = 0; i < firstDayIndex; i++) days.push(null)
  for (let i = 1; i <= totalDays; i++) days.push(i)
  while (days.length < 42) days.push(null)
  return days
})

const isToday = (day) => {
  const today = new Date()
  return today.getFullYear() === currentYear.value && today.getMonth() === currentMonth.value && today.getDate() === day
}

const selectDate = (day) => {
  if (!day) return
  selectedDate.value = day
  const event = marketingEvents[`${currentYear.value}-${currentMonth.value+1}-${day}`]
  if (event) {
    alert(`${currentYear.value}年${currentMonth.value+1}月${day}日: ${event}`)
  } else {
    alert(`已选择日期: ${currentYear.value}年${currentMonth.value+1}月${day}日`)
  }
}

const prevMonth = () => {
  if (currentMonth.value === 0) {
    currentYear.value--
    currentMonth.value = 11
  } else {
    currentMonth.value--
  }
  selectedDate.value = null
}

const nextMonth = () => {
  if (currentMonth.value === 11) {
    currentYear.value++
    currentMonth.value = 0
  } else {
    currentMonth.value++
  }
  selectedDate.value = null
}

// 近期热点
const hotNews = [
  { imgText: '热点图片1', title: '端午节农产品营销趋势分析' },
  { imgText: '热点图片2', title: '乡村文旅如何利用短视频推广' },
  { imgText: '热点图片3', title: 'AI生成文案在农产品电商中的应用' }
]

const viewMore = () => {
  alert('查看更多热点新闻')
}

// 话题榜
const topics = [
  { title: '农产品电商直播带货', stats: '热度 120万', tag: '热', tagClass: 'hot' },
  { title: '乡村文旅品牌打造', stats: '热度 98万', tag: '新', tagClass: 'new' },
  { title: 'AI智能营销方案', stats: '热度 85万', tag: '' },
  { title: '端午节营销策略', stats: '热度 72万', tag: '' },
  { title: '方言直播技巧', stats: '热度 65万', tag: '' },
  { title: '乡村特产包装设计', stats: '热度 58万', tag: '' }
]

const viewTopic = (topic) => {
  alert(`查看话题详情: ${topic.title}`)
}

// 按钮涟漪效果
const createRipple = (event) => {
  const button = event.currentTarget
  const ripple = document.createElement('span')
  const rect = button.getBoundingClientRect()
  const size = Math.max(rect.width, rect.height)
  const x = event.clientX - rect.left - size / 2
  const y = event.clientY - rect.top - size / 2

  ripple.style.cssText = `
    position: absolute;
    border-radius: 50%;
    background: rgba(125, 186, 40, 0.4);
    transform: scale(0);
    animation: ripple-animation 0.7s ease-out;
    width: ${size}px;
    height: ${size}px;
    top: ${y}px;
    left: ${x}px;
    pointer-events: none;
    z-index: 1;
  `

  const computedStyle = window.getComputedStyle(button)
  if (computedStyle.position === 'static') {
    button.style.position = 'relative'
  }
  if (computedStyle.overflow !== 'hidden') {
    button.style.overflow = 'hidden'
  }

  button.appendChild(ripple)
  setTimeout(() => {
    ripple.remove()
  }, 700)
}

onMounted(() => {
  const buttons = document.querySelectorAll('button')
  buttons.forEach(btn => {
    btn.addEventListener('click', createRipple)
  })
})

onUnmounted(() => {
  const buttons = document.querySelectorAll('button')
  buttons.forEach(btn => {
    btn.removeEventListener('click', createRipple)
  })
})

// 监听selectedTags变化，更新标签显示
watch(selectedTags, () => {
  nextTick(() => {
    if (window.feather) window.feather.replace()
  })
}, { deep: true })
</script>

<style scoped>

.view-8 {
  position: absolute;
  top: 0;
  left: 258px;
  width: calc(100% - 258px);
  min-width: 1182px;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 30px 40px;
  overflow-y: auto;
}

.top-bar {
  width: 100%;
  height: 146px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.search-container {
  width: 658px;
  height: 114px;
  display: flex;
  align-items: center;
}

.search-box {
  width: 603px;
  height: 59px;
  background: white;
  border-radius: 10px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.search-box:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
}

.search-icon {
  width: 32px;
  height: 32px;
  color: #4A4A4A;
  margin-right: 15px;
}

.search-input {
  flex: 1;
  height: 100%;
  border: none;
  background: transparent;
  font-family: "Inter", Helvetica;
  font-weight: 400;
  color: rgba(0, 0, 0, 0.7);
  font-size: 18px;
  outline: none;
}

.search-input::placeholder {
  color: rgba(0, 0, 0, 0.4);
}

.member-container {
  width: 303px;
  height: 101px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.member-count {
  display: flex;
  align-items: center;
  background: white;
  border-radius: 10px;
  padding: 0 15px;
  height: 56px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.member-icon {
  width: 40px;
  height: 40px;
  color: #2F5800;
  margin-right: 10px;
}

.member-text {
  font-family: "Inter", Helvetica;
  font-weight: 400;
  color: #4A4A4A;
  font-size: 20px;
}

/* 登录/注册按钮样式 */
.login-btn {
  width: 135px;
  height: 59px;
  background: #7EBA29;
  border-radius: 4px;
  border: none;
  color: white;
  font-family: "Inter", Helvetica;
  font-weight: 400;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(126, 186, 41, 0.3);
}

.login-btn:hover {
  background: #6aa11e;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(126, 186, 41, 0.4);
}

.main-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 20px;
  flex: 1;
}

.grid-item {
  background: white;
  border-radius: 10px;
  box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
}

.grid-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

/* 产品输入区域 */
.product-input-container {
  grid-column: 1;
  grid-row: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  position: relative;
}

.section-title {
  font-family: "Inter", Helvetica;
  font-weight: 300;
  color: black;
  font-size: 32px;
  margin-bottom: 20px;
}

.input-card {
  background: #EEEEEE;
  border-radius: 10px;
  border: 1px solid rgba(77, 77, 77, 0.45);
  padding: 10px 21px;
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.input-card:hover {
  background: #e5e5e5;
  transform: translateX(5px);
}

.input-text {
  font-family: "Inter", Helvetica;
  font-weight: 400;
  color: #848484;
  font-size: 16px;
}

.start-creating-btn {
  width: 131px;
  height: 44px;
  background: #7EBA29;
  border-radius: 5px;
  border: none;
  color: white;
  font-family: "Inter", Helvetica;
  font-weight: 600;
  font-size: 21px;
  cursor: pointer;
  transition: all 0.3s ease;
  align-self: flex-end;
  box-shadow: 2px 2px 8px rgba(126, 186, 41, 0.3);
}

.start-creating-btn:hover {
  background: #6aa11e;
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(126, 186, 41, 0.4);
}

.tags-container {
  background: white;
  border-radius: 11px;
  box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.1);
  margin-top: 20px;
  position: relative;
}

.tag-header {
  background: #7EBA29;
  color: white;
  font-family: "Inter", Helvetica;
  font-weight: 400;
  font-size: 16px;
  padding: 10px 24px;
  cursor: pointer;
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s ease;
  z-index: 10;
}

.tag-header:hover {
  background: #6aa11e;
}

.tag-header.selected {
  background-color: rgba(125, 186, 40, 0.1);
  color: #51830a;
}

.tag-header.selected .tag-arrow {
  color: #7dba28;
}

.tag-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 24px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
  z-index: 10;
}

.tag-row:hover {
  background: #f9fafb;
}

.tag-row:last-child {
  border-bottom: none;
}

.tag-row.selected {
  background-color: rgba(125, 186, 40, 0.1);
  color: #51830a;
  font-weight: 500;
}

.tag-row.selected .tag-label {
  color: #51830a;
}

.tag-row.selected .tag-arrow {
  color: #7dba28;
}

.tag-label {
  font-family: "Inter", Helvetica;
  font-weight: 400;
  color: #2C4707;
  font-size: 16px;
  flex: 1;
  transition: color 0.2s ease;
}

.tag-arrow {
  color: rgba(87, 87, 87, 0.6);
  width: 28px;
  height: 17px;
  transition: transform 0.3s ease, color 0.2s ease;
}

.tag-dropdown-menu {
  position: absolute;
  bottom: 100%;
  left: 0;
  width: 100%;
  background: white;
  border-radius: 8px 8px 0 0;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  padding: 0;
  opacity: 0;
  visibility: hidden;
  transform: translateY(10px);
  transition: all 0.3s ease;
  max-height: 220px;
  overflow-y: auto;
  border: 1px solid #f0f0f0;
  border-bottom: none;
}

.tag-dropdown-menu.active {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.tag-dropdown-menu::-webkit-scrollbar {
  width: 6px;
}

.tag-dropdown-menu::-webkit-scrollbar-track {
  background: #f5f5f5;
  border-radius: 3px;
}

.tag-dropdown-menu::-webkit-scrollbar-thumb {
  background: rgba(125, 186, 40, 0.5);
  border-radius: 3px;
}

.tag-dropdown-header {
  padding: 8px 16px;
  font-family: "Inter", Helvetica;
  font-size: 14px;
  font-weight: 500;
  color: #666;
  background: #f9f9f9;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 0;
  position: sticky;
  top: 0;
  z-index: 1;
}

.tag-dropdown-options {
  max-height: 180px;
  overflow-y: auto;
}

.tag-dropdown-option {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: "Inter", Helvetica;
  font-size: 14px;
  color: #333;
  border-bottom: 1px solid #f8f8f8;
}

.tag-dropdown-option:last-child {
  border-bottom: none;
}

.tag-dropdown-option:hover {
  background-color: rgba(125, 186, 40, 0.1);
}

.tag-dropdown-option.selected {
  background-color: rgba(125, 186, 40, 0.2);
  color: #51830a;
  font-weight: 500;
}

.tag-dropdown-option .checkbox {
  width: 16px;
  height: 16px;
  border: 2px solid #ccc;
  border-radius: 4px;
  margin-right: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
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

/* 轮播图 */
.carousel-container {
  grid-column: 2 / 4;
  grid-row: 1;
  background: linear-gradient(135deg, #355309 0%, #7dba28 100%);
  position: relative;
  overflow: hidden;
}

.carousel-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: url('https://placehold.co/2572x1450') center/cover no-repeat;
  opacity: 0.3;
}

.carousel-content {
  position: relative;
  z-index: 1;
  padding: 40px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.carousel-title {
  color: white;
  font-family: "Inter", Helvetica;
  font-size: 45px;
  font-weight: 600;
  line-height: 1.2;
  margin-bottom: 10px;
  transition: opacity 0.3s;
}

.carousel-subtitle {
  color: white;
  font-family: "Inter", Helvetica;
  font-size: 30px;
  font-weight: 500;
  opacity: 0.9;
  transition: opacity 0.3s;
}

.carousel-feature {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 14px;
  padding: 20px;
  max-width: 412px;
  margin-top: 20px;
}

.feature-title {
  color: white;
  font-family: "Inter", Helvetica;
  font-size: 30px;
  font-weight: 600;
  margin-bottom: 10px;
}

.feature-desc {
  color: rgba(255, 255, 255, 0.9);
  font-family: "Inter", Helvetica;
  font-size: 15px;
  font-weight: 400;
  line-height: 1.5;
}

/* 营销日历 */
.calendar-container {
  grid-column: 1;
  grid-row: 2;
  background: #DFDFDF;
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.calendar-content {
  background: white;
  border-radius: 10px;
  box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.1);
  flex: 1;
  overflow: hidden;
  position: relative;
  padding: 15px;
  display: flex;
  flex-direction: column;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.calendar-nav-btn {
  background: #7EBA29;
  border: none;
  color: white;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.calendar-nav-btn:hover {
  background: #6aa11e;
  transform: scale(1.1);
}

.calendar-month-year {
  font-family: "Inter", Helvetica;
  font-weight: 600;
  font-size: 18px;
  color: #333;
}

.calendar-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  margin-bottom: 10px;
}

.calendar-weekday {
  font-family: "Inter", Helvetica;
  font-weight: 500;
  font-size: 14px;
  color: #666;
  padding: 5px 0;
}

.calendar-days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 5px;
  flex: 1;
}

.calendar-day {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: "Inter", Helvetica;
  font-size: 14px;
  cursor: pointer;
  border-radius: 5px;
  transition: all 0.2s ease;
  position: relative;
}

.calendar-day:hover {
  background: rgba(125, 186, 40, 0.1);
}

.calendar-day.empty {
  visibility: hidden;
}

.calendar-day.today {
  background: #7EBA29;
  color: white;
  font-weight: 600;
}

.calendar-day.selected {
  background: rgba(125, 186, 40, 0.2);
  color: #51830a;
  font-weight: 600;
}

.calendar-marketing-event {
  position: absolute;
  bottom: 2px;
  left: 50%;
  transform: translateX(-50%);
  width: 4px;
  height: 4px;
  background: #ff6b6b;
  border-radius: 50%;
}

/* 近期热点 */
.hot-news-container {
  grid-column: 2;
  grid-row: 2;
  background: #DFDFDF;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.hot-news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.view-more {
  color: #848484;
  font-family: "Inter", Helvetica;
  font-weight: 400;
  font-size: 20px;
  text-decoration: underline;
  cursor: pointer;
  transition: all 0.2s ease;
}

.view-more:hover {
  color: #7dba28;
}

.hot-news-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 15px;
  flex: 1;
}

.news-card {
  background: white;
  border-radius: 5px;
  box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.1);
  border: 1.5px solid #B7B7B7;
  overflow: hidden;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.news-card:hover {
  transform: translateY(-5px);
  border-color: #7dba28;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

.news-image {
  width: 100%;
  height: 106px;
  background: #ECECEC;
  object-fit: cover;
  flex-shrink: 0;
}

.news-content {
  padding: 15px;
  flex: 1;
  display: flex;
  align-items: center;
}

.news-content p {
  font-family: "Inter", Helvetica;
  font-weight: 500;
  color: #333;
  font-size: 16px;
  margin: 0;
  line-height: 1.4;
}

/* 话题榜 */
.topics-container {
  grid-column: 3;
  grid-row: 2;
  background: white;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.topics-header {
  background: #f0f0f0;
  color: #333;
  font-family: "Inter", Helvetica;
  font-weight: 600;
  font-size: 22px;
  text-align: center;
  padding: 15px 0;
  border-bottom: 1px solid #e0e0e0;
}

.topics-list {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.topic-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  margin: 0;
  border-bottom: 1px solid #f0f0f0;
  background: #ffffff;
  transition: all 0.2s ease;
  cursor: pointer;
  position: relative;
}

.topic-item:hover {
  background: #f8f9fa;
}

.topic-item:last-child {
  border-bottom: none;
}

.topic-rank {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  color: #999;
  font-size: 16px;
  font-weight: 700;
  margin-right: 12px;
  flex-shrink: 0;
}

.topic-item.rank-1 .topic-rank {
  color: #ff3b30;
}

.topic-item.rank-2 .topic-rank {
  color: #ff9500;
}

.topic-item.rank-3 .topic-rank {
  color: #ffcc00;
}

.topic-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.topic-title {
  font-family: "Inter", Helvetica;
  font-weight: 500;
  color: #333;
  font-size: 15px;
  line-height: 1.4;
  margin-bottom: 4px;
}

.topic-stats {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.topic-tag {
  display: inline-block;
  padding: 2px 6px;
  background: #f0f0f0;
  color: #666;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 500;
  margin-left: 8px;
}

.topic-tag.hot {
  background: #ffebe6;
  color: #ff3b30;
}

.topic-tag.new {
  background: #e6f2ff;
  color: #007aff;
}

/* 占位图片样式 */
.placeholder-image {
  width: 100%;
  height: 100%;
  background: linear-gradient(45deg, #f0f5e6 25%, #ffffff 50%, #f0f5e6 75%);
  background-size: 200% 200%;
  animation: shimmer 2s infinite linear;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7dba28;
  font-family: "Inter", Helvetica;
  font-weight: 500;
  font-size: 18px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 涟漪动画 */
@keyframes ripple-animation {
  to {
    transform: scale(4);
    opacity: 0;
  }
}

/* 响应式调整 */
@media (max-width: 1600px) {
  .view-8 {
    min-width: 1200px;
  }
  
  .carousel-title {
    font-size: 36px;
  }
  
  .carousel-subtitle {
    font-size: 24px;
  }
}
/* 用户信息显示样式 */
.user-info {
  height: 59px;
  display: flex;
  align-items: center;
  background: #f0f5e6;
  border-radius: 4px;
  padding: 0 20px;
  border: 1px solid #7dba28;
}

.user-id {
  font-family: "Inter", Helvetica;
  font-weight: 500;
  color: #51830a;
  font-size: 18px;
}
</style>