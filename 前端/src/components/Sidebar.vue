<template>
  <aside class="view" role="navigation">
    <header class="view-header">
      <div class="u-globe">稼</div>
      <h1 class="text-wrapper-9">云稼集·AgriWit</h1>
    </header>

    <nav class="div">
      <ul class="nav-list">
        <li><router-link to="/"         exact-active-class="view-5"><i data-feather="home"       class="img"></i><span class="text-wrapper">首页</span></router-link></li>
        <li><router-link to="/creation" exact-active-class="view-5"><i data-feather="edit-2"     class="img"></i><span class="text-wrapper">创作中心</span></router-link></li>
        <li><router-link to="/products" exact-active-class="view-5"><i data-feather="credit-card" class="img"></i><span class="text-wrapper">产品管理</span></router-link></li>
        <li><router-link to="/toolbox"  exact-active-class="view-5"><i data-feather="command"    class="img"></i><span class="text-wrapper">工具箱</span></router-link></li>
        <li><router-link to="/materials" exact-active-class="view-5"><i data-feather="columns" class="img"></i><span class="text-wrapper">素材库</span></router-link></li>
      </ul>

      <nav class="frame">
        <router-link to="/system"><span class="text-wrapper-5">系统信息</span></router-link>
        <router-link to="/help">  <span class="text-wrapper-6">帮助支持</span></router-link>
        <router-link to="/about"> <span class="text-wrapper-6">关注我们</span></router-link>
      </nav>
    </nav>

    <footer class="view-7">
      <template v-if="!userInfo">
        <div class="user" @click="openAuthModal"><i data-feather="user" class="icon"></i></div>
        <div class="text-wrapper-7" @click="openAuthModal" style="cursor:pointer">点击登录</div>
        <div class="text-wrapper-8">未登录</div>
      </template>
      <template v-else>
        <div class="user logged-in"><span class="user-initial">{{ userInitial }}</span></div>
        <div class="text-wrapper-7">{{ userDisplayName }}</div>
        <div class="text-wrapper-8">{{ userEmail }}</div>
        <button class="logout-btn" @click="handleLogout">
          <i data-feather="log-out"></i><span>退出登录</span>
        </button>
      </template>
    </footer>
  </aside>
</template>

<script setup>
import { computed, inject, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { clearAuth, getUser } from '../api'

const router        = useRouter()
const openAuthModal = inject('openAuthModal')
const user          = inject('user')

const userInfo        = computed(() => user?.value || getUser())
const userDisplayName = computed(() => { const u = userInfo.value; return u?.username || u?.account || '用户' })
const userInitial     = computed(() => userDisplayName.value.charAt(0).toUpperCase())
const userEmail       = computed(() => { const u = userInfo.value; return u?.account || u?.email || '已登录' })

const handleLogout = () => {
  if (!confirm('确认退出登录？')) return
  clearAuth()
  if (user) user.value = null
  router.push('/')
  nextTick(() => { if (window.feather) window.feather.replace() })
}

onMounted(() => { if (window.feather) window.feather.replace() })
</script>

<style scoped>
.view { position:fixed; top:0; left:0; width:258px; height:100vh; background:#fff; box-shadow:0 4px 20px rgba(0,0,0,.08); z-index:100; display:flex; flex-direction:column; overflow:hidden; }
.view-header { height:154px; display:flex; align-items:center; padding-left:32px; border-bottom:1px solid #f0f0f0; }
.u-globe { width:42px; height:42px; background:#7dba28; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-weight:bold; font-size:20px; transition:transform .6s cubic-bezier(.34,1.56,.64,1); }
.u-globe:hover { transform:rotate(20deg) scale(1.1); }
.text-wrapper-9 { font-weight:800; font-size:28px; margin-left:14px; background:linear-gradient(135deg,#51830a,#7dba28); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.div { width:100%; padding:20px 0; }
.nav-list { list-style:none; padding:0; margin:0; }
.nav-list li { width:100%; }
.nav-list a { display:flex; align-items:center; width:100%; height:72px; padding:0 32px; text-decoration:none; color:inherit; transition:all .3s; position:relative; }
.nav-list a::before { content:''; position:absolute; left:0; top:0; height:100%; width:4px; background:#7dba28; transform:scaleY(0); transition:transform .3s; }
.nav-list a:hover { background:rgba(125,186,40,.15); }
.nav-list a:hover::before { transform:scaleY(.3); }
.view-5 { background:rgba(125,186,40,.2) !important; }
.view-5::before { transform:scaleY(1) !important; }
.img { width:26px; height:26px; margin-right:16px; transition:transform .3s,color .3s; stroke:currentColor; stroke-width:2; fill:none; }
.nav-list a:hover .img { transform:translateX(4px); color:#7dba28; }
.text-wrapper { font-weight:500; font-size:18px; color:#555; transition:color .3s; }
.nav-list a:hover .text-wrapper,.view-5 .text-wrapper { color:#427107; font-weight:600; }
.frame { padding:24px 32px; display:flex; flex-direction:column; gap:18px; border-top:1px solid #f0f0f0; margin-top:20px; }
.frame a { text-decoration:none; display:flex; align-items:center; height:32px; transition:all .3s; }
.text-wrapper-5,.text-wrapper-6 { font-size:16px; color:#666; transition:all .3s; position:relative; padding-left:8px; }
.text-wrapper-5::before,.text-wrapper-6::before { content:''; position:absolute; left:0; top:50%; transform:translateY(-50%); width:4px; height:4px; background:#ccc; border-radius:50%; transition:background .3s; }
.frame a:hover .text-wrapper-5,.frame a:hover .text-wrapper-6 { color:#427107; transform:translateX(6px); }
.frame a:hover .text-wrapper-5::before,.frame a:hover .text-wrapper-6::before { background:#7dba28; }
.view-7 { margin-top:auto; padding:20px 0 16px; display:flex; flex-direction:column; align-items:center; border-top:1px solid #f0f0f0; }
.user { width:64px; height:64px; border-radius:50%; background:linear-gradient(135deg,#7dba28,#51830a); display:flex; align-items:center; justify-content:center; margin-bottom:10px; cursor:pointer; box-shadow:0 6px 16px rgba(125,186,40,.25); transition:all .4s cubic-bezier(.34,1.56,.64,1); }
.user:hover { transform:scale(1.08); }
.user.logged-in { cursor:default; }
.user-initial { color:white; font-size:26px; font-weight:bold; }
.icon { width:30px; height:30px; color:white; }
.text-wrapper-7 { font-weight:600; color:#333; font-size:18px; text-align:center; margin-bottom:4px; max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.text-wrapper-8 { font-size:13px; color:#888; text-align:center; max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.logout-btn { margin-top:12px; display:flex; align-items:center; gap:6px; background:none; border:1px solid #e0e0e0; border-radius:20px; padding:6px 16px; color:#999; font-size:13px; cursor:pointer; transition:all .25s; }
.logout-btn:hover { border-color:#f44336; color:#f44336; background:#fff5f5; }
.logout-btn i { width:14px; height:14px; }
@media (max-width: 768px) { .view { display:none; } }
</style>
