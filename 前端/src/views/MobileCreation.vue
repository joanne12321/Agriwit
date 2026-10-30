<template>
  <main class="mobile-shell">
    <section class="mobile-hero">
      <div>
        <p class="mobile-kicker">云稼集 Agriwit</p>
        <h1>填表生成农产品宣传方案</h1>
        <p class="mobile-subtitle">
          面向农户的手机端入口，填写产品信息后生成文案、标签、风险提示和参考案例。
        </p>
      </div>
      <RouterLink class="desktop-link" to="/creation">进入完整版</RouterLink>
    </section>

    <section class="panel form-panel" aria-label="产品信息表单">
      <div class="section-title">
        <span>产品信息</span>
        <small>6 项以内，先把主流程跑通</small>
      </div>

      <label class="field">
        <span>产品名称</span>
        <input v-model.trim="form.productName" placeholder="例如：梅州金柚" />
      </label>

      <div class="field-grid">
        <label class="field">
          <span>产品品类</span>
          <select v-model="form.category">
            <option value="">请选择</option>
            <option value="水果">水果</option>
            <option value="蔬菜">蔬菜</option>
            <option value="茶叶">茶叶</option>
            <option value="粮油">粮油</option>
            <option value="加工食品">加工食品</option>
          </select>
        </label>

        <label class="field">
          <span>目标平台</span>
          <select v-model="form.platform">
            <option value="小红书">小红书</option>
            <option value="抖音">抖音</option>
            <option value="淘宝">淘宝</option>
            <option value="朋友圈">朋友圈</option>
          </select>
        </label>
      </div>

      <label class="field">
        <span>产地</span>
        <input v-model.trim="form.origin" placeholder="例如：广东梅州" />
      </label>

      <label class="field">
        <span>核心卖点</span>
        <textarea
          v-model.trim="form.sellingPoints"
          placeholder="例如：老树种植、清甜多汁、坏果包赔、适合送礼"
        />
      </label>

      <label class="field">
        <span>目标人群</span>
        <select v-model="form.targetUser">
          <option value="">大众消费者</option>
          <option value="年轻人">年轻人</option>
          <option value="家庭用户">家庭用户</option>
          <option value="孕产妈妈">孕产妈妈</option>
          <option value="银发族">银发族</option>
          <option value="送礼人群">送礼人群</option>
          <option value="减脂健身人群">减脂健身人群</option>
        </select>
      </label>

      <button class="primary-action" type="button" :disabled="loading" @click="generate">
        {{ loading ? '正在生成' : '开始生成宣传方案' }}
      </button>

      <p class="form-note">
        当前是 H5 演示版，保留最短路径。登录后仍会自动读取已有用户档案和产品记忆。
      </p>
    </section>

    <section v-if="loading" class="panel progress-panel" aria-live="polite">
      <div class="step active">读取产品信息</div>
      <div class="step active">匹配参考案例</div>
      <div class="step">生成平台文案</div>
      <div class="step">检查风险表达</div>
    </section>

    <section v-if="error" class="panel error-panel">
      <strong>生成失败</strong>
      <p>{{ error }}</p>
    </section>

    <section v-if="content" class="panel result-panel">
      <div class="section-title result-title">
        <span>宣传文案</span>
        <button type="button" @click="copyText(content)">复制</button>
      </div>
      <p class="generated-copy">{{ content }}</p>
    </section>

    <section v-if="tags.length" class="panel">
      <div class="section-title">
        <span>推荐标签</span>
        <button type="button" @click="copyText(tags.join(' '))">复制全部</button>
      </div>
      <div class="tag-list">
        <button v-for="tag in tags" :key="tag" type="button" @click="copyText(tag)">
          {{ tag }}
        </button>
      </div>
    </section>

    <section v-if="ragExamples.length" class="panel">
      <div class="section-title">
        <span>参考案例</span>
        <small>来自本地农业文案数据集</small>
      </div>
      <article v-for="item in ragExamples.slice(0, 3)" :key="`${item.title}-${item.score}`" class="case-card">
        <div class="case-meta">
          <span>{{ item.platform || '数据集' }}</span>
          <span>匹配度 {{ Number(item.score || 0).toFixed(1) }}</span>
        </div>
        <h2>{{ item.title || item.product_name }}</h2>
        <p>{{ item.body }}</p>
      </article>
    </section>
  </main>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { generateContent } from '../api'

const form = reactive({
  productName: '',
  category: '',
  origin: '',
  sellingPoints: '',
  platform: '小红书',
  targetUser: ''
})

const loading = ref(false)
const error = ref('')
const content = ref('')
const tags = ref([])
const ragExamples = ref([])

const generate = async () => {
  if (!form.productName) {
    error.value = '请先填写产品名称。'
    return
  }

  loading.value = true
  error.value = ''
  content.value = ''
  tags.value = []
  ragExamples.value = []

  try {
    const data = await generateContent({
      product_name: form.productName,
      platform: form.platform,
      target_user_hint: form.targetUser,
      supplemental_info: [
        form.category ? `产品品类：${form.category}` : '',
        form.origin ? `产地：${form.origin}` : '',
        form.sellingPoints ? `核心卖点：${form.sellingPoints}` : ''
      ].filter(Boolean).join('；'),
      word_count_hint: '100到120字',
      word_count_target: 120
    })

    content.value = data.content || ''
    tags.value = data.recommended_tags || []
    ragExamples.value = data.rag_examples || []
    if (!content.value) error.value = '服务已响应，但没有返回文案内容。'
  } catch (err) {
    error.value = err?.message || '无法连接 AI 服务，请确认后端已经启动。'
  } finally {
    loading.value = false
  }
}

