<template>
  <div class="manage-wrapper">
    <div class="manage-header">
      <h2 class="manage-title">产品管理</h2>
      <button class="btn-add" @click="showAddModal = true">+ 添加新产品</button>
    </div>

    <!-- 加载中 -->
    <div class="loading-box" v-if="loading">加载中…</div>

    <!-- 无产品提示 -->
    <div class="empty-box" v-else-if="products.length === 0">
      <div class="empty-icon">🌾</div>
      <p>还没有登记产品</p>
      <button class="btn-add" @click="showAddModal = true">立即添加</button>
    </div>

    <!-- 产品卡片列表 -->
    <div class="product-grid" v-else>
      <div v-for="p in products" :key="p.id" class="product-card"
        :class="{ primary: p.is_primary }">

        <!-- 主推标记 -->
        <div class="primary-badge" v-if="p.is_primary">主推</div>

        <!-- 产品图 -->
        <div class="product-img-wrap">
          <img v-if="p.image_base64" :src="p.image_base64" class="product-img" />
          <div v-else class="product-img-placeholder">🌿</div>
          <label class="img-upload-btn" :for="'img-' + p.id" title="更换图片">📷</label>
          <input :id="'img-' + p.id" type="file" accept="image/*"
            style="display:none" @change="e => uploadImage(p, e)" />
        </div>

        <!-- 信息 -->
        <div class="product-info">
          <div class="product-name">{{ p.name }}</div>
          <div class="product-meta">
            <span class="meta-tag">{{ CATEGORY_LABELS[p.category] || p.category }}</span>
            <span class="meta-origin">📍 {{ p.origin }}</span>
          </div>
          <div class="product-keywords" v-if="p.keywords && p.keywords.length">
            <span v-for="kw in p.keywords" :key="kw" class="kw-tag">{{ kw }}</span>
          </div>
        </div>

        <!-- 操作 -->
        <div class="product-actions">
          <button v-if="!p.is_primary" class="btn-primary-set" @click="setPrimary(p)">
            设为主推
          </button>
          <button class="btn-edit" @click="startEdit(p)">编辑</button>
          <button class="btn-delete" @click="deleteProduct(p)">删除</button>
        </div>
      </div>
    </div>

    <!-- 添加/编辑产品弹窗 -->
    <div class="modal-overlay" v-if="showAddModal || editingProduct" @click.self="closeModal">
      <div class="modal-box">
        <div class="modal-header">
          <h3>{{ editingProduct ? '编辑产品' : '添加新产品' }}</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>

        <div class="modal-body">
          <div class="form-row">
            <label>产品名称 *</label>
            <input v-model="form.name" placeholder="例如：梅州金柚" />
          </div>
          <div class="form-row">
            <label>产品类别 *</label>
            <select v-model="form.category">
              <option value="">请选择</option>
              <option v-for="(label, val) in CATEGORY_LABELS" :key="val" :value="val">
                {{ label }}
              </option>
            </select>
          </div>
          <div class="form-row">
            <label>产地（精确到村镇）*</label>
            <input v-model="form.origin" placeholder="例如：xx镇xx村" />
          </div>
          <div class="form-row">
            <label>产品特点关键词（点击选择）</label>
            <div class="keyword-options">
              <span v-for="kw in keywordOptions" :key="kw"
                class="kw-option" :class="{ selected: form.keywords.includes(kw) }"
                @click="toggleKw(kw)">{{ kw }}</span>
            </div>
          </div>
          <div class="form-row">
            <label>简短描述</label>
            <textarea v-model="form.description" rows="2"
              placeholder="一句话介绍产品特色，如：种植在海拔800米沙地，粉糯香甜"></textarea>
          </div>
          <div class="error-msg" v-if="formError">{{ formError }}</div>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="closeModal">取消</button>
          <button class="btn-save" @click="saveProduct" :disabled="saving">
            {{ saving ? '保存中…' : (editingProduct ? '保存修改' : '添加产品') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getUser } from '@/api'

const MAIN_API = 'http://localhost:5000'

const CATEGORY_LABELS = {
  fruit: '水果', vegetable: '蔬菜', grain: '粮油',
  tea: '茶叶', meat_egg: '畜牧/肉蛋', aquatic: '水产',
  processed: '加工品', other: '其他'
}

const keywordOptions = ['有机', '送礼', '童年味道', '新潮国风', '地理标志',
  '非遗', '产地直供', '绿色食品', '高山种植', '传统工艺', '新鲜直达', '限量供应']

// ── 状态 ──
const loading        = ref(false)
const saving         = ref(false)
const products       = ref([])
const showAddModal   = ref(false)
const editingProduct = ref(null)
const formError      = ref('')

const form = reactive({
  name: '', category: '', origin: '', keywords: [], description: ''
})

// ── 加载产品列表 ──
const loadProducts = async () => {
  const user = getUser()
  if (!user?.id) return
  loading.value = true
  try {
    const res  = await fetch(`${MAIN_API}/api/user/${user.id}/profile`)
    const data = await res.json()
    const list = data.products || []

    // 尝试加载每个产品的图片
    for (const p of list) {
      try {
        const imgRes = await fetch(`${MAIN_API}/api/product/${p.id}/image`)
        if (imgRes.ok) {
          const imgData = await imgRes.json()
          p.image_base64 = imgData.image_base64 || ''
        }
      } catch {}
    }
    products.value = list
  } catch (e) {
    console.error('加载产品失败:', e)
  } finally {
    loading.value = false
  }
}

// ── 设为主推 ──
const setPrimary = async (product) => {
  const user = getUser()
  try {
    await fetch(`${MAIN_API}/api/product/${product.id}/set-primary`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user.id })
    })
    await loadProducts()
  } catch (e) { alert('操作失败') }
}

