<template>
  <div class="creation-wrapper">
    <main class="view-8" :class="{ submitted: submitted }" ref="mainContent">

      <!-- ===== 初始状态 ===== -->
      <div v-if="!submitted" class="initial-content">
        <div class="welcome-title">欢迎来到云稼集·AgriWit</div>

        <section class="view-16">

          <!-- 左上：选择背景模板按钮 -->
          <button class="view-25" type="button" @click="templateModalOpen = true">
            <img v-if="templateThumbnail" :src="templateThumbnail" class="thumbnail-preview" alt="已选模板" />
            <div v-else class="btn-inner-hint">
              <span class="text-wrapper-17">+</span>
              <span class="btn-label">背景模板</span>
            </div>
            <div v-if="selectedTemplate" class="selected-badge">✓</div>
          </button>

          <!-- 左下：上传产品图按钮 -->
          <button class="view-17" type="button" @click="triggerFileUpload">
            <img v-if="uploadedImagePreview" :src="uploadedImagePreview" class="thumbnail-preview round-preview" alt="已上传" />
            <div v-else class="btn-inner-hint-round">
              <span class="text-wrapper-14">+</span>
            </div>
            <div v-if="uploadedImagePreview" class="selected-badge">✓</div>
          </button>
          <input type="file" ref="fileInput" style="display:none;" accept="image/*" @change="handleFileUpload" />

          <!-- 填空容器 -->
          <div class="fill-container">
            请为您的宣传内容选择一个
            <span class="tag-fill-container">
              <button class="fill-btn" :class="{ selected: selectedTags.platform.length > 0 }" @click.stop="toggleMenu('platform')">
                <span>{{ getPlatformDisplay() }}</span>
              </button>
              <div class="tag-dropdown-popup" :class="{ active: activeMenu === 'platform' }">
                <div class="tag-dropdown-header">选择平台 (可多选)</div>
                <div class="tag-dropdown-options">
                  <div v-for="opt in platformOptions" :key="opt.value" class="tag-dropdown-option"
                    :class="{ selected: selectedTags.platform.includes(opt.value) }"
                    @click.stop="togglePlatform(opt.value)">
                    <div class="checkbox"></div><span>{{ opt.label }}</span>
                  </div>
                </div>
              </div>
            </span>
            ，并确定合适的
            <span class="tag-fill-container">
              <button class="fill-btn" :class="{ selected: selectedTags.style }" @click.stop="toggleMenu('style')">
                <span>{{ getSingleDisplay('style', styleOptions) }}</span>
              </button>
              <div class="tag-dropdown-popup" :class="{ active: activeMenu === 'style' }">
                <div class="tag-dropdown-header">选择风格</div>
                <div class="tag-dropdown-options">
                  <div v-for="opt in styleOptions" :key="opt.value" class="tag-dropdown-option"
                    :class="{ selected: selectedTags.style === opt.value }"
                    @click.stop="selectSingle('style', opt.value)">
                    <div class="checkbox"></div><span>{{ opt.label }}</span>
                  </div>
                </div>
              </div>
            </span>
            ，同时考虑即将到来的
            <span class="tag-fill-container">
              <button class="fill-btn" :class="{ selected: selectedTags.festival }" @click.stop="toggleMenu('festival')">
                <span>{{ getSingleDisplay('festival', festivalOptions) }}</span>
              </button>
              <div class="tag-dropdown-popup" :class="{ active: activeMenu === 'festival' }">
                <div class="tag-dropdown-header">选择节日</div>
                <div class="tag-dropdown-options">
                  <div v-for="opt in festivalOptions" :key="opt.value" class="tag-dropdown-option"
                    :class="{ selected: selectedTags.festival === opt.value }"
                    @click.stop="selectSingle('festival', opt.value)">
                    <div class="checkbox"></div><span>{{ opt.label }}</span>
                  </div>
                </div>
              </div>
            </span>
            以及
            <span class="tag-fill-container">
              <button class="fill-btn" :class="{ selected: selectedTags['product-type'] }" @click.stop="toggleMenu('product-type')">
                <span>{{ getSingleDisplay('product-type', productTypeOptions) }}</span>
              </button>
              <div class="tag-dropdown-popup" :class="{ active: activeMenu === 'product-type' }">
                <div class="tag-dropdown-header">选择产品类型</div>
                <div class="tag-dropdown-options">
                  <div v-for="opt in productTypeOptions" :key="opt.value" class="tag-dropdown-option"
                    :class="{ selected: selectedTags['product-type'] === opt.value }"
                    @click.stop="selectSingle('product-type', opt.value)">
                    <div class="checkbox"></div><span>{{ opt.label }}</span>
                  </div>
                </div>
              </div>
            </span>
            。我们的设计将面向
            <span class="tag-fill-container">
              <button class="fill-btn" :class="{ selected: selectedTags['target-user'] }" @click.stop="toggleMenu('target-user')">
                <span>{{ getSingleDisplay('target-user', targetUserOptions) }}</span>
              </button>
              <div class="tag-dropdown-popup" :class="{ active: activeMenu === 'target-user' }">
                <div class="tag-dropdown-header">选择目标用户</div>
                <div class="tag-dropdown-options">
                  <div v-for="opt in targetUserOptions" :key="opt.value" class="tag-dropdown-option"
                    :class="{ selected: selectedTags['target-user'] === opt.value }"
                    @click.stop="selectSingle('target-user', opt.value)">
                    <div class="checkbox"></div><span>{{ opt.label }}</span>
                  </div>
                </div>
              </div>
            </span>
            在
            <span class="tag-fill-container">
              <button class="fill-btn" :class="{ selected: selectedTags['promotion-scene'] }" @click.stop="toggleMenu('promotion-scene')">
                <span>{{ getSingleDisplay('promotion-scene', promotionSceneOptions) }}</span>
              </button>
              <div class="tag-dropdown-popup" :class="{ active: activeMenu === 'promotion-scene' }">
                <div class="tag-dropdown-header">选择宣传场景</div>
                <div class="tag-dropdown-options">
                  <div v-for="opt in promotionSceneOptions" :key="opt.value" class="tag-dropdown-option"
                    :class="{ selected: selectedTags['promotion-scene'] === opt.value }"
                    @click.stop="selectSingle('promotion-scene', opt.value)">
                    <div class="checkbox"></div><span>{{ opt.label }}</span>
                  </div>
                </div>
              </div>
            </span>
            中呈现最佳效果。
          </div>

          <!-- 自由输入框 -->
          <div class="textarea-wrapper">
            <textarea class="custom-textarea"
              placeholder="在此输入您的其他要求或描述… (自由输入)"
              rows="2"
              v-model="freeText">
            </textarea>
            
            <!-- 功能按钮组 -->
            <div class="input-tools">
              <!-- 方言语音输入 -->
              <div class="tool-btn-group">
                <button class="tool-btn voice-btn" 
                  :class="{ recording: isRecording }"
                  @click="toggleVoiceInput" 
                  @contextmenu.prevent="showDialectMenu = !showDialectMenu"
                  title="点击开始录音，右键切换方言"
                  :disabled="isGenerating">
                  <i data-feather="mic" class="tool-icon"></i>
                  <span class="tool-label">{{ dialectLabel }}</span>
                  <span v-if="isRecording" class="recording-indicator"></span>
                </button>
                <!-- 方言选择下拉 -->
                <div class="dialect-popover" :class="{ active: showDialectMenu }">
                  <button 
                    v-for="d in dialectOptions" :key="d.value"
                    class="dialect-opt"
                    :class="{ selected: currentDialect === d.value }"
                    @click="setDialect(d.value); showDialectMenu = false">
                    {{ d.label }}
                  </button>
                </div>
              </div>
              
              <!-- 直播脚本勾选 -->
              <button class="tool-btn script-btn" 
                :class="{ active: enableLiveScript }"
                @click="enableLiveScript = !enableLiveScript" 
                title="勾选后提交时自动生成直播脚本"
                :disabled="isGenerating">
                <i data-feather="video" class="tool-icon"></i>
                <span class="tool-label">直播</span>
                <span v-if="enableLiveScript" class="check-badge">✓</span>
              </button>
            </div>
          </div>

          <!-- 提交按钮 -->
          <button class="arrow-up-left-wrapper" type="button" @click="handleSubmit" :disabled="isGenerating">
            <span v-if="isGenerating" class="loading-spinner"></span>
            <i v-else data-feather="arrow-up-left" class="arrow-up-left"></i>
          </button>
        </section>
      </div>

      <!-- ===== AI 结果卡片 ===== -->
      <div v-if="submitted" class="ai-result-card">

        <!-- 第一部分：文案 -->
        <div class="result-section result-text">
          <div class="section-header">
            <h3 class="section-title">📝 文案内容</h3>
            <div class="header-actions">
              <span v-if="aiProductName" class="product-badge">{{ aiProductName }}</span>
              <span v-if="aiRegion" class="region-badge">📍 {{ aiRegion }}</span>
              <button class="copy-btn" @click="copyText(aiContent)" title="复制文案">
                <i data-feather="copy"></i>
              </button>
            </div>
          </div>
          <!-- 骨架屏（生成中） -->
          <div class="ai-text-loading" v-if="isGenerating">
            <div class="skeleton-line"></div>
            <div class="skeleton-line short"></div>
            <div class="skeleton-line"></div>
            <div class="skeleton-line medium"></div>
          </div>
          <div class="ai-text" v-else>{{ aiContent }}</div>
        </div>

        <!-- 第二部分：图片 -->
        <div class="result-section result-images">
          <div class="section-header">
            <h3 class="section-title">🖼️ 生成图片</h3>
            <span v-if="!uploadedImagePreview" class="hint-small">请在左侧上传产品图后重新生成</span>
          </div>

          <!-- ★ 进度条：图片处理中时显示 ★ -->
          <div class="progress-card" v-if="imgIsProcessing">
            <div class="progress-header">
              <span>🎨</span>
              <span class="progress-title">AI 正在处理图片</span>
              <span class="progress-pct">{{ imgProgress }}%</span>
            </div>
            <div class="progress-bar-track">
              <div class="progress-bar-fill" :style="{ width: imgProgress + '%' }">
                <div class="progress-shimmer"></div>
              </div>
            </div>
            <div class="progress-step">
              <span class="step-dot"></span>{{ imgProgressStep }}
            </div>
            <div class="step-bubbles">
              <div class="step-bubble" :class="{ active: imgProgress < 50, done: imgProgress >= 50 }">
                <span>✂️</span><span>智能抠图</span>
              </div>
              <div class="step-bubble" :class="{ active: imgProgress >= 50 && imgProgress < 65, done: imgProgress >= 65, wait: imgProgress < 50 }">
                <span>🖼️</span><span>合成海报</span>
              </div>
              <div class="step-bubble" :class="{ active: imgProgress >= 65 && imgProgress < 100, done: imgProgress >= 100, wait: imgProgress < 65 }">
                <span>🎨</span><span>生成滤镜</span>
              </div>
            </div>
            <div class="progress-tip">{{ currentTip }}</div>
          </div>

          <!-- 三张海报 -->
          <div class="ai-images-container" v-if="!imgIsProcessing">
            <div class="view-10">
              <div v-for="(slot, idx) in posterSlots" :key="idx"
                class="img-wrapper"
                :class="{ 'img-selected': slot.filterId === selectedFilter }"
                @click="selectFilter(slot.filterId)">
                <img v-if="slot.src" :src="slot.src" class="poster-img" :alt="slot.label" />
                <div v-else class="placeholder-image">{{ slot.label }}</div>
                <div v-if="slot.src" class="poster-filter-label">{{ slot.filterName }}</div>
                <div v-if="slot.src && slot.filterId === selectedFilter" class="poster-selected-mark">✓ 已选</div>
              </div>
            </div>

            <!-- 滤镜选择条（有海报才显示） -->
            <div class="filter-strip" v-if="imgPosterVersions && Object.keys(imgPosterVersions).length">
              <div class="filter-strip-label">🎨 选择滤镜风格（点击切换）</div>
              <div class="filter-strip-options">
                <div v-for="(ver, fid) in imgPosterVersions" :key="fid"
                  class="filter-option"
                  :class="{ active: selectedFilter === fid }"
                  @click="applyFilter(fid)">
                  <img :src="ver.thumbnail || ver.image" class="filter-thumb" :alt="ver.name" />
                  <span class="filter-option-name">{{ ver.name }}</span>
                </div>
              </div>
            </div>

            <!-- 工具按钮 -->
            <div class="ai-tools-container">
              <div class="ai-tools">
                <button class="view-13" @click="downloadPoster" :disabled="!selectedPosterSrc">
                  <i data-feather="download"></i> 下载海报
                </button>
                <button class="view-14" @click="openReupload">
                  <i data-feather="image"></i> 重新上传
                </button>
                <button class="ai-poster-btn" @click="showAiPosterInput = !showAiPosterInput">
                  <i data-feather="sparkles"></i> ✨ AI 生成海报
                </button>
              </div>
              <!-- AI海报生成输入框 -->
              <div class="ai-poster-input-area" v-if="showAiPosterInput">
                <input 
                  type="text" 
                  class="ai-poster-prompt" 
                  v-model="aiPosterPrompt"
                  placeholder="描述您想要的海报风格（如：清新绿色田园风 / 复古中国风 / 金色丰收季...）"
                  @keyup.enter="generateAiPoster" />
                <button class="ai-poster-gen-btn" @click="generateAiPoster" :disabled="aiPosterGenerating || !aiPosterPrompt.trim()">
                  <span v-if="aiPosterGenerating" class="loading-spinner-sm"></span>
                  <span v-else>生成</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 第三部分：推荐标签 -->
        <div class="result-section result-tags" v-if="hotTags.length">
          <div class="section-header">
            <h3 class="section-title">🏷️ 推荐标签</h3>
            <div class="header-actions">
              <span class="tag-source-hint">来自 Neo4j 标签库</span>
              <button class="copy-btn" @click="copyText(hotTags.join(' '))">
                <i data-feather="copy"></i>
              </button>
            </div>
          </div>
          <div class="tags-list">
            <span v-for="tag in hotTags" :key="tag" class="hot-tag"
              :class="{ 'tag-copied': copiedTag === tag }"
              @click="copySingleTag(tag)">
              {{ tag }}
            </span>
          </div>
        </div>

        <!-- 第四部分：数据集参考案例 -->
        <div class="result-section result-rag" v-if="ragExamples.length">
          <div class="section-header">
            <h3 class="section-title">📚 数据集参考案例</h3>
            <span class="tag-source-hint">来自本地农业文案数据集</span>
          </div>
          <div class="rag-list">
            <article v-for="ex in ragExamples" :key="`${ex.title}-${ex.score}`" class="rag-item">
              <div class="rag-item-head">
                <span class="rag-platform">{{ ex.platform || '数据集' }}</span>
                <span class="rag-score">匹配度 {{ Number(ex.score || 0).toFixed(1) }}</span>
              </div>
              <div class="rag-title">{{ ex.title || ex.product_name }}</div>
              <div class="rag-meta">{{ ex.product_name }} · {{ ex.category }}</div>
              <p class="rag-body">{{ ex.body }}</p>
            </article>
          </div>
        </div>

        <!-- ★ 实时排版预览 -->
        <div class="result-section preview-section" v-if="aiContent">
          <div class="section-header">
            <h3 class="section-title">📱 排版预览</h3>
            <span class="hint-small">模拟手机端展示效果</span>
          </div>
          <div class="phone-preview-wrap">
            <div class="phone-frame">
              <div class="phone-notch"></div>
              <div class="phone-screen">
                <!-- 平台标识 -->
                <div class="preview-platform-bar">
                  <span class="preview-avatar">{{ (aiProductName || '农').charAt(0) }}</span>
                  <span class="preview-username">{{ aiProductName || '农产品' }}</span>
                  <span class="preview-follow">+ 关注</span>
                </div>
                <!-- 海报图 -->
                <div class="preview-img-area" v-if="selectedPosterSrc">
                  <img :src="selectedPosterSrc" class="preview-poster" />
                </div>
                <div class="preview-img-placeholder" v-else>
                  <span>🖼️ 生成海报后显示</span>
                </div>
                <!-- 文案 -->
                <div class="preview-text-area">
                  <p class="preview-content">{{ aiContent }}</p>
                </div>
                <!-- 标签 -->
                <div class="preview-tags-area" v-if="hotTags.length">
                  <span v-for="tag in hotTags.slice(0,5)" :key="tag" class="preview-tag">{{ tag }}</span>
                </div>
                <!-- 底部互动栏 -->
                <div class="preview-action-bar">
                  <span>❤️ 点赞</span>
                  <span>💬 评论</span>
                  <span>⭐ 收藏</span>
                  <span>↗️ 转发</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ★ 直播脚本结果模块（在预览图下方） -->
        <div class="result-section live-script-section" v-if="enableLiveScript && generatedScript">
          <div class="section-header">
            <h3 class="section-title">🎬 直播脚本</h3>
            <div class="header-actions">
              <select class="script-duration-select" v-model="scriptDuration" @change="regenerateScript">
                <option :value="30">30秒</option>
                <option :value="60">1分钟</option>
                <option :value="180">3分钟</option>
                <option :value="300">5分钟</option>
              </select>
              <button class="copy-btn" @click="copyScript" title="复制脚本">
                <i data-feather="copy"></i>
              </button>
              <button class="refresh-btn" @click="regenerateScript" :disabled="scriptGenerating" title="重新生成">
                <i data-feather="refresh-cw"></i>
              </button>
            </div>
          </div>
          <div class="script-loading" v-if="scriptGenerating">
            <div class="skeleton-line"></div>
            <div class="skeleton-line short"></div>
            <div class="skeleton-line"></div>
            <div class="skeleton-line medium"></div>
            <div class="skeleton-line short"></div>
          </div>
          <div class="script-body" v-else v-html="renderMarkdown(generatedScript)"></div>
        </div>

        <!-- 进一步需求 -->
        <div class="further-request">
          <input type="text" class="further-input"
            placeholder="输入进一步需求（如：改成更文艺的风格/强调获得过的奖项）…"
            v-model="furtherText"
            @keyup.enter="regenerate" />
          <button class="further-btn" @click="regenerate" :disabled="isGenerating">
            <span v-if="isGenerating" class="loading-spinner-sm"></span>
            <span v-else>重新生成</span>
          </button>
        </div>
      </div>
    </main>

    <!-- 右侧操作栏 -->
    <aside class="view-26" v-if="!historyOpen">
      <button class="history-button" @click="historyOpen = true" title="历史记录">
        <i data-feather="clock" class="history-icon"></i>
      </button>
      <button class="new-project-button" @click="newChat" title="新建对话">
        <i data-feather="plus-square" class="new-project-icon"></i>
      </button>
      <!-- 退出登录 -->
      <button class="logout-button" @click="handleLogout" title="退出登录">
        <i data-feather="log-out" class="logout-icon"></i>
      </button>
    </aside>

    <HistorySidebar v-model="historyOpen" :items="historyItems" @select="loadHistory" @new-chat="newChat" @delete="deleteHistory" />
    <TemplateModal v-model="templateModalOpen" @select="onTemplateSelect" />
    
    <input type="file" ref="reuploadInput" style="display:none;" accept="image/*" @change="handleReupload" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch, inject } from 'vue'
