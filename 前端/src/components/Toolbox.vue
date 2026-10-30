<template>
  <div class="toolbox-wrapper">
    <div class="toolbox-header">
      <h2 class="toolbox-title">🧰 工具箱</h2>
      <p class="toolbox-sub">补充你的个人/公司信息，AI 生成文案时会智能调用</p>
    </div>

    <!-- 核心功能：个人/公司信息补充 -->
    <div class="tool-card">
      <div class="tool-card-header">
        <div class="tool-icon">🏆</div>
        <div>
          <div class="tool-name">个人 / 公司信息补充</div>
          <div class="tool-desc">填写获奖经历、种植年限、合作客户等，AI 会在合适时机融入文案</div>
        </div>
      </div>

      <!-- 示例提示 -->
      <div class="example-hints">
        <div class="example-label">💡 可以这样写：</div>
        <div class="example-tags">
          <span v-for="ex in examples" :key="ex" class="example-tag"
            @click="appendExample(ex)">{{ ex }}</span>
        </div>
      </div>

      <!-- 输入框 -->
      <textarea
        v-model="infoText"
        class="info-textarea"
        rows="5"
        placeholder="随意填写，比如：
我们家种板栗已经有30年了，父亲那辈就开始种。2023年参加梅州农博会获得银奖。目前合作了20多家餐厅和酒店。采用古法炒制，不加任何添加剂。"
      ></textarea>

      <div class="action-row">
        <button class="btn-save" @click="saveInfo" :disabled="saving || !infoText.trim()">
          {{ saving ? '保存中…' : '💾 保存到 AI 记忆' }}
        </button>
        <button class="btn-clear" @click="clearInfo" v-if="savedItems.length">
          🗑️ 清除所有记忆
        </button>
      </div>

      <div class="save-tip success" v-if="saveSuccess">{{ saveSuccess }}</div>
      <div class="save-tip error"   v-if="saveError">{{ saveError }}</div>
    </div>

    <!-- 已存储的信息展示 -->
    <div class="tool-card" v-if="savedItems.length">
      <div class="tool-card-header">
        <div class="tool-icon">🧠</div>
        <div>
          <div class="tool-name">AI 已记住的信息（{{ savedItems.length }} 条）</div>
          <div class="tool-desc">生成文案时会根据语义相关性自动选用，不会每次都全部塞入</div>
        </div>
      </div>
      <div class="memory-list">
        <div v-for="(item, idx) in savedItems" :key="item.chunk_id || idx" class="memory-item">
          <span class="memory-dot">•</span>
          <span class="memory-text">{{ item.text || item }}</span>
          <!-- 逐条删除按钮 -->
          <button class="delete-single-btn" @click="deleteSingleItem(idx, item.chunk_id)" title="删除这条记忆">
            🗑️
          </button>
        </div>
      </div>
    </div>

    <!-- 向量库未安装提示 -->
    <div class="tool-card warn-card" v-if="noChroma">
      <div class="tool-icon">⚠️</div>
      <div>
        <div class="tool-name">向量数据库未安装</div>
        <div class="tool-desc">需要安装 chromadb 才能使用此功能：</div>
        <code class="install-code">pip install chromadb</code>
      </div>
    </div>

    <!-- 占位：未来可以加更多工具 -->
    <div class="tool-card coming-soon">
      <div class="tool-icon">🔜</div>
      <div>
        <div class="tool-name">更多工具即将上线</div>
        <div class="tool-desc">批量生成、素材库管理、文案风格测试…</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getUser } from '@/api'

const MAIN_API = import.meta.env.VITE_HOST || 'http://localhost:5000'

const infoText = ref('')
const saving = ref(false)
const saveSuccess = ref('')
const saveError = ref('')
const savedItems = ref([])
const noChroma = ref(false)

const examples = [
  '点击添加：获奖经历',
  '点击添加：种植年限',
  '点击添加：合作客户',
  '点击添加：产品认证',
  '点击添加：生产工艺',
]

const exampleTexts = {
  '点击添加：获奖经历': '我们在2023年获得了广东省农业博览会银奖。',
  '点击添加：种植年限': '我们家已经种植这个产品超过20年，是祖传的老品种。',
  '点击添加：合作客户': '目前已经和30多家本地餐厅、酒店建立了长期合作关系。',
  '点击添加：产品认证': '产品已获得绿色食品认证和无公害农产品认证。',
  '点击添加：生产工艺': '采用传统古法加工工艺，全程不添加任何防腐剂和添加剂。',
}

const appendExample = (label) => {
  const text = exampleTexts[label] || ''
  infoText.value = (infoText.value + '\n' + text).trim()
}

// 保存信息（你原来的逻辑）
const saveInfo = async () => {
  if (!infoText.value.trim()) return
  const user = getUser()
  if (!user?.id) {
    saveError.value = '请先登录'
    return
  }

  saving.value = true
  saveSuccess.value = ''
  saveError.value = ''

  try {
    const res = await fetch(`${MAIN_API}/api/user/extra-info`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user.id, text: infoText.value })
    })
    const data = await res.json()

    if (data.success) {
      saveSuccess.value = `✅ 已存入 ${data.saved_chunks} 条信息片段，AI 下次生成时会参考`
      infoText.value = ''
      setTimeout(() => {
        saveSuccess.value = ''
      }, 4000)
      await loadSavedItems() // ← 重点：保存后立即刷新列表
    } else {
      noChroma.value = true
      saveError.value = data.message || '保存失败'
    }
  } catch (e) {
    saveError.value = '连接后端失败，请确认 main.py 已启动'
  } finally {
    saving.value = false
  }
}