// ── 编辑 ──
const startEdit = (p) => {
  editingProduct.value = p
  Object.assign(form, {
    name: p.name, category: p.category,
    origin: p.origin, keywords: [...(p.keywords || [])],
    description: p.description || ''
  })
}

// ── 保存产品（新增或编辑）──
const saveProduct = async () => {
  formError.value = ''
  if (!form.name.trim())     { formError.value = '请输入产品名称'; return }
  if (!form.category)        { formError.value = '请选择产品类别'; return }
  if (!form.origin.trim())   { formError.value = '请输入产品产地'; return }

  saving.value = true
  const user = getUser()

  try {
    if (editingProduct.value) {
      // 编辑：调更新接口
      const res = await fetch(`${MAIN_API}/api/product/${editingProduct.value.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.name, category: form.category, origin: form.origin,
          keywords: form.keywords, description: form.description
        })
      })
      if (!res.ok) throw new Error('更新失败')
    } else {
      // 新增
      const res = await fetch(`${MAIN_API}/api/product/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.id, name: form.name, category: form.category,
          origin: form.origin, keywords: form.keywords,
          description: form.description, is_primary: products.value.length === 0
        })
      })
      if (!res.ok) throw new Error('添加失败')
    }
    await loadProducts()
    closeModal()
  } catch (e) {
    formError.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

// ── 删除 ──
const deleteProduct = async (p) => {
  if (!confirm(`确认删除产品「${p.name}」？此操作不可恢复。`)) return
  try {
    await fetch(`${MAIN_API}/api/product/${p.id}`, { method: 'DELETE' })
    await loadProducts()
  } catch (e) { alert('删除失败') }
}

// ── 上传图片 ──
const uploadImage = async (p, e) => {
  const file = e.target.files[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  try {
    await fetch(`${MAIN_API}/api/product/${p.id}/image`, { method: 'POST', body: formData })
    await loadProducts()
  } catch (err) { alert('图片上传失败') }
}

// ── 关键词多选 ──
const toggleKw = (kw) => {
  const i = form.keywords.indexOf(kw)
  i === -1 ? form.keywords.push(kw) : form.keywords.splice(i, 1)
}

const closeModal = () => {
  showAddModal.value   = false
  editingProduct.value = null
  formError.value      = ''
  Object.assign(form, { name:'', category:'', origin:'', keywords:[], description:'' })
}

onMounted(loadProducts)
</script>

<style scoped>
.manage-wrapper {
  padding: 32px 40px;
  max-width: 1000px;
  margin-left: 258px;        /* 和侧边栏宽度一致，不被遮挡 */
  min-height: 100vh;
  box-sizing: border-box;
}

@media (max-width: 768px) {
  .manage-wrapper {
    margin-left: 0;           /* 手机端侧边栏隐藏，不需要偏移 */
    padding: 20px 16px;
  }
}
.manage-header  { display: flex; justify-content: space-between; align-items: center; margin-bottom: 28px; }
.manage-title   { font-size: 24px; font-weight: 600; color: #2c3e2f; }

.btn-add {
  background: linear-gradient(135deg,#8bc34a,#6a994e); color: white;
  border: none; border-radius: 10px; padding: 10px 20px;
  font-size: 14px; font-weight: 500; cursor: pointer; transition: all .3s;
}
.btn-add:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(139,195,74,.3); }

.loading-box, .empty-box {
  text-align: center; padding: 80px 20px; color: #aaa; font-size: 16px;
}
.empty-icon { font-size: 48px; margin-bottom: 16px; }

.product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px,1fr)); gap: 20px; }

