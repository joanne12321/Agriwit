import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Creation from '../views/Creation.vue'
import ProductManage from '../components/ProductManage.vue'
import Materials from '../components/Materials.vue'
import Toolbox from '../components/Toolbox.vue'
import SystemInfo from '../components/SystemInfo.vue'
import Help from '../components/Help.vue'
import About from '../components/About.vue'
const routes = [
 { path: '/', name: 'Home', component: Home },
 { path: '/creation', name: 'Creation', component: Creation },
 { path: '/products', name: 'ProductManage', component: ProductManage },
 { path: '/toolbox', name: 'Toolbox', component: Toolbox },
 { path: '/materials', name: 'Materials', component: Materials },
 { path: '/system', name: 'SystemInfo', component: SystemInfo },
 { path: '/help', name: 'Help', component: Help },
 { path: '/about', name: 'About', component: About },
]
const router = createRouter({
 history: createWebHistory(),
 routes
})
export default router