import HistorySidebar from '@/components/HistorySidebar.vue'
import TemplateModal from '@/components/TemplateModal.vue'
import { isLoggedIn, getUser, clearAuth, getHistory } from '@/api'

const openAuthModal = inject('openAuthModal', null)

// 退出登录
const handleLogout = () => {
  if (!confirm('确认退出登录？')) return
  clearAuth()
  // 清空页面状态
  newChat()
  // 跳回首页或弹出登录框
  if (openAuthModal) openAuthModal()
  else window.location.reload()
}

// ── 服务地址 ──
const AI_API  = 'http://localhost:5001'
const IMG_API = 'http://localhost:5003'

// ── 平台/节日映射 ──
const PLATFORM_MAP = { xiaohongshu:'小红书', douyin:'抖音', taobao:'淘宝', weibo:'微博', toutiao:'头条' }
const FESTIVAL_MAP = { 'spring-festival':'春节', 'mid-autumn':'中秋节', 'national-day':'国庆节', 'dragon-boat':'端午节', qixi:'七夕节' }
const TARGET_MAP   = { young:'年轻人', 'middle-aged':'中年人', elderly:'老年人', female:'女性用户', family:'家庭用户' }
const FILTER_NAMES = { original:'原图', warm:'暖调', cool:'冷调', vivid:'鲜艳', vintage:'复古', soft:'柔和', dramatic:'浓郁', bright:'明亮', green:'田园' }