.product-card {
  background: white; border-radius: 16px; padding: 20px;
  box-shadow: 0 4px 16px rgba(0,0,0,.08); border: 2px solid transparent;
  position: relative; transition: all .3s;
}
.product-card:hover  { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,.12); }
.product-card.primary { border-color: #8bc34a; }

.primary-badge {
  position: absolute; top: 12px; right: 12px;
  background: #8bc34a; color: white; padding: 3px 10px;
  border-radius: 20px; font-size: 12px; font-weight: 600;
}

.product-img-wrap {
  width: 100%; height: 140px; border-radius: 10px; overflow: hidden;
  background: #f0f5e6; margin-bottom: 14px; position: relative;
}
.product-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.product-img-placeholder {
  width: 100%; height: 100%; display: flex; align-items: center;
  justify-content: center; font-size: 40px;
}
.img-upload-btn {
  position: absolute; bottom: 8px; right: 8px;
  background: rgba(0,0,0,.5); color: white; border-radius: 8px;
  padding: 4px 8px; font-size: 14px; cursor: pointer;
  opacity: 0; transition: opacity .2s;
}
.product-img-wrap:hover .img-upload-btn { opacity: 1; }

.product-name   { font-size: 18px; font-weight: 600; color: #2c3e2f; margin-bottom: 8px; }
.product-meta   { display: flex; gap: 8px; align-items: center; margin-bottom: 10px; flex-wrap: wrap; }
.meta-tag       { background: #e8f5e9; color: #2e7d32; padding: 2px 10px; border-radius: 20px; font-size: 12px; }
.meta-origin    { font-size: 13px; color: #888; }
.product-keywords { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
.kw-tag         { background: #f1f8e9; color: #6a994e; padding: 3px 10px; border-radius: 20px; font-size: 12px; border: 1px solid #d9e5c5; }

.product-actions { display: flex; gap: 8px; }
.btn-primary-set, .btn-edit, .btn-delete {
  flex: 1; height: 34px; border: none; border-radius: 8px;
  font-size: 13px; font-weight: 500; cursor: pointer; transition: all .2s;
}
.btn-primary-set { background: #f0f5e6; color: #6a994e; }
.btn-primary-set:hover { background: #8bc34a; color: white; }
.btn-edit   { background: #f0f5e6; color: #6a994e; }
.btn-edit:hover { background: #8bc34a; color: white; }
.btn-delete { background: #ffebee; color: #c62828; }
.btn-delete:hover { background: #c62828; color: white; }

/* 弹窗 */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.4);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-box {
  width: 480px; max-height: 80vh; background: white; border-radius: 20px;
  overflow: hidden; display: flex; flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,.3);
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 24px; border-bottom: 1px solid #f0f0f0;
}
.modal-header h3 { font-size: 20px; font-weight: 600; }
.modal-close { background: none; border: none; font-size: 24px; cursor: pointer; color: #999; }
.modal-body { padding: 20px 24px; overflow-y: auto; flex: 1; }
.modal-footer {
  padding: 16px 24px; border-top: 1px solid #f0f0f0;
  display: flex; justify-content: flex-end; gap: 12px;
}

.form-row { margin-bottom: 18px; }
.form-row label { display: block; font-size: 14px; font-weight: 500; color: #555; margin-bottom: 6px; }
.form-row input, .form-row select, .form-row textarea {
  width: 100%; padding: 10px 12px; border: 1px solid #e0e0e0; border-radius: 8px;
  font-size: 14px; box-sizing: border-box;
}
.form-row input:focus, .form-row select:focus, .form-row textarea:focus {
  outline: none; border-color: #8bc34a; box-shadow: 0 0 0 3px rgba(139,195,74,.1);
}
.form-row textarea { resize: vertical; }

.keyword-options { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 6px; }
.kw-option {
  padding: 5px 14px; border-radius: 20px; font-size: 13px; cursor: pointer;
  background: #f5f5f5; border: 1px solid #e0e0e0; color: #555; transition: all .2s;
}
.kw-option.selected { background: #8bc34a; color: white; border-color: #6a994e; }

.error-msg { background: #ffebee; color: #c62828; padding: 10px; border-radius: 6px; font-size: 13px; }

.btn-cancel { background: #e0e0e0; color: #666; border: none; border-radius: 8px; padding: 10px 24px; cursor: pointer; }
.btn-save   { background: linear-gradient(135deg,#8bc34a,#6a994e); color: white; border: none; border-radius: 8px; padding: 10px 24px; cursor: pointer; font-weight: 500; }
.btn-save:disabled { opacity: .6; cursor: not-allowed; }
</style>
