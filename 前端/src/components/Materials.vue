<template>
  <div class="materials-wrapper">
    <div class="page-header">
      <h2>📚 素材库</h2>
      <p class="sub">热点推荐 · 文案模板 · 运营技巧</p>
    </div>

    <!-- Tab 切换 -->
    <div class="tab-bar">
      <button v-for="tab in tabs" :key="tab.key"
        class="tab-btn" :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key">
        {{ tab.label }}
      </button>
    </div>

    <!-- ═══ Tab1：热点推荐 ═══ -->
    <div v-if="activeTab === 'hotspot'">

      <!-- 平台选择 + 刷新 -->
      <div class="hotspot-controls">
        <div class="platform-selector">
          <button v-for="p in platforms" :key="p.value"
            class="platform-btn" :class="{ active: hotPlatform === p.value }"
            @click="hotPlatform = p.value; loadHotspot()">
            {{ p.label }}
          </button>
        </div>
        <button class="btn-refresh" @click="loadHotspot" :disabled="hotLoading">
          <span v-if="hotLoading">⏳ 生成中…</span>
          <span v-else>🔄 换一批</span>
        </button>
      </div>

      <!-- 产品标识 -->
      <div class="product-hint" v-if="userProduct">
        <span class="hint-icon">🎯</span>
        <span>正在为「<strong>{{ userProduct }}</strong>」生成个性化热点</span>
        <span class="hint-sub">基于你的主推产品定制</span>
      </div>
      <div class="product-hint generic" v-else>
        <span class="hint-icon">🌾</span>
        <span>通用农产品运营热点</span>
        <span class="hint-sub">登录并登记产品后可获取个性化推荐</span>
      </div>

      <!-- 骨架屏 -->
      <div class="skeleton-list" v-if="hotLoading">
        <div v-for="n in 5" :key="n" class="skeleton-item">
          <div class="skeleton-line long"></div>
          <div class="skeleton-line short"></div>
        </div>
      </div>

      <!-- 热点列表 -->
      <div class="hotspot-list" v-else>
        <div v-for="(item, i) in hotspots" :key="i" class="hotspot-card">
          <div class="hot-rank" :class="i < 3 ? 'top' : ''">{{ i + 1 }}</div>
          <div class="hot-content">
            <div class="hot-title">{{ item.title }}</div>
            <div class="hot-angle">💡 {{ item.angle }}</div>
          </div>
          <div class="hot-meta">
            <span class="heat-badge" :class="item.heat">{{ item.heat }}热度</span>
            <button class="btn-use" @click="useHotspot(item)">用这个</button>
          </div>
        </div>
      </div>

      <!-- 运营技巧 -->
      <div class="tips-card" v-if="tips.length && !hotLoading">
        <div class="tips-title">📌 运营小技巧</div>
        <div class="tip-item" v-for="(tip, i) in tips" :key="i">
          <span class="tip-num">{{ i + 1 }}</span>
          <span>{{ tip }}</span>
        </div>
      </div>
    </div>

    <!-- ═══ Tab2：文案模板 ═══ -->
    <div v-if="activeTab === 'template'">

      <!-- 分类筛选 -->
      <div class="filter-bar">
        <button v-for="cat in templateCategories" :key="cat"
          class="filter-btn" :class="{ active: selectedCat === cat }"
          @click="selectedCat = cat">
          {{ cat }}
        </button>
      </div>

      <!-- 模板卡片 -->
      <div class="template-grid">
        <div v-for="tpl in filteredTemplates" :key="tpl.id" class="template-card">
          <div class="tpl-header">
            <span class="tpl-platform">{{ tpl.platform }}</span>
            <span class="tpl-cat">{{ tpl.category }}</span>
          </div>
          <div class="tpl-title">{{ tpl.title }}</div>
          <div class="tpl-preview">{{ tpl.content }}</div>
          <div class="tpl-footer">
            <span class="tpl-tags">{{ tpl.tags }}</span>
            <button class="btn-use-tpl" @click="useTemplate(tpl)">使用模板</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 使用提示 Toast -->
    <div class="toast" v-if="toastMsg" :class="{ show: toastMsg }">{{ toastMsg }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getUser, isLoggedIn } from '@/api'
