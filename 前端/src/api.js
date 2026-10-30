// src/api.js  ── 修复版
const HOST = import.meta.env.VITE_HOST || 'http://localhost:5000'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'
const AI_API       = import.meta.env.VITE_AI_API || 'http://localhost:5001'
const TAG_API      = import.meta.env.VITE_TAG_API || 'http://localhost:5002'
const IMG_API      = import.meta.env.VITE_IMG_API || 'http://localhost:5003'

const TOKEN_KEY = 'auth_token'
const USER_KEY  = 'user_info'

export const setToken    = (t) => localStorage.setItem(TOKEN_KEY, t)
export const getToken    = ()  => localStorage.getItem(TOKEN_KEY)
export const removeToken = ()  => localStorage.removeItem(TOKEN_KEY)
export const setUser     = (u) => localStorage.setItem(USER_KEY, JSON.stringify(u))
export const getUser     = ()  => { const s = localStorage.getItem(USER_KEY); return s ? JSON.parse(s) : null }
export const removeUser  = ()  => localStorage.removeItem(USER_KEY)
export const clearAuth   = ()  => { removeToken(); removeUser() }
export const isLoggedIn  = ()  => !!(getToken() && getUser())

// ── 通用请求（修复：FastAPI 用 detail）──
async function request(endpoint, options = {}) {
    const url     = `${API_BASE_URL}${endpoint}`
    const token   = getToken()
    const headers = { 'Content-Type': 'application/json', ...options.headers }
    if (token) headers['Authorization'] = `Bearer ${token}`

    let res
    try {
        res = await fetch(url, { ...options, headers })
    } catch (networkErr) {
        // 真正的网络错误（后端没启动、断网）才提示连接失败
        throw new Error('无法连接到后端，请确认 main.py 已启动（python main.py）')
    }

    // 能走到这里说明后端有响应，读取具体错误信息
    const data = await res.json().catch(() => null)
    if (!res.ok) {
        // FastAPI 错误格式是 { detail: "..." }
        const msg = (data && (data.detail || data.message)) || `请求失败 (${res.status})`
        throw new Error(msg)
    }
    return data
}

// 注册第一步：创建账号
export async function register(username, account, password, userType = 'individual', companyName = '', region = '', phone = '') {
    const data = await request('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, account, password, user_type: userType, company_name: companyName, region, phone })
    })
    if (data && data.access_token) {
        const user = { id: data.user_id, username: data.username, account }
        setToken(data.access_token)
        setUser(user)
        return { code: 0, message: '注册成功', data: { token: data.access_token, user, user_id: data.user_id } }
    }
    throw new Error((data && data.detail) || '注册失败')
}

// 注册第二步：保存产品信息（AI 生成时会读这里）
// 注意：直接用 fetch 不走 request()，避免自动带 Authorization 头导致 CORS 问题
export async function registerProduct(userId, productName, category, origin, keywords = [], description = '', isPrimary = true) {
    let res
    try {
        res = await fetch(`${API_BASE_URL}/product/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, name: productName, category, origin, keywords, description, is_primary: isPrimary })
        })
    } catch (e) {
        throw new Error('无法连接到后端，请确认 main.py 已启动')
    }
    const data = await res.json().catch(() => null)
    if (!res.ok) throw new Error((data && (data.detail || data.message)) || '产品信息保存失败')
    return { code: 0, message: '产品信息已保存', data }
}

// 登录
export async function login(account, password) {
    const data = await request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ account, password })
    })
    if (data && data.access_token) {
        const user = { id: data.user_id, username: data.username, account }
        setToken(data.access_token)
        setUser(user)
        return { code: 0, message: '登录成功', data: { token: data.access_token, user, registration_step: data.registration_step } }
    }
    throw new Error((data && data.detail) || '登录失败')
}

// AI 文案生成
export async function generateContent(params) {
    const user = getUser()
    const res  = await fetch(`${AI_API}/api/ai/generate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...params, user_id: params.user_id || user?.id })
    })
    if (!res.ok) throw new Error('AI 服务请求失败，请确认 ai_service.py 已启动')
    return res.json()
}

export async function refineContent(params) {
    const res = await fetch(`${AI_API}/api/ai/refine`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(params)
    })
    return res.json()
}

// 图片服务
export async function getTemplates() {
    const res = await fetch(`${IMG_API}/api/templates`)
    return res.json()
}
export async function fullImagePipeline(params) {
    const res = await fetch(`${IMG_API}/api/image/full-pipeline`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(params)
    })
    return res.json()
}

// 标签服务
export async function getMyTags(platform, region, category) {
    const res = await fetch(`${TAG_API}/api/tags/all?platform=${encodeURIComponent(platform)}&region=${encodeURIComponent(region)}&product_category=${encodeURIComponent(category)}`)
    return res.json()
}
export async function getMyForbiddenWords() {
    return (await fetch(`${TAG_API}/api/forbidden-words`)).json()
}
export async function getMyRegionStyle(region) {
    return (await fetch(`${TAG_API}/api/region/${encodeURIComponent(region)}`)).json()
}


// ========== 历史记录（走 ai_service.py:5001）==========
export async function getHistory(limit = 20) {
  const user = getUser()
  const userId = user?.id || ''
  const url = `${AI_API}/api/history?limit=${limit}&user_id=${userId}`
  try {
    const res = await fetch(url)
    return await res.json()
  } catch (e) {
    console.error('获取历史失败:', e)
    return { history: [], total: 0 }
  }
}