// ────────────────────────────────────────────
//  文案相关状态
// ────────────────────────────────────────────
const submitted     = ref(false)
const isGenerating  = ref(false)
const freeText      = ref('')
const furtherText   = ref('')
const aiContent     = ref('')
const aiProductName = ref('')
const aiRegion      = ref('')
const sessionId     = ref(null)
const hotTags       = ref([])
const ragExamples   = ref([])
const copiedTag     = ref('')

// ────────────────────────────────────────────
//  语音输入和直播脚本状态
// ────────────────────────────────────────────
const isRecording       = ref(false)
const voiceInputText    = ref('')
const currentDialect    = ref('mandarin')
const enableLiveScript  = ref(false)    // ★ 勾选开关
const generatedScript   = ref('')
const scriptGenerating  = ref(false)
const scriptDuration    = ref(60)

// AI 海报生成状态
const aiPosterPrompt     = ref('')
const aiPosterGenerating = ref(false)
const showAiPosterInput  = ref(false)

// 方言选项
const dialectOptions = [
  { value: 'mandarin', label: '普通话' },
  { value: 'cantonese', label: '粤语' },
  { value: 'sichuan', label: '四川话' },
  { value: 'shandong', label: '山东话' },
  { value: 'zhejiang', label: '浙江话' },
  { value: 'fujian', label: '福建话' },
]

const dialectLabel = computed(() => {
  const d = dialectOptions.find(o => o.value === currentDialect.value)
  return d ? d.label : '语音'
})

// 方言菜单显示状态
const showDialectMenu = ref(false)

// ────────────────────────────────────────────
//  图片相关状态
// ────────────────────────────────────────────
const uploadedImageBase64  = ref('')
const uploadedImagePreview = ref('')
const selectedTemplate     = ref(null)
const templateThumbnail    = ref('')
const templateModalOpen    = ref(false)
const selectedFilter       = ref('original')

// ★ 图片处理进度（直接在这里管理，不用引入额外 composable）★
const imgIsProcessing  = ref(false)
const imgProgress      = ref(0)
const imgProgressStep  = ref('')
const imgPosterVersions = ref(null)  // { original:{image,thumbnail,name}, warm:{...}, ... }
let   imgPollTimer     = null

// ── Agent 工作流状态 ──
const agentStates = ref({})
let _pendingSave = null  // 等图片完成后再保存历史
const workflowId  = ref(null)

const AGENT_LABELS = {
  ProfileAgent:     { icon: '👤', label: '读取用户档案' },
  RegionAgent:      { icon: '🗺️', label: '分析地域文化' },
  TagPoolAgent:     { icon: '🏷️', label: '加载标签库' },
  CopywriterAgent:  { icon: '✍️', label: '创作文案' },
  QAAgent_round1:   { icon: '🔍', label: '质检 第1轮' },
  QAAgent_round2:   { icon: '🔍', label: '质检 第2轮' },
  QAAgent_round3:   { icon: '🔍', label: '质检 第3轮' },
  TagSelectorAgent: { icon: '⭐', label: '筛选推荐标签' },
}

const tips = [
  '💡 背景越简单，抠图效果越好',
  '🌿 AI 自动识别产品主体，无需手动标注',
  '🎯 抠图完成后可选择 4 种滤镜风格',
  '✨ 暖调滤镜最适合农产品宣传',
  '📐 建议使用正方形图片，合成效果更佳',
]
const currentTip = ref(tips[0])
let tipTimer = null

// ── 侧边栏 ──
const historyOpen   = ref(false)
const historyItems  = ref([])
const fileInput     = ref(null)
const reuploadInput = ref(null)

//  历史记录功能 
const fetchHistoryList = async () => {
  try {
    const res = await getHistory(20)
    if (res && res.history) {
      historyItems.value = res.history.map((item, idx) => ({
        id:          item.workflow_id || item.timestamp || idx,
        name:        `${item.product} · ${(item.timestamp || '').substring(0, 10)}`,
        content:     item.content,
        tags:        item.tags || [],
        productName: item.product,
        region:      item.region || '',
        platform:    item.platform || '',
        posterVersions: item.poster_versions || {},  // ← 关键：对应新字段名
        createdAt:   item.timestamp,
        active:      false,
        menuOpen:    false
      }))
    }
  } catch (e) {
    console.warn('加载历史失败', e)
  }
}


