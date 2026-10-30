<template>
  <div class="auth-modal-overlay" :class="{ active: modelValue }" @click.self="closeModal">
    <div class="auth-modal">
      <div class="auth-header">
        <h2 class="auth-title">{{ isLogin ? '登录' : '企业信息登记' }}</h2>
        <button class="close-btn" @click="closeModal">×</button>
      </div>

      <div class="auth-content">
        <div v-if="loading" class="loading">处理中...</div>

        <!-- ───── 登录表单 ───── -->
        <div v-else-if="isLogin" id="loginFormContainer">
          <form @submit.prevent="handleLogin">
            <div class="form-group">
              <label>邮箱/账号</label>
              <input type="email" v-model="loginForm.account" placeholder="请输入邮箱" required />
            </div>
            <div class="form-group">
              <label>密码</label>
              <input type="password" v-model="loginForm.password" placeholder="请输入密码" required />
            </div>
            <div v-if="loginError" class="error-message">{{ loginError }}</div>
            <button type="submit" class="submit-btn" :disabled="loading">登录</button>
          </form>
        </div>

        <!-- ───── 注册表单（两步）───── -->
        <div v-else id="registerFormContainer">
          <!-- 步骤指示器 -->
          <div class="step-indicator">
            <div class="step-item" :class="{ active: currentStep === 1, done: currentStep > 1 }">
              企业信息
            </div>
            <div class="step-line" :class="{ done: currentStep > 1 }"></div>
            <div class="step-item" :class="{ active: currentStep === 2 }">
              产品信息
            </div>
          </div>

          <!-- ── 步骤1：企业/个人信息 ── -->
          <div v-show="currentStep === 1">
            <div class="form-group">
              <label>用户类型</label>
              <div class="radio-group">
                <label class="radio-label">
                  <input type="radio" value="enterprise" v-model="registerData.userType" /> 企业/合作社
                </label>
                <label class="radio-label">
                  <input type="radio" value="individual" v-model="registerData.userType" /> 个人/新农人
                </label>
              </div>
            </div>
            <div class="form-group">
              <label>{{ registerData.userType === 'enterprise' ? '企业名称' : '姓名' }}</label>
              <input type="text" v-model="registerData.companyName"
                :placeholder="registerData.userType === 'enterprise' ? '请输入企业/合作社全称' : '请输入您的姓名'"
                required />
            </div>
            <div class="form-group">
              <label>邮箱</label>
              <input type="email" v-model="registerData.account" placeholder="常用邮箱，用于登录" required />
            </div>
            <div class="form-group">
              <label>密码</label>
              <input type="password" v-model="registerData.password" placeholder="至少6位" required />
            </div>
            <div class="form-group">
              <label>确认密码</label>
              <input type="password" v-model="registerData.confirmPassword" placeholder="再次输入密码" required />
            </div>
            <div class="form-group">
              <label>所在地区</label>
              <input type="text" v-model="registerData.region" placeholder="例如：广东省-梅州市-xx镇" required />
              <div class="hint">用于产地默认值和文化故事检索</div>
            </div>
            <div class="form-group">
              <label>联系电话 (选填)</label>
              <input type="tel" v-model="registerData.contactPhone" placeholder="手机或固定电话" />
            </div>
          </div>

          <!-- ── 步骤2：产品信息 ── -->
          <div v-show="currentStep === 2">

            <!-- 已注册成功提示 -->
            <div class="success-tip" v-if="registeredUserId">
              ✅ 账号已创建（ID: {{ registeredUserId }}），请继续填写产品信息
            </div>

            <div class="form-group">
              <label>产品名称</label>
              <input type="text" v-model="registerData.productName" placeholder="例如：梅州金柚" required />
            </div>
            <div class="form-group">
              <label>产品类别</label>
              <select v-model="registerData.productCategory" required>
                <option value="">请选择</option>
                <option value="fruit">水果</option>
                <option value="vegetable">蔬菜</option>
                <option value="grain">粮油</option>
                <option value="tea">茶叶</option>
                <option value="meat_egg">畜牧/肉蛋</option>
                <option value="aquatic">水产</option>
                <option value="processed">加工品</option>
                <option value="other">其他</option>
              </select>
            </div>
            <div class="form-group">
              <label>产品产地（精确到村镇）</label>
              <input type="text" v-model="registerData.productOrigin" placeholder="例如：xx镇xx村" required />
            </div>
            <div class="form-group">
              <label>产品特点关键词（可多选）</label>
              <div class="tag-group">
                <span v-for="tag in tagOptions" :key="tag" class="tag-option"
                  :class="{ selected: registerData.productTags.includes(tag) }"
                  @click="toggleTag(tag)">
                  {{ tag }}
                </span>
              </div>
              <div class="hint">选择最能代表产品卖点的标签，AI 生成文案会优先使用</div>
            </div>
            <div class="form-group">
              <label>简短描述（选填）</label>
              <textarea v-model="registerData.productDescription"
                placeholder="一句话介绍产品特色，如：种植在海拔800米沙地，粉糯香甜"
                rows="2"></textarea>
            </div>
            <div class="form-group">
              <label>产品主图（选填，建议上传）</label>
              <div class="file-upload" @click="triggerFileUpload">
                <span>+ 点击上传图片</span>
                <input type="file" ref="fileInput" accept="image/*" @change="handleFileChange" />
              </div>
              <div v-if="imageFileName" class="file-name">{{ imageFileName }}</div>
              <div class="hint">上传后 AI 可进行抠图与风格化处理</div>
            </div>
          </div>

          <!-- 错误提示 -->
          <div v-if="registerError" class="error-message">{{ registerError }}</div>

          <!-- 操作按钮 -->
          <div class="form-actions">
            <button type="button" class="btn-prev" v-if="currentStep === 2"
              @click="prevStep" :disabled="loading">上一步</button>

            <!-- 下一步：调注册接口，成功才到第二步 -->
            <button type="button" class="btn-next" v-if="currentStep === 1"
              @click="handleNextStep" :disabled="loading">
              {{ loading ? '处理中…' : '下一步' }}
            </button>

            <!-- 完成登记：调产品接口 -->
            <button type="button" class="submit-btn" v-if="currentStep === 2"
              @click="handleRegister" :disabled="loading">
              {{ loading ? '保存中…' : '完成登记' }}
            </button>
          </div>
        </div>

        <!-- 切换登录/注册 -->
        <div class="switch-text">
          <span>{{ isLogin ? '没有账号？' : '已有账号？' }}</span>
          <button class="switch-btn" @click="toggleMode" :disabled="loading">
            {{ isLogin ? '立即登记' : '立即登录' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { login, register, registerProduct } from '../api'

const MAIN_API = import.meta.env.VITE_HOST || 'http://localhost:5000'

const props = defineProps({ modelValue: Boolean })
const emit  = defineEmits(['update:modelValue', 'login-success'])

// ── 标签选项 ──
const tagOptions = ['有机', '送礼', '童年味道', '新潮国风', '地理标志', '非遗', '产地直供', '绿色食品', '高山种植', '传统工艺']

// ── 状态 ──
const isLogin       = ref(true)
const loading       = ref(false)
const loginError    = ref('')
const registerError = ref('')
const currentStep   = ref(1)

// 注册成功后拿到的 user_id，第二步用
const registeredUserId = ref(null)

// ── 登录表单 ──
const loginForm = reactive({ account: '', password: '' })

// ── 注册表单 ──
const registerData = reactive({
  userType:           'enterprise',
  companyName:        '',
  account:            '',
  password:           '',
  confirmPassword:    '',
  region:             '',
  contactPhone:       '',
  // 第二步
  productName:        '',
  productCategory:    '',
  productOrigin:      '',
  productTags:        [],
  productDescription: '',
  productImage:       null
})

const fileInput     = ref(null)
const imageFileName = ref('')

// ── 工具 ──
const toggleMode  = () => { isLogin.value = !isLogin.value; resetForms() }
const closeModal  = () => { emit('update:modelValue', false); resetForms() }
const toggleTag   = (tag) => {
  const i = registerData.productTags.indexOf(tag)
  i === -1 ? registerData.productTags.push(tag) : registerData.productTags.splice(i, 1)
}
const triggerFileUpload = () => fileInput.value?.click()
const handleFileChange  = (e) => {
  const f = e.target.files[0]
  registerData.productImage = f || null
  imageFileName.value = f ? f.name : ''
}

const resetForms = () => {
  Object.assign(loginForm, { account: '', password: '' })
  loginError.value    = ''
  registerError.value = ''
  currentStep.value   = 1
  registeredUserId.value = null
  Object.assign(registerData, {
    userType:'enterprise', companyName:'', account:'', password:'',
    confirmPassword:'', region:'', contactPhone:'',
    productName:'', productCategory:'', productOrigin:'',
    productTags:[], productDescription:'', productImage:null
  })
  imageFileName.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

// ── 步骤1 验证 ──
const validateStep1 = () => {
  if (!registerData.companyName.trim()) {
    registerError.value = registerData.userType === 'enterprise' ? '请输入企业名称' : '请输入姓名'
    return false
  }
  if (!registerData.account.trim()) { registerError.value = '请输入邮箱'; return false }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerData.account)) {
    registerError.value = '邮箱格式不正确'; return false
  }
  if (!registerData.password) { registerError.value = '请输入密码'; return false }
  if (registerData.password.length < 6) { registerError.value = '密码至少6位'; return false }
  if (registerData.password !== registerData.confirmPassword) {
    registerError.value = '两次密码不一致'; return false
  }
  if (!registerData.region.trim()) { registerError.value = '请输入所在地区'; return false }
  return true
}

// ── 步骤2 验证 ──
const validateStep2 = () => {
  if (!registerData.productName.trim())   { registerError.value = '请输入产品名称'; return false }
  if (!registerData.productCategory)      { registerError.value = '请选择产品类别'; return false }
  if (!registerData.productOrigin.trim()) { registerError.value = '请输入产品产地'; return false }
  return true
}

// ══════════════════════════════════════════════
//  下一步按钮：调注册接口，成功后跳第二步
//  ← 这里是关键修改：把注册 API 调用从 handleRegister 移到这里
// ══════════════════════════════════════════════
const handleNextStep = async () => {
  registerError.value = ''
  if (!validateStep1()) return

  loading.value = true
  try {
    // 第一步：创建账号
    // register(username, account, password, userType, companyName, region, phone)
    const res = await register(
      registerData.companyName,       // username / 姓名
      registerData.account,           // 邮箱
      registerData.password,
      registerData.userType,          // "enterprise" | "individual"
      registerData.companyName,       // company_name（个人时与username相同）
      registerData.region,
      registerData.contactPhone
    )

    if (res && res.code === 0) {
      // 保存 user_id 供第二步使用
      registeredUserId.value = res.data.user_id || res.data.user?.id
      currentStep.value = 2
    } else {
      registerError.value = res.message || '注册失败，请重试'
    }
  } catch (err) {
    // err.message 现在能显示 FastAPI 的真实错误（如"该邮箱已被注册"）
    registerError.value = err.message || '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

const prevStep = () => { currentStep.value = 1; registerError.value = '' }

// ══════════════════════════════════════════════
//  完成登记按钮：调产品接口，把第二步数据存库
//  ← 这样 AI 生成时就能读到这些数据了
// ══════════════════════════════════════════════
const handleRegister = async () => {
  registerError.value = ''
  if (!validateStep2()) return

  if (!registeredUserId.value) {
    registerError.value = '账号信息丢失，请返回上一步重试'
    return
  }

  loading.value = true
  try {
    // 第二步：保存产品信息
    const res = await registerProduct(
      registeredUserId.value,
      registerData.productName,
      registerData.productCategory,
      registerData.productOrigin,
      registerData.productTags,
      registerData.productDescription,
      true
    )

    if (res && res.code === 0) {
      const productId = res.data?.product_id

      // ★ 如果用户上传了产品图，上传到服务器
      if (registerData.productImage && productId) {
        try {
          const formData = new FormData()
          formData.append('file', registerData.productImage)
          await fetch(`${MAIN_API}/api/product/${productId}/image`, {
            method: 'POST',
            body: formData   // 不设 Content-Type，浏览器自动加 boundary
          })
          console.log('✅ 产品图片已上传')
        } catch (imgErr) {
          console.warn('图片上传失败（不影响注册）:', imgErr)
        }
      }

      alert(`登记成功！欢迎 ${registerData.companyName}，产品「${registerData.productName}」已保存。`)
      emit('login-success', { id: registeredUserId.value, username: registerData.companyName, account: registerData.account })
      closeModal()
    } else {
      registerError.value = res.message || '产品信息保存失败'
    }
  } catch (err) {
    registerError.value = err.message || '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

// ── 登录 ──
const handleLogin = async () => {
  if (!loginForm.account || !loginForm.password) {
    loginError.value = '请填写账号和密码'; return
  }
  loading.value = true
  loginError.value = ''
  try {
    const res = await login(loginForm.account, loginForm.password)
    if (res && res.code === 0) {
      emit('login-success', res.data.user)
      closeModal()
    } else {
      loginError.value = res.message || '登录失败'
    }
  } catch (err) {
    loginError.value = err.message || '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

watch(() => props.modelValue, (val) => { if (!val) { isLogin.value = true; resetForms() } })
</script>

<style scoped>
.auth-modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-color: rgba(0,0,0,0.5); z-index: 2000;
  display: none; align-items: center; justify-content: center;
  backdrop-filter: blur(3px);
}
.auth-modal-overlay.active { display: flex; }

.auth-modal {
  width: 440px; max-width: 90%; background: white;
  border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  overflow: hidden; transform: scale(0.9); opacity: 0; transition: all 0.3s;
}
.active .auth-modal { transform: scale(1); opacity: 1; }

.auth-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 24px; border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f8f9fa 0%, #fff 100%);
}
.auth-title { font-size: 24px; font-weight: 600; color: #333; margin: 0; }
.close-btn {
  width: 32px; height: 32px; border-radius: 50%; border: none;
  background: transparent; color: #999; font-size: 28px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all 0.2s;
}
.close-btn:hover { background: #f0f0f0; color: #666; }

.auth-content { padding: 24px; max-height: 70vh; overflow-y: auto; }

.loading { text-align: center; padding: 40px; color: #666; }

/* ── 步骤指示器 ── */
.step-indicator {
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 24px; gap: 0;
}
.step-item {
  display: flex; flex-direction: column; align-items: center;
  font-size: 12px; color: #aaa; gap: 4px; position: relative;
}
.step-item::before {
  content: ''; width: 24px; height: 24px; border-radius: 50%;
  background: #e0e0e0; display: block; transition: all 0.3s;
}
.step-item.active::before { background: #7dba28; }
.step-item.done::before   { background: #7dba28; content: '✓'; color: white;
  font-size: 14px; font-weight: bold; line-height: 24px; text-align: center; }
.step-item.active  { color: #7dba28; font-weight: 500; }
.step-line {
  flex: 1; height: 2px; background: #e0e0e0; margin: 0 8px;
  margin-bottom: 16px; transition: background 0.3s; min-width: 40px;
}
.step-line.done { background: #7dba28; }

/* ── 成功提示 ── */
.success-tip {
  background: #f1f8e9; color: #2e7d32; border: 1px solid #c5e1a5;
  border-radius: 8px; padding: 10px 14px; font-size: 13px; margin-bottom: 16px;
}

/* ── 表单 ── */
.form-group { margin-bottom: 18px; }
.form-group label {
  display: block; font-size: 14px; font-weight: 500; color: #555; margin-bottom: 6px;
}
.form-group input,
.form-group select,
.form-group textarea {
  width: 100%; height: 44px; padding: 0 12px; border: 1px solid #e0e0e0;
  border-radius: 8px; font-size: 15px; box-sizing: border-box; background: white; transition: all 0.2s;
}
.form-group textarea { height: 80px; padding: 10px 12px; resize: vertical; }
.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none; border-color: #7dba28; box-shadow: 0 0 0 3px rgba(125,186,40,0.1);
}
.form-group input::placeholder,
.form-group textarea::placeholder { color: #aaa; font-size: 14px; }

.radio-group { display: flex; gap: 16px; margin-top: 6px; }
.radio-label  { display: flex; align-items: center; font-size: 15px; color: #333; cursor: pointer; }
.radio-label input { width: auto; height: auto; margin-right: 6px; accent-color: #7dba28; }

.tag-group { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.tag-option {
  background: #f5f5f5; border: 1px solid #e0e0e0; border-radius: 30px;
  padding: 5px 14px; font-size: 13px; color: #555; cursor: pointer;
  transition: all 0.2s; user-select: none;
}
.tag-option.selected { background: #7dba28; border-color: #51830a; color: white; }

.file-upload {
  border: 1px dashed #7dba28; border-radius: 8px; padding: 12px;
  text-align: center; background: #f9f9f9; cursor: pointer; position: relative;
}
.file-upload input {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;
}
.file-upload span { color: #7dba28; font-weight: 500; }
.file-name { margin-top: 6px; font-size: 12px; color: #666; }

.hint { font-size: 12px; color: #999; margin-top: 4px; }

/* ── 按钮 ── */
.form-actions { display: flex; gap: 12px; margin-top: 20px; }
.form-actions button {
  flex: 1; height: 46px; border: none; border-radius: 8px;
  font-size: 15px; font-weight: 500; cursor: pointer; transition: all 0.3s;
}
.btn-prev { background: #f0f0f0; color: #666; }
.btn-prev:hover:not(:disabled) { background: #e0e0e0; }
.btn-next, .submit-btn {
  background: linear-gradient(135deg, #7dba28 0%, #51830a 100%);
  color: white; box-shadow: 0 4px 12px rgba(125,186,40,0.3);
}
.btn-next:hover:not(:disabled),
.submit-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(125,186,40,0.4); }
.btn-next:disabled,
.btn-prev:disabled,
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.error-message {
  background: #ffebee; color: #c62828; padding: 10px 12px;
  border-radius: 6px; font-size: 14px; margin-bottom: 16px; border-left: 3px solid #c62828;
}

/* ── 切换 ── */
.switch-text { margin-top: 20px; text-align: center; font-size: 14px; color: #666; }
.switch-btn {
  background: none; border: none; color: #7dba28;
  font-weight: 500; cursor: pointer; font-size: 14px;
}
.switch-btn:hover:not(:disabled) { color: #51830a; text-decoration: underline; }

/* ── 登录按钮 ── */
#loginFormContainer .submit-btn {
  background: linear-gradient(135deg, #7dba28 0%, #51830a 100%);
  color: white; border: none; border-radius: 8px; height: 46px;
  font-size: 15px; font-weight: 500; cursor: pointer;
  width: 100%; display: block; margin-top: 8px;
  box-shadow: 0 4px 12px rgba(125,186,40,0.3); transition: all 0.3s;
}
#loginFormContainer .submit-btn:hover:not(:disabled) { transform: translateY(-2px); }
#loginFormContainer .submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