import { useRouter } from 'vue-router'

const AI_API   = import.meta.env.VITE_AI_API || 'http://localhost:5001'
const MAIN_API = import.meta.env.VITE_HOST || 'http://localhost:5000'
const router   = useRouter()

// ── 状态 ──
const activeTab   = ref('hotspot')
const hotPlatform = ref('小红书')
const hotLoading  = ref(false)
const hotspots    = ref([])
const tips        = ref([])
const userProduct = ref('')
const toastMsg    = ref('')
const selectedCat = ref('全部')

const tabs = [
  { key: 'hotspot',  label: '🔥 热点推荐' },
  { key: 'template', label: '📝 文案模板' },
]

const platforms = [
  { value: '小红书', label: '📕 小红书' },
  { value: '抖音',   label: '🎵 抖音' },
  { value: '淘宝',   label: '🛒 淘宝' },
]

// ── 加载用户主推产品 ──
const loadUserProduct = async () => {
  if (!isLoggedIn()) return
  try {
    const user = getUser()
    const res  = await fetch(`${MAIN_API}/api/user/${user.id}/profile`)
    const data = await res.json()
    userProduct.value = data?.primary_product?.name || ''
  } catch {}
}

// ── 加载热点 ──
const loadHotspot = async () => {
  hotLoading.value = true
  hotspots.value   = []
  tips.value       = []
  try {
    const res  = await fetch(`${AI_API}/api/hotspot`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        product_name: userProduct.value,
        platform:     hotPlatform.value
      })
    })
    const data = await res.json()
    hotspots.value = data.hotspots || []
    tips.value     = data.tips     || []
  } catch (e) {
    console.error('热点加载失败:', e)
  } finally {
    hotLoading.value = false
  }
}

// ── 使用热点 → 跳转到创作页 ──
const useHotspot = (item) => {
  sessionStorage.setItem('prefill_text', item.title + '，' + item.angle)
  router.push('/creation')
  showToast('已填入创作框，请点击生成')
}

// ── Toast 提示 ──
const showToast = (msg) => {
  toastMsg.value = msg
  setTimeout(() => { toastMsg.value = '' }, 2500)
}

// ══════════════════════════════════
//  文案模板数据
// ══════════════════════════════════
const templateCategories = ['全部', '节日营销', '产品种草', '故事情感', '促销转化', '地域特色']

const templates = [
  {
    id: 1, platform: '小红书', category: '产品种草',
    title: '开门见山种草型',
    content: '【产品名】来啦！产自XX，XX特点，XX口感。自家种的，不打药，早上摘下来就发货，带着露水的新鲜。试试看？',
    tags: '#农家特产 #产地直供 #新鲜现摘'
  },
  {
    id: 2, platform: '小红书', category: '故事情感',
    title: '家乡味道情感型',
    content: '妈妈说，这个味道是家乡的味道。每次打开包裹，那熟悉的香气就出来了。不是因为多好吃，是因为每一颗都是用心种的。',
    tags: '#妈妈的味道 #家乡特产 #童年记忆'
  },
  {
    id: 3, platform: '抖音', category: '产品种草',
    title: '开门三秒抓眼球型',
    content: '这个XX真的绝了！！看我咬一口——汁水哗哗流，甜度刚刚好。产地直发，不过任何中间商，价格直接给到最低。',
    tags: '#三农 #助农 #产地直发'
  },
  {
    id: 4, platform: '抖音', category: '促销转化',
    title: '限时促销紧迫型',
    content: '今年收成不多，就这最后一批了！错过等明年。顺丰直达，坏果包赔。家人们，冲！',
    tags: '#限量供应 #今年最后一批 #支持助农'
  },
  {
    id: 5, platform: '小红书', category: '节日营销',
    title: '节日礼品推荐型',
    content: '送礼不知道选什么？这个XX绝对拿得出手！产自XX，获得XX认证，精美包装开箱就是惊喜。长辈收到都说好。',
    tags: '#送礼指南 #伴手礼推荐 #高颜值礼物'
  },
  {
    id: 6, platform: '淘宝', category: '促销转化',
    title: '卖点罗列信任型',
    content: '【产品名】✅产地直供 ✅当天现摘 ✅顺丰包邮 ✅坏果包赔 ✅支持7天退换。种了XX年，品质有保障，放心下单。',
    tags: '产地直供 现摘现发 坏果包赔'
  },
  {
    id: 7, platform: '小红书', category: '地域特色',
    title: '地域文化背书型',
    content: '来自XX的XX，这里山高水清，年均温度XX，是种植XX的天然宝地。几十年的老品种，不是大棚货，慢慢长大的才好吃。',
    tags: '#地标优选 #原生态 #大山馈赠'
  },
  {
    id: 8, platform: '抖音', category: '故事情感',
    title: '农户日记真实型',
    content: '今天凌晨4点就起来摘了，露水还没干，装箱封好，下午就能到你手里。种地苦，但看到大家喜欢吃，值了。',
    tags: '#我在大山卖特产 #新农人 #乡村振兴'
  },
]