// 删除历史记录
const deleteHistory = async (item) => {
  if (!confirm(`确认删除「${item.name}」？`)) return
  const userId = getUser()?.id || ''
  try {
    await fetch(`${AI_API}/api/history/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workflow_id: item.id, user_id: String(userId) })
    })
    // 从本地列表移除
    const idx = historyItems.value.findIndex(h => h.id === item.id)
    if (idx > -1) historyItems.value.splice(idx, 1)
  } catch (e) {
    console.warn('删除历史失败', e)
  }
}

const loadHistory = (item) => {
  aiContent.value     = item.content || ''
  aiProductName.value = item.productName || ''
  aiRegion.value      = item.region || ''
  hotTags.value       = item.tags || []
  submitted.value     = true
  historyOpen.value   = false
  // 恢复 滤镜
  if (item.posterVersions && Object.keys(item.posterVersions).length) {
    imgPosterVersions.value = item.posterVersions
    selectedFilter.value = Object.keys(item.posterVersions)[0] || 'original'
  } else if (item.posterSrc) {
    imgPosterVersions.value = {
      original: { name:'原图', image: item.posterSrc, thumbnail: item.posterSrc }
    }
    selectedFilter.value = 'original'
  } else {
    imgPosterVersions.value = null
  }
  historyItems.value.forEach(h => { h.active = h.id === item.id })
  nextTick(() => { if (window.feather) window.feather.replace() })
}

// ── 标签选项 ──
const selectedTags = reactive({ platform:[], style:'', festival:'', 'product-type':'', 'target-user':'', 'promotion-scene':'' })

const platformOptions     = [{value:'xiaohongshu',label:'小红书'},{value:'douyin',label:'抖音'},{value:'taobao',label:'淘宝'},{value:'weibo',label:'微博'},{value:'toutiao',label:'头条'}]
const styleOptions        = [{value:'fresh',label:'清新自然'},{value:'traditional',label:'传统中式'},{value:'modern',label:'现代科技'},{value:'minimalist',label:'极简主义'},{value:'vintage',label:'复古风'}]
const festivalOptions     = [{value:'spring-festival',label:'春节'},{value:'mid-autumn',label:'中秋节'},{value:'national-day',label:'国庆节'},{value:'dragon-boat',label:'端午节'},{value:'qixi',label:'七夕节'}]
const productTypeOptions  = [{value:'agricultural',label:'农产品'},{value:'food',label:'食品饮料'},{value:'clothing',label:'服装服饰'},{value:'electronics',label:'电子产品'},{value:'cosmetics',label:'美妆个护'}]
const targetUserOptions   = [{value:'young',label:'年轻人'},{value:'middle-aged',label:'中年人'},{value:'elderly',label:'老年人'},{value:'female',label:'女性用户'},{value:'family',label:'家庭用户'}]
const promotionSceneOptions=[{value:'promotion',label:'促销活动'},{value:'brand',label:'品牌宣传'},{value:'festival',label:'节日营销'},{value:'launch',label:'新品发布'},{value:'anniversary',label:'周年庆典'}]

// ────────────────────────────────────────────
//  计算：三个海报展示槽
// ────────────────────────────────────────────
const posterSlots = computed(() => {
  const defaults = [
    { filterId:'original', filterName:'原图',  label:'宣传图片1', src:'' },
    { filterId:'warm',     filterName:'暖调',  label:'宣传图片2', src:'' },
    { filterId:'vivid',    filterName:'鲜艳',  label:'宣传图片3', src:'' },
  ]
  if (!imgPosterVersions.value) return defaults
  const keys = Object.keys(imgPosterVersions.value)
  return defaults.map((slot, i) => {
    const key = keys[i] || slot.filterId
    const ver = imgPosterVersions.value[key]
    return { filterId: key, filterName: FILTER_NAMES[key] || key, label: slot.label, src: ver ? ver.image : '' }
  })
})

const selectedPosterSrc = computed(() => {
  if (!imgPosterVersions.value) return ''
  return imgPosterVersions.value[selectedFilter.value]?.image || ''
})

// ────────────────────────────────────────────
//  文件上传
// ────────────────────────────────────────────
const triggerFileUpload = () => fileInput.value?.click()
const openReupload      = () => reuploadInput.value?.click()

const readFileAsBase64 = (file) => new Promise((res, rej) => {
  const reader = new FileReader()
  reader.onload = e => res(e.target.result)
  reader.onerror = rej
  reader.readAsDataURL(file)
})

const handleFileUpload = async (e) => {
  const file = e.target.files[0]
  if (!file) return
  const b64 = await readFileAsBase64(file)
  uploadedImageBase64.value  = b64
  uploadedImagePreview.value = b64
  fileInput.value.value = ''
}

const handleReupload = async (e) => {
  const file = e.target.files[0]
  if (!file) return
  const b64 = await readFileAsBase64(file)
  uploadedImageBase64.value  = b64
  uploadedImagePreview.value = b64
  reuploadInput.value.value = ''
  if (selectedTemplate.value) runImagePipeline()
}

// ────────────────────────────────────────────
//  模板选择
// ────────────────────────────────────────────
const onTemplateSelect = (tpl) => {
  console.log('模板对象：', tpl) 
  selectedTemplate.value  = tpl
  templateThumbnail.value = tpl.thumbnail || ''
  templateModalOpen.value = false
}

// ────────────────────────────────────────────
//  标签菜单
// ────────────────────────────────────────────
const activeMenu = ref(null)
const toggleMenu     = (type) => { activeMenu.value = activeMenu.value === type ? null : type }
const togglePlatform = (value) => {
  const idx = selectedTags.platform.indexOf(value)
  idx > -1 ? selectedTags.platform.splice(idx, 1) : selectedTags.platform.push(value)
}
const selectSingle = (type, value) => { selectedTags[type] = selectedTags[type] === value ? '' : value; activeMenu.value = null }
const getPlatformDisplay = () => {
  const c = selectedTags.platform.length
  if (c === 0) return '平台'
  if (c === 1) return platformOptions.find(o => o.value === selectedTags.platform[0])?.label || '平台'
  return `平台 (${c})`
}
const getSingleDisplay = (type, options) => {
  const val = selectedTags[type]
  if (!val) return { style:'风格', festival:'节日', 'product-type':'产品类型', 'target-user':'目标用户', 'promotion-scene':'宣传场景' }[type]
  return options.find(o => o.value === val)?.label || ''
}

// ────────────────────────────────────────────
//  核心：图片处理（异步轮询）
// ────────────────────────────────────────────
const runImagePipeline = async () => {
  if (!uploadedImageBase64.value) return

  // 重置状态
  imgIsProcessing.value   = true
  imgProgress.value       = 0
  imgProgressStep.value   = '正在提交任务…'
  imgPosterVersions.value = null

  // 轮换提示语
  tipTimer = setInterval(() => {
    currentTip.value = tips[Math.floor(Math.random() * tips.length)]
  }, 3000)

  try {
    // 分析模板类型，决定构图策略
    const template = selectedTemplate.value
    const compositionStrategy = determineCompositionStrategy(template)
    
    // 第一步：提交任务，立刻拿到 task_id
    const res = await fetch(`${IMG_API}/api/image/full-pipeline`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_base64: uploadedImageBase64.value,
        template_id:  template?.id || 'green_gradient',
        template_type: template?.type || 'builtin',
        size:         [1080, 1080],
        position:     compositionStrategy.position,
        scale:        compositionStrategy.scale,
        alignment:    compositionStrategy.alignment,
        auto_composition: template?.auto_composition || false,
        filters:      ['original', 'vintage', 'vivid']
      })
    })
    const data = await res.json()

    if (!data.task_id) {
      throw new Error(data.error || '提交失败')
    }

    imgProgressStep.value = '任务已提交，AI 处理中…'

    // 第二步：轮询进度，每秒问一次后端
    await new Promise((resolve, reject) => {
      imgPollTimer = setInterval(async () => {
        try {
          const pollRes  = await fetch(`${IMG_API}/api/task/${data.task_id}`)
          const pollData = await pollRes.json()

          imgProgress.value     = pollData.progress || 0
          imgProgressStep.value = pollData.step     || ''

          if (pollData.status === 'done') {
            clearInterval(imgPollTimer)
            imgPosterVersions.value = pollData.poster_versions
            selectedFilter.value    = Object.keys(pollData.poster_versions || {})[0] || 'original'
            resolve()

          } else if (pollData.status === 'error') {
            clearInterval(imgPollTimer)
            reject(new Error(pollData.error || '处理失败'))
          }
        } catch (e) {
          clearInterval(imgPollTimer)
          reject(e)
        }
      }, 1000)   // ← 每秒轮询一次
    })
    // ★ 图片处理成功！立刻把 poster 数据同步到历史记录
    if (workflowId.value && imgPosterVersions.value) {
      const userId = getUser()?.id || 'default_user'
      try {
        await fetch(`${AI_API}/api/history/update-poster`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            workflow_id: workflowId.value,
            user_id: String(userId),
            poster_versions: imgPosterVersions.value
          })
        })
        console.log('✅ 历史记录图片已同步')
      } catch (e) {
        console.warn('同步图片到历史失败（不影响展示）:', e)
      }
    }

  } catch (e) {
    console.error('图片处理失败:', e)
    imgProgressStep.value = '图片处理失败：' + e.message
  } finally {
    imgIsProcessing.value = false
    clearInterval(tipTimer)
  }

}

// ────────────────────────────────────────────
//  自适应构图智能排版策略
// ────────────────────────────────────────────
const determineCompositionStrategy = (template) => {
  if (!template) {
    return {
      position: 'center',
      scale: 1.0,
      alignment: 'center'
    }
  }

  // AI生成的模板需要更智能的构图
  if (template.type === 'ai' || template.auto_composition) {
    return {
      position: 'smart',      // 智能位置
      scale: 0.85,           // 适当缩放，留出空间给背景
      alignment: 'center',
      strategy: 'auto'
    }
  }

  // 自定义图片模板（用户上传的背景）
  if (template.type === 'file') {
    return {
      position: 'intelligent', // 智能分析背景后决定位置
      scale: 0.75,            // 较小缩放，避免遮挡背景关键元素
      alignment: 'auto',       // 自动对齐
      strategy: 'adaptive'
    }
  }

  // 内置渐变模板
  return {
    position: 'center',
    scale: 0.9,
    alignment: 'center',
    strategy: 'center'
  }
}

// ────────────────────────────────────────────
//  提交生成
// ────────────────────────────────────────────
const handleSubmit = async () => {
  if (!isLoggedIn()) {
    alert('请先登录')
    if (openAuthModal) openAuthModal()
    return
  }

  isGenerating.value = true
  submitted.value    = true
  hotTags.value      = []
  ragExamples.value  = []
  aiContent.value    = ''

  const userId   = getUser()?.id || 'default_user'
  const platform = selectedTags.platform.map(v => PLATFORM_MAP[v] || v)[0] || '小红书'
  const festivalLabel = selectedTags.festival ? FESTIVAL_MAP[selectedTags.festival] || '' : ''
  const targetUser    = selectedTags['target-user'] ? TARGET_MAP[selectedTags['target-user']] || '' : ''

  try {
    // ★ 重置 Agent 状态面板
  agentStates.value = {}
  workflowId.value  = null

  // ★ 从用户输入中提取字数要求，如"生成300字" → word_count_target=300
  const wordMatch = freeText.value.match(/(\d+)\s*字/)
  const wordCountTarget = wordMatch ? parseInt(wordMatch[1]) : 120
  const wordCountHint   = wordMatch ? `${wordCountTarget}字左右` : '100～120字'

  const genRes = await fetch(`${AI_API}/api/ai/generate`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_name: freeText.value || '',
        platform,
        user_id: userId,
        session_id: sessionId.value,
        festival_hint: festivalLabel ? `节日氛围：${festivalLabel}` : '',
        target_user_hint: targetUser,
        custom_tags: [],
        word_count_hint: wordCountHint,
        word_count_target: wordCountTarget,
  // ★ 新增：模板内容
        template: selectedTemplate.value
          ? (selectedTemplate.value.content || selectedTemplate.value.copyTemplate || selectedTemplate.value.description || '')
          : '',
  // ★ 新增：工具箱里保存的补充说明（直接读 localStorage）
        supplemental_info: (() => {
          try {
            const key = `user_supplement_${userId}`
            return localStorage.getItem(key) || ''
    }       catch {
            return ''
    }
  })()
      })
    })

    const genData = await genRes.json()

    if (genData.content) {

      // === 强制保存图片和标签到历史 ===
      const posterData = imgPosterVersions.value || {}
      console.log('准备保存的海报数据：', Object.keys(posterData))  // 调试用

      // 把图片数据塞进 genData
      genData.poster_versions = posterData
      genData.recommended_tags = genData.recommended_tags || hotTags.value || []

      console.log('✅ 准备保存历史记录，包含图片和标签')
      aiContent.value     = genData.content
      aiProductName.value = genData.product_name || ''
      aiRegion.value      = genData.region || ''
      sessionId.value     = genData.session_id || null
      hotTags.value       = genData.recommended_tags || []
      ragExamples.value   = genData.rag_examples || []
      // ★ 保存 workflow_id 供面板使用（最终状态已经返回，只是回显）
      if (genData.workflow_id) {
        workflowId.value  = genData.workflow_id
        agentStates.value = genData.agent_summary || {}
      }
    } else {
      aiContent.value = '生成失败，请重试。'
    }
  } catch (e) {
    console.error('AI生成错误:', e)
    // 显示真实错误原因，方便排查
    if (e.message && e.message.includes('fetch')) {
      aiContent.value = '❌ 无法连接到 AI 服务（:5001），请确认 ai_service.py 已启动'
    } else {
      aiContent.value = '❌ 生成失败：' + (e.message || '未知错误，请查看控制台')
    }
  } finally {
    isGenerating.value = false
    nextTick(() => { if (window.feather) window.feather.replace() })
  }

  // 文案生成完 → 同时启动图片处理（互不阻塞）
  if (uploadedImageBase64.value) {
    runImagePipeline()
  }

  // ★ 如果勾选了直播脚本，同时生成
  if (enableLiveScript.value && aiContent.value) {
    triggerLiveScript()
  }
}

// ────────────────────────────────────────────
//  重新生成
// ────────────────────────────────────────────
const regenerate = async () => {
  if (!furtherText.value.trim()) return
  isGenerating.value = true
  try {
    //  从"重新生成"输入框里也提取字数要求
    const wm = furtherText.value.match(/(\d+)\s*字/)
    const wcTarget = wm ? parseInt(wm[1]) : 120
    const wcHint   = wm ? `${wcTarget}字左右` : '100～120字'

    const res = await fetch(`${AI_API}/api/ai/refine`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        original_content:  aiContent.value,
        request:           furtherText.value,
        product_name:      aiProductName.value,
        platform:          selectedTags.platform.map(v => PLATFORM_MAP[v] || v)[0] || '小红书',
        word_count_hint:   wcHint,
        word_count_target: wcTarget
      })
    })
    const data = await res.json()
    if (data.content) aiContent.value = data.content
  } catch (e) {
    console.error('修改失败:', e)
  } finally {
    isGenerating.value = false
    nextTick(() => { if (window.feather) window.feather.replace() })
  }
}

// ────────────────────────────────────────────
//  滤镜 / 下载
// ────────────────────────────────────────────
const selectFilter  = (fid) => { if (imgPosterVersions.value?.[fid]) selectedFilter.value = fid }
const applyFilter   = (fid) => selectFilter(fid)
const downloadPoster = () => {
  if (!selectedPosterSrc.value) return
  const a = document.createElement('a')
  a.href = selectedPosterSrc.value
  a.download = `海报_${aiProductName.value || '农产品'}_${selectedFilter.value}.jpg`
  a.click()
}

// ────────────────────────────────────────────
//  复制
// ────────────────────────────────────────────
const copyText = async (text) => {
  try { await navigator.clipboard.writeText(text); alert('复制成功！') } catch { alert('请手动复制') }
}
const copySingleTag = async (tag) => {
  try {
    await navigator.clipboard.writeText(tag)
    copiedTag.value = tag
    setTimeout(() => { copiedTag.value = '' }, 1500)
  } catch {}
}

// ────────────────────────────────────────────
//  方言语音输入功能（使用Web Speech API + 后端讯飞识别）
// ────────────────────────────────────────────
let mediaRecorder = null
let audioChunks = []

const toggleVoiceInput = () => {
  if (isRecording.value) {
    stopVoiceRecording()
  } else {
    startVoiceRecording()
  }
}

const copyScript = async () => {
  try {
    await navigator.clipboard.writeText(generatedScript.value)
    alert('直播脚本已复制！')
  } catch {
    alert('请手动复制')
  }
}

// ────────────────────────────────────────────
//  直播脚本生成（提交时自动触发）
// ────────────────────────────────────────────
const triggerLiveScript = async () => {
  scriptGenerating.value = true
  generatedScript.value = ''

  const userId = getUser()?.id || 'default_user'
  const platform = selectedTags.platform.map(v => PLATFORM_MAP[v] || v)[0] || '抖音'

  try {
    const res = await fetch(`${AI_API}/api/ai/generate-live-script`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_name: aiProductName.value || freeText.value || '农产品',
        platform,
        user_id: userId,
        duration: scriptDuration.value,
        style: selectedTags.style || 'fresh',
        ai_content: aiContent.value    // ★ 关联生成的文案
      })
    })
    const data = await res.json()
    if (data.script) {
      generatedScript.value = typeof data.script === 'string'
        ? data.script
        : JSON.stringify(data.script, null, 2)
    } else {
      generatedScript.value = '脚本生成失败，请重试'
    }
  } catch (e) {
    console.error('生成直播脚本失败:', e)
    generatedScript.value = '网络错误，请重试'
  } finally {
    scriptGenerating.value = false
    nextTick(() => { if (window.feather) window.feather.replace() })
  }
}

const regenerateScript = () => {
  if (aiContent.value || freeText.value) triggerLiveScript()
}

// 简易 Markdown 渲染（用于脚本展示）
const renderMarkdown = (md) => {
  if (!md) return ''
  return md
    .replace(/^## (.+)$/gm, '<h4 class="script-h2">$1</h4>')
    .replace(/^### (.+)$/gm, '<h5 class="script-h3">$1</h5>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\[(.+?)\]/g, '<span class="script-action">[$1]</span>')
    .replace(/\n/g, '<br>')
}

// ────────────────────────────────────────────
//  AI 海报生成（Doubao-Seedream 4.0）
// ────────────────────────────────────────────
const generateAiPoster = async () => {
  if (!aiPosterPrompt.value.trim()) return
  aiPosterGenerating.value = true

  try {
    const res = await fetch(`${IMG_API}/api/ai/generate-poster`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: aiPosterPrompt.value,
        size: '1024x1024',
        style: selectedTags.style || ''
      })
    })
    const data = await res.json()
    if (data.success) {
      // 自动设为当前模板
      selectedTemplate.value = {
        id: data.template_id,
        name: data.name,
        type: 'ai',
        thumbnail: data.thumbnail,
        auto_composition: true
      }
      templateThumbnail.value = data.thumbnail
      alert(`✨ AI 海报生成成功！已自动设为背景模板${data.message ? '\n' + data.message : ''}`)
      showAiPosterInput.value = false
      // 如果已有产品图，自动重新合成
      if (uploadedImageBase64.value) {
        runImagePipeline()
      }
    } else {
      alert('海报生成失败: ' + (data.error || '未知错误'))
    }
  } catch (e) {
    console.error('AI海报生成失败:', e)
    alert('网络错误，请重试')
  } finally {
    aiPosterGenerating.value = false
    nextTick(() => { if (window.feather) window.feather.replace() })
  }
}

const startVoiceRecording = async () => {
  try {
    isRecording.value = true
    voiceInputText.value = ''
    audioChunks = []
    
    // 检查浏览器兼容性
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert('您的浏览器不支持语音输入功能，请使用现代浏览器（如Chrome、Edge）')
      isRecording.value = false
      return
    }
    
    // 请求麦克风权限
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    
    // 创建媒体录制器（使用兼容的MIME类型）
    const mimeType = MediaRecorder.isTypeSupported('audio/wav') ? 'audio/wav' : 
                     MediaRecorder.isTypeSupported('audio/mp3') ? 'audio/mp3' :
                     MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg'
    
    mediaRecorder = new MediaRecorder(stream, {
      mimeType: mimeType
    })
    
    // 监听数据可用事件
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data)
      }
    }
    
    // 录制结束时发送到后端
    mediaRecorder.onstop = async () => {
      try {
        // 停止流媒体
        stream.getTracks().forEach(track => track.stop())
        
        // 转换为base64
        const blob = new Blob(audioChunks, { type: mimeType })
        const reader = new FileReader()
        
        reader.onload = async (e) => {
          const audioBase64 = e.target.result
          
          // 调用后端语音识别接口
          const res = await fetch(`${IMG_API}/api/voice/recognize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              audio_base64: audioBase64,
              dialect: currentDialect.value,
              format: mimeType.split('/')[1] || 'wav'
            })
          })
          
          const data = await res.json()
          
          if (data.success && data.text) {
            voiceInputText.value = data.text
            freeText.value = data.text
          } else {
            console.error('语音识别失败:', data.error || '未知错误')
            alert('语音识别失败，请重试或手动输入')
          }
        }
        
        reader.readAsDataURL(blob)
        
      } catch (e) {
        console.error('处理录音失败:', e)
        alert('语音识别服务连接失败，请确认 image_service.py 已启动 (5003端口)')
      }
    }
    
    // 开始录制
    mediaRecorder.start(100) // 每100ms收集一次数据
    console.log('开始语音输入，方言:', currentDialect.value)
    
  } catch (e) {
    console.error('无法访问麦克风:', e)
    isRecording.value = false
    alert('无法访问麦克风，请允许浏览器访问麦克风权限后重试')
  }
}