const copyText = async (text) => {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    const input = document.createElement('textarea')
    input.value = text
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    input.remove()
  }
}
</script>

<style scoped>
.mobile-shell {
  min-height: 100dvh;
  width: 100%;
  max-width: 560px;
  margin: 0 auto;
  padding: 18px 16px 40px;
  background: #f5f7f2;
  color: #203027;
}

.mobile-hero {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 8px 0 18px;
}

.mobile-kicker {
  margin: 0 0 8px;
  color: #3d6b3d;
  font-size: 13px;
  font-weight: 800;
}

.mobile-hero h1 {
  max-width: 9em;
  margin: 0;
  font-size: 30px;
  line-height: 1.12;
  letter-spacing: 0;
}

.mobile-subtitle {
  margin: 10px 0 0;
  color: #66766c;
  font-size: 15px;
  line-height: 1.6;
}

.desktop-link {
  flex: 0 0 auto;
  align-self: flex-start;
  border: 1px solid #cad8c7;
  border-radius: 999px;
  padding: 8px 12px;
  color: #315f32;
  background: #ffffff;
  font-size: 13px;
  font-weight: 800;
  text-decoration: none;
}

.panel {
  margin-top: 14px;
  border: 1px solid #dce6d7;
  border-radius: 14px;
  padding: 16px;
  background: #ffffff;
  box-shadow: 0 8px 26px rgba(32, 48, 39, 0.06);
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  color: #203027;
  font-size: 17px;
  font-weight: 850;
}

.section-title small {
  color: #7a867d;
  font-size: 12px;
  font-weight: 650;
}

.section-title button {
  border: 1px solid #cad8c7;
  border-radius: 999px;
  padding: 7px 12px;
  color: #315f32;
  background: #ffffff;
  font-size: 13px;
  font-weight: 800;
}

.form-panel {
  display: grid;
  gap: 13px;
}

.field-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.field {
  display: grid;
  gap: 7px;
  color: #2e3d33;
  font-size: 14px;
  font-weight: 800;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  border: 1px solid #cbd8c5;
  border-radius: 10px;
  padding: 12px;
  background: #fbfcfa;
  color: #203027;
  font: inherit;
  font-weight: 650;
  outline: none;
}

.field textarea {
  min-height: 88px;
  resize: vertical;
  line-height: 1.55;
}

.field input:focus,
.field select:focus,
.field textarea:focus {
  border-color: #3d6b3d;
  box-shadow: 0 0 0 3px rgba(61, 107, 61, 0.13);
}

.primary-action {
  width: 100%;
  border: 0;
  border-radius: 12px;
  padding: 15px 16px;
  background: #315f32;
  color: #ffffff;
  font-size: 16px;
  font-weight: 850;
  cursor: pointer;
}

.primary-action:active {
  transform: translateY(1px);
}

.primary-action:disabled {
  opacity: 0.68;
  cursor: not-allowed;
}

.form-note {
  margin: 0;
  color: #758179;
  font-size: 12px;
  line-height: 1.55;
}

.progress-panel {
  display: grid;
  gap: 8px;
}

.step {
  border-radius: 10px;
  padding: 10px 12px;
  background: #f1f5ee;
  color: #637066;
  font-size: 14px;
  font-weight: 760;
}

.step.active {
  color: #315f32;
  background: #e7f1e4;
}

.error-panel {
  border-color: #efc6b9;
  background: #fff7f4;
  color: #8a341f;
}

.error-panel p {
  margin: 6px 0 0;
  line-height: 1.6;
}

.generated-copy {
  margin: 0;
  white-space: pre-wrap;
  color: #344339;
  font-size: 16px;
  line-height: 1.8;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-list button {
  border: 1px solid #d2e0cd;
  border-radius: 999px;
  padding: 7px 12px;
  background: #f1f7ee;
  color: #315f32;
  font-weight: 800;
}

.case-card {
  border-top: 1px solid #e5ece1;
  padding-top: 12px;
}

.case-card + .case-card {
  margin-top: 12px;
}

.case-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: #718076;
  font-size: 12px;
  font-weight: 750;
}

.case-card h2 {
  margin: 6px 0;
  color: #203027;
  font-size: 15px;
  line-height: 1.35;
}

.case-card p {
  display: -webkit-box;
  margin: 0;
  overflow: hidden;
  color: #526158;
  font-size: 13px;
  line-height: 1.65;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

@media (max-width: 420px) {
  .mobile-shell {
    padding-inline: 14px;
  }

  .mobile-hero {
    display: block;
  }

  .desktop-link {
    display: inline-flex;
    margin-top: 14px;
  }

  .field-grid {
    grid-template-columns: 1fr;
  }
}
</style>
