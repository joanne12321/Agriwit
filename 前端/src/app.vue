<template>
  <div class="screen">
    <Sidebar v-if="!isMobileRoute" />
    <router-view />
    <AuthModal v-model="authModalOpen" @login-success="handleLoginSuccess" />
  </div>
</template>

<script setup>
import { computed, ref, provide, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar   from './components/Sidebar.vue'
import AuthModal from './components/AuthModal.vue'
import { getUser, isLoggedIn, clearAuth } from './api'

const authModalOpen = ref(false)
const user          = ref(null)
const route         = useRoute()
const isMobileRoute = computed(() => route.path === '/mobile')

onMounted(() => {
  if (isLoggedIn()) {
    user.value = getUser()
  }
})

const openAuthModal = () => { authModalOpen.value = true }

// 退出登录（Sidebar 调用）
const handleLogout = () => {
  clearAuth()
  user.value = null
}

provide('openAuthModal', openAuthModal)
provide('handleLogout',  handleLogout)
provide('user', user)

const handleLoginSuccess = (userData) => {
  user.value = userData
}
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; font-family: "Inter", -apple-system, sans-serif; background: #f5f5f7; }
.screen { display: flex; min-height: 100vh; }
</style>