const stopVoiceRecording = () => {
  if (mediaRecorder && isRecording.value) {
    mediaRecorder.stop()
  }
  isRecording.value = false
  console.log('停止语音输入')
}

const setDialect = (dialect) => {
  currentDialect.value = dialect
  console.log('切换方言:', dialect)
}



// ────────────────────────────────────────────
//  新对话 / 历史
// ────────────────────────────────────────────
const newChat = () => {
  submitted.value = false
  freeText.value = furtherText.value = aiContent.value = ''
  aiProductName.value = aiRegion.value = ''
  sessionId.value = null
  hotTags.value = []
  ragExamples.value = []
  imgPosterVersions.value = null
  uploadedImageBase64.value = uploadedImagePreview.value = ''
  selectedTemplate.value = null
  templateThumbnail.value = ''
  imgIsProcessing.value = false
  imgProgress.value = 0
  // 重置语音和直播脚本状态
  isRecording.value = false
  voiceInputText.value = ''
  generatedScript.value = ''
  enableLiveScript.value = false
  scriptGenerating.value = false
  aiPosterPrompt.value = ''
  aiPosterGenerating.value = false
  showAiPosterInput.value = false
  clearInterval(imgPollTimer)
  clearInterval(tipTimer)
  Object.keys(selectedTags).forEach(k => { selectedTags[k] = Array.isArray(selectedTags[k]) ? [] : '' })
}