const filteredTemplates = computed(() => {
  if (selectedCat.value === '全部') return templates
  return templates.filter(t => t.category === selectedCat.value)
})

// ── 使用模板 ──
const useTemplate = (tpl) => {
  sessionStorage.setItem('prefill_text', tpl.content)
  router.push('/creation')
  showToast('模板已填入，进入创作页可直接生成')
}

onMounted(async () => {
  await loadUserProduct()
  loadHotspot()
})
</script>

<style scoped>
.materials-wrapper { padding: 32px 40px; max-width: 900px; margin-left: 258px; min-height: 100vh; }
.page-header { margin-bottom: 24px; }
.page-header h2 { font-size: 24px; font-weight: 600; color: #2c3e2f; margin-bottom: 4px; }
.sub { font-size: 14px; color: #888; }

/* Tab */
.tab-bar { display: flex; gap: 8px; margin-bottom: 24px; border-bottom: 2px solid #f0f0f0; padding-bottom: 0; }
.tab-btn {
  padding: 10px 24px; background: none; border: none; cursor: pointer;
  font-size: 15px; color: #888; font-weight: 500; border-bottom: 2px solid transparent;
  margin-bottom: -2px; transition: all .2s;
}
.tab-btn:hover  { color: #6a994e; }
.tab-btn.active { color: #6a994e; border-bottom-color: #8bc34a; font-weight: 600; }

/* 热点控制栏 */
.hotspot-controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px; }
.platform-selector { display: flex; gap: 8px; }
.platform-btn {
  padding: 6px 16px; border-radius: 20px; border: 1px solid #e0e0e0;
  background: white; cursor: pointer; font-size: 13px; transition: all .2s;
}
.platform-btn:hover, .platform-btn.active { background: #8bc34a; color: white; border-color: #8bc34a; }
.btn-refresh {
  padding: 8px 18px; border-radius: 10px; border: 1px solid #8bc34a;
  color: #6a994e; background: white; cursor: pointer; font-size: 13px; font-weight: 500;
  transition: all .2s;
}
.btn-refresh:hover:not(:disabled) { background: #8bc34a; color: white; }
.btn-refresh:disabled { opacity: .6; cursor: wait; }

/* 产品提示 */
.product-hint {
  display: flex; align-items: center; gap: 8px; padding: 10px 16px;
  background: #f0f8e6; border-radius: 10px; margin-bottom: 16px;
  font-size: 13px; color: #2e7d32; border: 1px solid #c5e1a5;
}
.product-hint.generic { background: #f9fafb; color: #888; border-color: #e0e0e0; }
.hint-icon { font-size: 16px; }
.hint-sub  { color: #aaa; font-size: 12px; margin-left: auto; }

/* 骨架屏 */
.skeleton-list { display: flex; flex-direction: column; gap: 12px; }
.skeleton-item { background: white; border-radius: 12px; padding: 16px; border: 1px solid #e8e8e8; }
.skeleton-line {
  height: 14px; border-radius: 4px;
  background: linear-gradient(90deg,#f0f0f0 25%,#e8e8e8 50%,#f0f0f0 75%);
  background-size: 200% 100%; animation: shimmer 1.5s infinite; margin-bottom: 8px;
}
.skeleton-line.long  { width: 70%; }
.skeleton-line.short { width: 45%; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* 热点列表 */
.hotspot-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 24px; }
.hotspot-card {
  display: flex; align-items: center; gap: 14px; padding: 16px 18px;
  background: white; border-radius: 12px; border: 1px solid #e8e8e8;
  box-shadow: 0 2px 8px rgba(0,0,0,.04); transition: all .2s;
}
.hotspot-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,.08); border-color: #c5e1a5; }
.hot-rank {
  width: 28px; height: 28px; border-radius: 8px; flex-shrink: 0;
  background: #f0f0f0; color: #999; font-size: 14px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.hot-rank.top { background: linear-gradient(135deg,#ff6b35,#ff9a3c); color: white; }
.hot-content { flex: 1; min-width: 0; }
.hot-title   { font-size: 15px; font-weight: 600; color: #333; margin-bottom: 4px; }
.hot-angle   { font-size: 12px; color: #888; }
.hot-meta    { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; flex-shrink: 0; }
.heat-badge  { font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 500; }
.heat-badge.高 { background: #ffebee; color: #c62828; }
.heat-badge.中 { background: #fff3e0; color: #e65100; }
.heat-badge.低 { background: #f1f8e9; color: #2e7d32; }
.btn-use {
  padding: 5px 14px; border-radius: 8px; border: 1px solid #8bc34a;
  color: #6a994e; background: white; cursor: pointer; font-size: 12px; font-weight: 500;
  transition: all .2s; white-space: nowrap;
}
.btn-use:hover { background: #8bc34a; color: white; }

/* 运营技巧 */
.tips-card { background: linear-gradient(135deg,#f0f8e6,#e8f5e9); border-radius: 14px; padding: 18px 20px; border: 1px solid #c5e1a5; }
.tips-title { font-size: 15px; font-weight: 600; color: #2e7d32; margin-bottom: 12px; }
.tip-item   { display: flex; gap: 10px; align-items: flex-start; margin-bottom: 8px; font-size: 13px; color: #555; }
.tip-num    { width: 20px; height: 20px; border-radius: 50%; background: #8bc34a; color: white; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 1px; }

/* 模板 */
.filter-bar { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
.filter-btn {
  padding: 6px 16px; border-radius: 20px; border: 1px solid #e0e0e0;
  background: white; cursor: pointer; font-size: 13px; transition: all .2s;
}
.filter-btn:hover, .filter-btn.active { background: #8bc34a; color: white; border-color: #8bc34a; }

.template-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px,1fr)); gap: 16px; }
.template-card {
  background: white; border-radius: 14px; padding: 18px;
  border: 1px solid #e8e8e8; box-shadow: 0 2px 8px rgba(0,0,0,.04);
  display: flex; flex-direction: column; gap: 10px; transition: all .2s;
}
.template-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,.1); border-color: #c5e1a5; }
.tpl-header { display: flex; gap: 6px; }
.tpl-platform, .tpl-cat { padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 500; }
.tpl-platform { background: #e8f5e9; color: #2e7d32; }
.tpl-cat      { background: #e3f2fd; color: #1565c0; }
.tpl-title    { font-size: 15px; font-weight: 600; color: #333; }
.tpl-preview  {
  font-size: 13px; color: #666; line-height: 1.7; background: #f9fafb;
  padding: 10px 12px; border-radius: 8px; border-left: 3px solid #c5e1a5;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
.tpl-footer   { display: flex; justify-content: space-between; align-items: center; margin-top: auto; }
.tpl-tags     { font-size: 11px; color: #8bc34a; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.btn-use-tpl  {
  padding: 6px 16px; border-radius: 8px; border: none;
  background: linear-gradient(135deg,#8bc34a,#6a994e); color: white;
  cursor: pointer; font-size: 12px; font-weight: 500; white-space: nowrap;
  transition: all .2s; flex-shrink: 0;
}
.btn-use-tpl:hover { transform: scale(1.05); }

/* Toast */
.toast {
  position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%) translateY(20px);
  background: rgba(0,0,0,.8); color: white; padding: 12px 24px;
  border-radius: 24px; font-size: 14px; opacity: 0; transition: all .3s; pointer-events: none; z-index: 9999;
}
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

@media (max-width: 768px) {
  .materials-wrapper { margin-left: 0; padding: 20px 16px; }
  .template-grid { grid-template-columns: 1fr; }
}
</style>