// 加载已存储的信息（加强版，页面一打开就刷新）
const loadSavedItems = async () => {
  const user = getUser()
  if (!user?.id) return
  try {
    const res = await fetch(`${MAIN_API}/api/user/${user.id}/extra-info`)
    const data = await res.json()
    savedItems.value = data.items || []
  } catch (e) {
    console.warn('加载记忆列表失败', e)
  }
}

// 新增：逐条删除
const deleteSingleItem = async (index, chunkId) => {
  if (!confirm('确定删除这条记忆吗？')) return
  const user = getUser()
  if (!user?.id) return

  try {
    const idToDelete = chunkId || index
    await fetch(`${MAIN_API}/api/user/${user.id}/extra-info/${idToDelete}`, {
      method: 'DELETE'
    })
    savedItems.value.splice(index, 1)
  } catch (e) {
    alert('删除失败，请稍后重试')
  }
}

// 清除所有
const clearInfo = async () => {
  if (!confirm('确认清除所有 AI 记忆？')) return
  const user = getUser()
  if (!user?.id) return
  try {
    await fetch(`${MAIN_API}/api/user/${user.id}/extra-info`, {
      method: 'DELETE'
    })
    savedItems.value = []
    saveSuccess.value = '已清除所有记忆'
    setTimeout(() => {
      saveSuccess.value = ''
    }, 2000)
  } catch {}
}

onMounted(() => {
  loadSavedItems() // ← 页面一打开就立即加载
})
</script>

<style scoped>
/* 你原来的所有样式保持不变，只在下面加了一点点删除按钮的样式 */
.toolbox-wrapper {
  padding: 32px 40px;
  max-width: 800px;
  margin-left: 258px;
  min-height: 100vh;
}
.toolbox-header {
  margin-bottom: 28px;
}
.toolbox-title {
  font-size: 24px;
  font-weight: 600;
  color: #2c3e2f;
  margin-bottom: 6px;
}
.toolbox-sub {
  font-size: 14px;
  color: #888;
}

.tool-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, .07);
  margin-bottom: 20px;
  border: 1px solid #e8e8e8;
}
.tool-card-header {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  margin-bottom: 18px;
}
.tool-icon {
  font-size: 28px;
  flex-shrink: 0;
}
.tool-name {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e2f;
  margin-bottom: 4px;
}
.tool-desc {
  font-size: 13px;
  color: #888;
  line-height: 1.5;
}

.example-hints {
  margin-bottom: 12px;
}
.example-label {
  font-size: 12px;
  color: #aaa;
  margin-bottom: 8px;
}
.example-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.example-tag {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  background: #f0f5e6;
  color: #6a994e;
  border: 1px solid #c5e1a5;
  cursor: pointer;
  transition: all .2s;
}
.example-tag:hover {
  background: #8bc34a;
  color: white;
  border-color: #8bc34a;
}

.info-textarea {
  width: 100%;
  padding: 14px;
  border: 1.5px solid #e0e0e0;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.7;
  resize: vertical;
  box-sizing: border-box;
  color: #333;
  transition: border-color .2s;
}
.info-textarea:focus {
  outline: none;
  border-color: #8bc34a;
  box-shadow: 0 0 0 3px rgba(139, 195, 74, .1);
}

.action-row {
  display: flex;
  gap: 12px;
  margin-top: 14px;
}
.btn-save {
  background: linear-gradient(135deg, #8bc34a, #6a994e);
  color: white;
  border: none;
  border-radius: 10px;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all .3s;
}
.btn-save:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(139, 195, 74, .3);
}
.btn-save:disabled {
  opacity: .6;
  cursor: not-allowed;
}
.btn-clear {
  background: #fff5f5;
  color: #e53e3e;
  border: 1px solid #fed7d7;
  border-radius: 10px;
  padding: 10px 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all .2s;
}
.btn-clear:hover {
  background: #e53e3e;
  color: white;
}

.save-tip {
  margin-top: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
}
.save-tip.success {
  background: #e8f5e9;
  color: #2e7d32;
}
.save-tip.error {
  background: #ffebee;
  color: #c62828;
}

.memory-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.memory-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: #f9fafb;
  border-radius: 8px;
  font-size: 13px;
  color: #555;
  border-left: 3px solid #8bc34a;
}
.memory-text {
  flex: 1;
}
.memory-dot {
  color: #8bc34a;
  font-weight: bold;
  flex-shrink: 0;
}

.delete-single-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  color: #999;
}
.delete-single-btn:hover {
  background: #fee;
  color: #e74c3c;
}

.warn-card {
  border-color: #fed7aa;
  background: #fff8f0;
  display: flex;
  gap: 14px;
  align-items: center;
}
.install-code {
  display: inline-block;
  margin-top: 8px;
  background: #1a1a2e;
  color: #7dba28;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
}

.coming-soon {
  opacity: .5;
}

@media (max-width: 768px) {
  .toolbox-wrapper {
    margin-left: 0;
    padding: 20px 16px;
  }
}
</style>