const handleClickOutside = (e) => { if (!e.target.closest('.tag-fill-container')) activeMenu.value = null }
onMounted(async () => {
  document.addEventListener('click', handleClickOutside)
  if (window.feather) window.feather.replace()
  await fetchHistoryList()  // ← 后端加载历史记录（已替换本地存储）

  // ★ 从素材库跳转过来时，自动填充文本框
  const prefill = sessionStorage.getItem('prefill_text')
  if (prefill) {
    freeText.value = prefill
    sessionStorage.removeItem('prefill_text')
  }

  //  登录后自动加载注册时的产品图（只在没有图片时才加载）
  if (isLoggedIn() && !uploadedImageBase64.value) {
    const user = getUser()
    if (user?.id) {
      try {
        const profileRes = await fetch(`http://localhost:5000/api/user/${user.id}/profile`)
        const profile    = await profileRes.json()
        const primaryProduct = profile?.products?.find(p => p.is_primary) || profile?.products?.[0]
        if (primaryProduct?.id) {
          const imgRes = await fetch(`http://localhost:5000/api/product/${primaryProduct.id}/image`)
          if (imgRes.ok) {
            const imgData = await imgRes.json()
            if (imgData.image_base64) {
              uploadedImageBase64.value  = imgData.image_base64
              uploadedImagePreview.value = imgData.image_base64
            }
          }
        }
      } catch (e) {}
    }
  }
})
watch([submitted, activeMenu, historyOpen], () => {
  nextTick(() => { if (window.feather) window.feather.replace() })
})
</script>

<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }

.creation-wrapper { position: relative; width: 100%; min-height: 100vh; background: #f5f5f7; }

.view-8 {
  margin-left: 258px; width: calc(100% - 358px); min-width: 973px;
  min-height: 100vh; display: flex; flex-direction: column; padding: 0 40px;
  background: radial-gradient(circle at 15% 25%,rgba(139,195,74,.12) 0%,transparent 25%),
              radial-gradient(circle at 85% 75%,rgba(139,195,74,.1) 0%,transparent 30%),#f5f5f7;
}

.initial-content { display: flex; flex-direction: column; justify-content: center; min-height: 100vh; }

.welcome-title {
  font-size: 46px; font-weight: 600; text-align: center; margin: 0 0 80px;
  background: linear-gradient(135deg,#376b0d,#8bc34a);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}

.view-16 { position: relative; width: 100%; min-height: 340px; background: #fff; border-radius: 20px; border: 1.5px solid #e0e0e0; box-shadow: 0 8px 24px rgba(0,0,0,.06); }

/* 模板按钮（左上） */
.view-25 { position: absolute; top: 20px; left: 24px; width: 130px; height: 88px; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #fff; border-radius: 16px; border: 2px dashed #8bc34a; cursor: pointer; transition: all .3s; z-index: 12; overflow: hidden; }
.view-25:hover { background: #f1f8e9; transform: scale(1.04); border-style: solid; }
.btn-inner-hint { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.text-wrapper-17 { font-size: 44px; font-weight: 300; color: #8bc34a; line-height: 1; }
.btn-label { font-size: 11px; color: #8bc34a; font-weight: 500; }

/* 上传按钮（左下） */
.view-17 { position: absolute; bottom: 24px; left: 24px; width: 68px; height: 68px; display: flex; align-items: center; justify-content: center; background: #fff; border-radius: 50%; border: 2px dashed #8bc34a; cursor: pointer; transition: all .3s; z-index: 12; overflow: hidden; }
.view-17:hover { background: #f1f8e9; transform: scale(1.08); border-style: solid; }
.text-wrapper-14 { font-size: 44px; font-weight: 300; color: #8bc34a; line-height: 1; }

.thumbnail-preview { width: 100%; height: 100%; object-fit: cover; border-radius: 14px; }
.round-preview { border-radius: 50%; }
.selected-badge { position: absolute; top: -6px; right: -6px; background: #8bc34a; color: white; width: 22px; height: 22px; border-radius: 50%; font-size: 12px; font-weight: bold; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(0,0,0,.2); z-index: 15; }

/* 填空容器 */
.fill-container { position: absolute; top: 20px; left: 180px; width: calc(100% - 340px); min-height: 80px; font-size: 18px; line-height: 2.2; color: #333; background: #f8f9fa; border-radius: 12px; padding: 20px 24px; z-index: 20; }
.tag-fill-container { position: relative; display: inline-block; margin: 0 6px; }
.fill-btn { display: inline-flex; align-items: center; justify-content: center; background: #f1f8e9; border: none; cursor: pointer; transition: all .2s; font-weight: 500; color: #6a994e; font-size: 16px; border-radius: 30px; padding: 6px 18px; white-space: nowrap; min-width: 80px; }
.fill-btn:hover, .fill-btn.selected { background: #8bc34a; color: #fff; }
.tag-dropdown-popup { position: absolute; top: 100%; left: 0; transform: translateY(8px); width: 190px; background: #fff; border-radius: 12px; box-shadow: 0 12px 28px rgba(0,0,0,.2); padding: 8px 0; z-index: 2000; opacity: 0; visibility: hidden; transition: opacity .2s,visibility .2s; border: 1px solid #e0e0e0; }
.tag-dropdown-popup.active { opacity: 1; visibility: visible; }
.tag-dropdown-header { padding: 8px 16px; font-size: 12px; font-weight: 600; color: #888; border-bottom: 1px solid #f0f0f0; }
.tag-dropdown-options { display: flex; flex-direction: column; }
.tag-dropdown-option { display: flex; align-items: center; padding: 10px 16px; cursor: pointer; font-size: 14px; color: #333; border-left: 3px solid transparent; transition: all .2s; }
.tag-dropdown-option:hover { background: rgba(139,195,74,.08); border-left-color: #8bc34a; padding-left: 19px; }
.tag-dropdown-option.selected { background: rgba(139,195,74,.1); color: #6a994e; font-weight: 500; border-left-color: #8bc34a; }
.tag-dropdown-option .checkbox { width: 16px; height: 16px; border: 2px solid #ccc; border-radius: 4px; margin-right: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.tag-dropdown-option.selected .checkbox { background: #8bc34a; border-color: #8bc34a; }
.tag-dropdown-option.selected .checkbox::after { content: '✓'; color: white; font-size: 12px; font-weight: bold; }

.custom-textarea { position: absolute; bottom: 23px; left: 110px; right: 110px; min-height: 70px; padding: 14px 18px; border: 1.5px solid #d9e5c5; border-radius: 18px; font-size: 15px; color: #2c3e2f; background: rgba(255,255,255,.85); resize: vertical; z-index: 10; }
.custom-textarea:focus { outline: none; border-color: #8bc34a; }

.arrow-up-left-wrapper { position: absolute; bottom: 24px; right: 24px; width: 68px; height: 68px; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg,#8bc34a,#6a994e); border-radius: 50%; border: none; cursor: pointer; transition: all .3s; box-shadow: 0 6px 16px rgba(139,195,74,.3); z-index: 12; }
.arrow-up-left-wrapper:hover { transform: scale(1.08) rotate(10deg); }
.arrow-up-left-wrapper:disabled { opacity: .7; cursor: not-allowed; }
.arrow-up-left { width: 28px; height: 28px; color: white; }

.loading-spinner { width: 22px; height: 22px; border: 3px solid rgba(255,255,255,.4); border-top-color: white; border-radius: 50%; animation: spin .8s linear infinite; display: inline-block; }
.loading-spinner-sm { width: 14px; height: 14px; border: 2px solid rgba(255,255,255,.4); border-top-color: white; border-radius: 50%; animation: spin .8s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 结果卡片 ── */
.ai-result-card { background: #fff; border-radius: 24px; padding: 28px; box-shadow: 0 12px 36px rgba(0,0,0,.08); border: 1px solid #e9ecef; margin: 20px 0 10px; overflow-y: auto; }
.result-section { margin-bottom: 24px; padding: 20px; background: #f9fafb; border-radius: 16px; border: 1px solid #e9ecef; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 8px; }
.section-title { font-size: 18px; font-weight: 600; color: #2c3e2f; }
.header-actions { display: flex; align-items: center; gap: 8px; }
.product-badge { background: #e8f5e9; color: #2e7d32; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.region-badge  { background: #fff3e0; color: #e65100; padding: 3px 10px; border-radius: 20px; font-size: 12px; }
.copy-btn { background: transparent; border: none; cursor: pointer; color: #8bc34a; display: flex; align-items: center; padding: 4px; border-radius: 4px; }
.copy-btn i { width: 18px; height: 18px; }
.ai-text { font-size: 17px; line-height: 1.8; color: #4b5563; }
.ai-text-loading { display: flex; flex-direction: column; gap: 10px; }
.skeleton-line { height: 16px; background: linear-gradient(90deg,#f0f0f0 25%,#e8e8e8 50%,#f0f0f0 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 4px; }
.skeleton-line.short { width: 60%; }
.skeleton-line.medium { width: 80%; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* ── 进度条 ── */
.progress-card { background: linear-gradient(135deg,#f0f7e6,#e8f5e9); border: 1px solid #c5e1a5; border-radius: 14px; padding: 16px 18px; margin-bottom: 14px; }
.progress-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.progress-title { font-size: 14px; font-weight: 600; color: #2e7d32; flex: 1; }
.progress-pct   { font-size: 20px; font-weight: 700; color: #7dba28; }
.progress-bar-track { height: 10px; background: rgba(255,255,255,.7); border-radius: 10px; overflow: hidden; margin-bottom: 8px; }
.progress-bar-fill  { height: 100%; border-radius: 10px; background: linear-gradient(90deg,#7dba28,#a5d633); transition: width .4s ease; position: relative; overflow: hidden; }
.progress-shimmer   { position: absolute; inset: 0; background: linear-gradient(90deg,transparent 0%,rgba(255,255,255,.4) 50%,transparent 100%); background-size: 200% 100%; animation: shimmer 1.5s infinite; }
.progress-step { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #555; margin-bottom: 12px; }
.step-dot { width: 8px; height: 8px; border-radius: 50%; background: #7dba28; animation: pulse 1s ease-in-out infinite; flex-shrink: 0; }
@keyframes pulse { 0%,100% { opacity:1;transform:scale(1); } 50% { opacity:.5;transform:scale(1.3); } }
.step-bubbles { display: flex; gap: 8px; margin-bottom: 10px; }
.step-bubble { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 8px 6px; border-radius: 10px; font-size: 11px; transition: all .3s; border: 1px solid transparent; }
.step-bubble.wait   { background: rgba(255,255,255,.4); color: #aaa; }
.step-bubble.active { background: white; border-color: #7dba28; color: #2e7d32; font-weight: 600; box-shadow: 0 2px 8px rgba(125,186,40,.25); }
.step-bubble.done   { background: rgba(125,186,40,.12); color: #51830a; }
.progress-tip { font-size: 12px; color: #7dba28; text-align: center; padding: 6px; background: rgba(255,255,255,.5); border-radius: 8px; font-style: italic; }

/* ── 图片区 ── */
.view-10 { display: flex; gap: 16px; margin-bottom: 16px; }
.img-wrapper { flex: 1; height: 180px; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,.08); border: 2px solid transparent; cursor: pointer; position: relative; transition: all .3s; }
.img-wrapper:hover { transform: translateY(-3px); }
.img-wrapper.img-selected { border-color: #8bc34a; box-shadow: 0 0 0 3px rgba(139,195,74,.3); }
.poster-img { width: 100%; height: 100%; object-fit: cover; }
.poster-filter-label { position: absolute; bottom: 0; left: 0; right: 0; background: rgba(0,0,0,.5); color: white; font-size: 12px; text-align: center; padding: 4px; }
.poster-selected-mark { position: absolute; top: 8px; right: 8px; background: #8bc34a; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
.placeholder-image { width: 100%; height: 100%; background: #f1f8e9; display: flex; align-items: center; justify-content: center; color: #6a994e; font-weight: 500; }

/* 滤镜条 */
.filter-strip { background: #f0f5e8; border-radius: 12px; padding: 12px 14px; margin-bottom: 14px; }
.filter-strip-label { font-size: 13px; font-weight: 600; color: #6a994e; margin-bottom: 10px; }
.filter-strip-options { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 4px; }
.filter-option { display: flex; flex-direction: column; align-items: center; gap: 5px; cursor: pointer; flex-shrink: 0; padding: 6px 8px; border-radius: 10px; border: 2px solid transparent; transition: all .2s; }
.filter-option:hover { background: rgba(139,195,74,.1); }
.filter-option.active { border-color: #8bc34a; background: rgba(139,195,74,.12); }
.filter-thumb { width: 60px; height: 60px; object-fit: cover; border-radius: 8px; }
.filter-option-name { font-size: 11px; color: #555; white-space: nowrap; }
.filter-option.active .filter-option-name { color: #6a994e; font-weight: 700; }

.ai-tools-container { display: flex; justify-content: flex-end; }
.ai-tools { display: flex; gap: 12px; }
.view-13, .view-14 { height: 40px; padding: 0 18px; display: flex; align-items: center; gap: 6px; background: linear-gradient(135deg,#8bc34a,#6a994e); border-radius: 10px; border: none; cursor: pointer; font-weight: 500; color: #fff; font-size: 14px; transition: all .3s; }
.view-13:hover, .view-14:hover { transform: translateY(-2px); }
.view-13:disabled { opacity: .5; cursor: not-allowed; transform: none; }
.view-13 i, .view-14 i { width: 15px; height: 15px; }

.tag-source-hint { font-size: 11px; color: #aaa; }
.tags-list { display: flex; flex-wrap: wrap; gap: 8px; }
.hot-tag { background: #f1f8e9; color: #6a994e; padding: 6px 16px; border-radius: 30px; font-size: 14px; border: 1px solid #d9e5c5; cursor: pointer; transition: all .2s; user-select: none; }
.hot-tag:hover, .hot-tag.tag-copied { background: #8bc34a; color: white; transform: translateY(-2px); }

.result-rag { background: #fffdf7; border-color: #eadfca; }
.rag-list { display: grid; gap: 10px; }
.rag-item { background: #fff; border: 1px solid #eee2c9; border-radius: 12px; padding: 12px 14px; }
.rag-item-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 6px; }
.rag-platform { background: #f1f8e9; color: #51830a; border-radius: 999px; padding: 2px 8px; font-size: 11px; font-weight: 700; }
.rag-score { color: #a77c2b; font-size: 11px; }
.rag-title { color: #2c3e2f; font-size: 14px; font-weight: 700; margin-bottom: 4px; }
.rag-meta { color: #8a8f98; font-size: 12px; margin-bottom: 6px; }
.rag-body { color: #4b5563; font-size: 13px; line-height: 1.65; margin: 0; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }

.further-request { display: flex; align-items: center; gap: 16px; background: #fff; border-radius: 40px; padding: 8px 8px 8px 24px; box-shadow: 0 4px 20px rgba(0,0,0,.1); border: 1px solid #e0e0e0; margin-top: 24px; }
.further-input  { flex: 1; border: none; background: transparent; font-size: 16px; padding: 12px 0; outline: none; color: #333; }
.further-input::placeholder { color: #aaa; }
.further-btn { background: linear-gradient(135deg,#8bc34a,#6a994e); border: none; border-radius: 40px; padding: 12px 32px; color: white; font-weight: 500; cursor: pointer; transition: all .3s; min-width: 100px; display: flex; align-items: center; justify-content: center; gap: 6px; }
.further-btn:hover { transform: translateY(-2px); }
.further-btn:disabled { opacity: .7; cursor: not-allowed; transform: none; }

.view-26 { position: fixed; top: 0; right: 0; width: 100px; height: 100vh; background: #fff; box-shadow: -4px 0 20px rgba(0,0,0,.06); padding: 30px 10px; display: flex; flex-direction: column; align-items: center; z-index: 99; }
.history-button, .new-project-button, .logout-button { background: transparent; border: none; cursor: pointer; width: 52px; height: 52px; border-radius: 12px; margin-bottom: 20px; display: flex; align-items: center; justify-content: center; transition: all .3s; }
.history-button:hover, .new-project-button:hover { background: rgba(139,195,74,.1); transform: scale(1.08); }
.logout-button { margin-top: auto; margin-bottom: 20px; }
.logout-button:hover { background: rgba(220,53,69,.1); transform: scale(1.08); }
.history-icon, .new-project-icon { width: 28px; height: 28px; color: #666; }
.logout-icon { width: 24px; height: 24px; color: #999; }
.logout-button:hover .logout-icon { color: #dc3545; }

.view-8.submitted { overflow: hidden; padding-top: 20px; padding-bottom: 40px; height: 100vh; }
.view-8.submitted .ai-result-card { flex: 1; overflow-y: auto; margin: 0; min-height: 0; }
.hint-small { font-size: 12px; color: #aaa; }

/* ── 手机排版预览 ── */
.preview-section { background: #f0f5e6; }
.phone-preview-wrap { display: flex; justify-content: center; padding: 10px 0; }
.phone-frame {
  width: 280px; background: #1a1a1a; border-radius: 40px;
  padding: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.4);
  position: relative;
}
.phone-notch {
  width: 80px; height: 20px; background: #1a1a1a;
  border-radius: 0 0 14px 14px; margin: 0 auto 6px;
  position: relative; z-index: 2;
}
.phone-screen {
  background: white; border-radius: 30px; overflow: hidden;
  max-height: 520px; overflow-y: auto;
}
.phone-screen::-webkit-scrollbar { display: none; }

.preview-platform-bar {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 12px; border-bottom: 1px solid #f0f0f0;
}
.preview-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg,#8bc34a,#6a994e);
  color: white; font-size: 12px; font-weight: bold;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.preview-username { font-size: 13px; font-weight: 600; flex: 1; color: #333; }
.preview-follow {
  font-size: 11px; color: #8bc34a; border: 1px solid #8bc34a;
  border-radius: 10px; padding: 2px 8px;
}

.preview-img-area { width: 100%; }
.preview-poster { width: 100%; display: block; }
.preview-img-placeholder {
  width: 100%; height: 160px; background: #f5f5f5;
  display: flex; align-items: center; justify-content: center;
  color: #aaa; font-size: 13px;
}

.preview-text-area { padding: 10px 12px; }
.preview-content {
  font-size: 12px; line-height: 1.7; color: #333;
  display: -webkit-box; -webkit-line-clamp: 6;
  -webkit-box-orient: vertical; overflow: hidden;
}

.preview-tags-area {
  padding: 0 12px 8px; display: flex; flex-wrap: wrap; gap: 4px;
}
.preview-tag {
  font-size: 11px; color: #8bc34a; background: #f1f8e9;
  padding: 2px 8px; border-radius: 10px;
}

.preview-action-bar {
  display: flex; justify-content: space-around; padding: 10px 12px;
  border-top: 1px solid #f0f0f0; font-size: 12px; color: #888;
}

/* ── 移动端适配 ── */
@media (max-width: 768px) {
  .view-8 { margin-left: 0; width: 100%; min-width: unset; padding: 0 16px; }
  .view-26 { display: none; }   /* 移动端隐藏右侧操作栏 */
  .welcome-title { font-size: 28px; margin-bottom: 40px; }
  .fill-container { position: static; width: 100%; margin: 16px 0; }
  .custom-textarea { position: static; width: 100%; margin-top: 12px; }
  .view-16 { min-height: auto; padding-bottom: 80px; }
  .view-25 { top: 12px; left: 12px; width: 80px; height: 60px; }
  .view-17 { bottom: 16px; left: 12px; width: 52px; height: 52px; }
  .arrow-up-left-wrapper { bottom: 16px; right: 12px; width: 52px; height: 52px; }
  .view-10 { flex-direction: column; }
  .img-wrapper { height: 220px; }
  .filter-strip-options { gap: 8px; }
  .filter-thumb { width: 50px; height: 50px; }
  .ai-result-card { padding: 16px; border-radius: 16px; }
  .result-section { padding: 14px; }
  .further-request { padding: 6px 6px 6px 16px; }
  .further-btn { padding: 10px 20px; }
  .tags-list { gap: 6px; }
  .hot-tag { padding: 5px 12px; font-size: 13px; }
  .agent-list { gap: 6px; }
}

/* ── 文本输入框工具按钮 ── */
.textarea-wrapper {
  position: absolute;
  bottom: 23px;
  left: 110px;
  right: 110px;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.custom-textarea {
  flex: 1;
  min-height: 70px;
  padding: 14px 18px;
  border: 1.5px solid #d9e5c5;
  border-radius: 18px;
  font-size: 15px;
  color: #2c3e2f;
  background: rgba(255,255,255,.85);
  resize: vertical;
  z-index: 10;
}

.custom-textarea:focus {
  outline: none;
  border-color: #8bc34a;
}

.input-tools {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tool-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  background: #fff;
  border: 1.5px solid #d9e5c5;
  border-radius: 14px;
  cursor: pointer;
  transition: all .3s;
  position: relative;
}

.tool-btn:hover {
  background: #f1f8e9;
  border-color: #8bc34a;
  transform: translateY(-2px);
}

.tool-btn:disabled {
  opacity: .5;
  cursor: not-allowed;
  transform: none;
}

.tool-btn .tool-icon {
  width: 20px;
  height: 20px;
  color: #6a994e;
}

.tool-btn:hover .tool-icon {
  color: #8bc34a;
}

.tool-btn .tool-label {
  font-size: 10px;
  color: #6a994e;
  margin-top: 2px;
}

/* 语音按钮录制状态 */
.tool-btn.voice-btn.recording {
  background: linear-gradient(135deg, #ff6b6b, #ee5a5a);
  border-color: #ff6b6b;
  animation: pulse-glow 1.5s ease-in-out infinite;
}

.tool-btn.voice-btn.recording .tool-icon,
.tool-btn.voice-btn.recording .tool-label {
  color: white;
}

.recording-indicator {
  position: absolute;
  bottom: 4px;
  width: 8px;
  height: 8px;
  background: #fff;
  border-radius: 50%;
  animation: blink 1s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(255, 107, 107, 0); }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* ── 直播脚本勾选按钮 ── */
.tool-btn.script-btn:hover,
.tool-btn.script-btn.active {
  background: linear-gradient(135deg, #64b5f6, #42a5f5);
  border-color: #42a5f5;
}
.tool-btn.script-btn:hover .tool-icon,
.tool-btn.script-btn:hover .tool-label,
.tool-btn.script-btn.active .tool-icon,
.tool-btn.script-btn.active .tool-label {
  color: white;
}
.check-badge {
  position: absolute; top: -4px; right: -4px;
  width: 18px; height: 18px; border-radius: 50%;
  background: #4caf50; color: white; font-size: 11px;
  display: flex; align-items: center; justify-content: center;
  font-weight: bold; box-shadow: 0 2px 6px rgba(0,0,0,.2);
}

/* ── 工具按钮组（方言弹出框的锚点） ── */
.tool-btn-group { position: relative; }

/* ── 方言选择弹出框（附着在语音按钮上方） ── */
.dialect-popover {
  position: absolute; bottom: 110%; left: 50%;
  transform: translateX(-50%) scale(0.9);
  background: white; border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.18);
  padding: 6px; min-width: 110px;
  opacity: 0; visibility: hidden;
  transition: all .2s; z-index: 200;
}
.dialect-popover.active { opacity: 1; visibility: visible; transform: translateX(-50%) scale(1); }
.dialect-popover::after {
  content: ''; position: absolute; bottom: -6px; left: 50%;
  transform: translateX(-50%);
  border-left: 6px solid transparent; border-right: 6px solid transparent;
  border-top: 6px solid white;
}
.dialect-opt {
  display: block; width: 100%; padding: 8px 12px;
  background: transparent; border: none; border-radius: 8px;
  cursor: pointer; font-size: 12px; color: #333;
  text-align: center; transition: background .2s;
}
.dialect-opt:hover { background: #f1f8e9; }
.dialect-opt.selected { background: #e8f5e9; color: #6a994e; font-weight: 600; }

/* ── AI 海报生成按钮和输入区 ── */
.ai-poster-btn {
  height: 40px; padding: 0 18px;
  display: flex; align-items: center; gap: 6px;
  background: linear-gradient(135deg, #ff9800, #e65100);
  border-radius: 10px; border: none; cursor: pointer;
  font-weight: 500; color: #fff; font-size: 14px;
  transition: all .3s;
}
.ai-poster-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 14px rgba(255,152,0,.35); }
.ai-poster-btn i { width: 15px; height: 15px; }

.ai-poster-input-area {
  display: flex; gap: 10px; margin-top: 12px;
  background: #fff8e1; border: 1px solid #ffe0b2;
  border-radius: 12px; padding: 10px 14px;
  animation: fadeSlide .3s ease;
}
@keyframes fadeSlide { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: none; } }
.ai-poster-prompt {
  flex: 1; border: none; background: transparent;
  font-size: 14px; color: #333; outline: none;
}
.ai-poster-prompt::placeholder { color: #bbb; }
.ai-poster-gen-btn {
  padding: 8px 20px;
  background: linear-gradient(135deg, #ff9800, #e65100);
  color: white; border: none; border-radius: 8px;
  cursor: pointer; font-weight: 500; font-size: 13px;
  transition: all .2s; min-width: 60px;
  display: flex; align-items: center; justify-content: center;
}
.ai-poster-gen-btn:hover { transform: translateY(-1px); }
.ai-poster-gen-btn:disabled { opacity: .6; cursor: not-allowed; transform: none; }

/* ── 直播脚本内联结果区 ── */
.live-script-section {
  background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
  border: 1px solid #bbdefb;
}
.script-duration-select {
  padding: 4px 10px; border: 1px solid #d0d0d0; border-radius: 8px;
  background: white; font-size: 12px; color: #555; cursor: pointer;
  outline: none;
}
.refresh-btn {
  background: transparent; border: none; cursor: pointer;
  color: #8bc34a; padding: 4px; border-radius: 4px;
  display: flex; align-items: center;
}
.refresh-btn:hover { background: rgba(139,195,74,.1); }
.refresh-btn:disabled { opacity: .4; cursor: not-allowed; }
.refresh-btn i { width: 18px; height: 18px; }

.script-loading { display: flex; flex-direction: column; gap: 10px; }

.script-body {
  font-size: 15px; line-height: 1.9; color: #4b5563;
  max-height: 500px; overflow-y: auto;
  padding: 8px 0;
}
.script-body::-webkit-scrollbar { width: 4px; }
.script-body::-webkit-scrollbar-thumb { background: #c5cae9; border-radius: 4px; }

:deep(.script-h2) {
  font-size: 18px; font-weight: 700; color: #1a237e;
  margin: 16px 0 8px; padding-bottom: 6px;
  border-bottom: 2px solid rgba(26,35,126,.1);
}
:deep(.script-h3) {
  font-size: 15px; font-weight: 600; color: #42a5f5;
  margin: 14px 0 6px;
}
:deep(.script-action) {
  color: #e65100; font-style: italic; font-size: 13px;
}

</style>
