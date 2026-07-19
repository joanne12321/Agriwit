<template>
  <div class="page-wrapper">
    <div class="page-header">
      <h2>💚 关注我们</h2>
      <p class="sub">团队介绍 · 联系方式 · 项目背景</p>
    </div>

    <!-- 项目介绍 -->
    <div class="info-card hero-card">
      <div class="hero-logo">稼</div>
      <div class="hero-text">
        <div class="hero-name">云稼集·AgriWit</div>
        <div class="hero-slogan">让每一位农户都有专属的声音</div>
        <div class="hero-desc">
          云稼集·AgriWit是一款面向农产品经营者的 AI 营销文案与海报生成平台。
          基于多 Agent 工作流和知识图谱技术，帮助农户快速生成接地气的宣传内容，
          助力乡村振兴和农产品上行。
        </div>
      </div>
    </div>

    <!-- 团队介绍 -->
    <div class="info-card">
      <div class="card-title">👥 团队介绍</div>
      <div class="team-grid">
        <div class="team-member" v-for="m in members" :key="m.name">
          <div class="member-avatar">{{ m.name.charAt(0) }}</div>
          <div class="member-name">{{ m.name }}</div>
          <div class="member-role">{{ m.role }}</div>
        </div>
      </div>
      <div class="school-info">
        <span>📍 指导老师：郝鹃老师、余扬老师</span>
        <span>🏫 广东外语外贸大学大学 · 信息科学与技术学院</span>
        <span>📅 2024＆2025届</span>
      </div>
    </div>

    <!-- 联系方式 -->
    <div class="info-card">
      <div class="card-title">📬 联系方式</div>
      <div class="contact-list">
        <div class="contact-item">
          <span class="contact-icon">📧</span>
          <span class="contact-label">邮箱</span>
          <span class="contact-value">2939968704@qq.com</span>
        </div>
        <div class="contact-item">
          <span class="contact-icon">💬</span>
          <span class="contact-label">微信</span>
          <span class="contact-value">pvo_Blade</span>
        </div>
        <div class="contact-item">
          <span class="contact-icon">🐙</span>
          <span class="contact-label">Gitee</span>
          <span class="contact-value">完善中</span>
        </div>
      </div>
    </div>

    <!-- 二维码区域 -->
    <div class="info-card">
      <div class="card-title">📱 扫码访问</div>
      <div class="qr-area">
        <div class="qr-box">
          
          <div class="qr-placeholder">
            <div class="qr-mock">
              <div v-for="r in 8" :key="r" class="qr-row">
                <div v-for="c in 8" :key="c" class="qr-cell"
                  :class="{ filled: (r + c) % 3 !== 0 }"></div>
              </div>
            </div>
          </div>
          <div class="qr-label">项目演示地址</div>
          <div class="qr-sub">同一 WiFi 下扫码访问</div>
        </div>
        <div class="qr-tips">
          <div class="tip-title">📌 手机访问方法</div>
          <div class="tip-step">1. 电脑和手机连同一个 WiFi</div>
          <div class="tip-step">2. 前端启动命令加 <code>--host</code></div>
          <div class="tip-code">npm run dev -- --host</div>
          <div class="tip-step">3. 手机浏览器访问终端显示的 Network 地址</div>
          <div class="tip-code">http://192.168.x.x:3000</div>
        </div>
      </div>
    </div>

    <!-- 项目背景 -->
    <div class="info-card">
      <div class="card-title">🌾 项目背景</div>
      <div class="bg-text">
        随着农村电商的快速发展，越来越多的农户开始在小红书、抖音、淘宝等平台销售农产品。
        然而，大多数农户缺乏专业的文案写作能力和设计工具，创作宣传内容有一定难度。
        <br><br>
        云稼集·AgriWit针对这一痛点，结合地域文化特色（客家文化、广府文化、潮汕文化等）和
        平台运营规律，通过 AI 多 Agent 协同工作流，为农户提供一站式的文案创作和海报生成服务。
        <br><br>
        项目融合了大语言模型、知识图谱、计算机视觉等多项技术，致力于让每一位农户都能
        用上智能营销工具，让优质的农产品被更多人看见。
      </div>
    </div>
  </div>
</template>

<script setup>
// 修改成你们团队的真实信息
const members = [
  { name: '陈娇', role: '全栈开发 / 项目负责人' },
  { name: '雄芊羽', role: '前端开发 / UI设计' },
  { name: '吴敏菲', role: '后端开发 / AI算法' },
  { name: '易欣雨', role: '数据库 / 知识图谱' },
]
</script>

<style scoped>
.page-wrapper { padding: 32px 40px; max-width: 800px; margin-left: 258px; min-height: 100vh; }
.page-header { margin-bottom: 28px; }
.page-header h2 { font-size: 24px; font-weight: 600; color: #2c3e2f; margin-bottom: 6px; }
.sub { font-size: 14px; color: #888; }

.info-card {
  background: white; border-radius: 16px; padding: 24px;
  box-shadow: 0 4px 16px rgba(0,0,0,.07); margin-bottom: 20px; border: 1px solid #e8e8e8;
}
.card-title { font-size: 16px; font-weight: 600; color: #2c3e2f; margin-bottom: 18px; }

/* Hero */
.hero-card { display: flex; gap: 20px; align-items: flex-start; background: linear-gradient(135deg,#f0f8e6,#e8f5e9); border-color: #c5e1a5; }
.hero-logo {
  width: 60px; height: 60px; border-radius: 16px; flex-shrink: 0;
  background: linear-gradient(135deg,#7dba28,#51830a);
  color: white; font-size: 28px; font-weight: bold;
  display: flex; align-items: center; justify-content: center;
}
.hero-name   { font-size: 20px; font-weight: 700; color: #2c3e2f; margin-bottom: 4px; }
.hero-slogan { font-size: 14px; color: #6a994e; font-style: italic; margin-bottom: 10px; }
.hero-desc   { font-size: 13px; color: #555; line-height: 1.7; }

/* 团队 */
.team-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }
.team-member { text-align: center; }
.member-avatar {
  width: 52px; height: 52px; border-radius: 50%; margin: 0 auto 8px;
  background: linear-gradient(135deg,#8bc34a,#6a994e);
  color: white; font-size: 20px; font-weight: bold;
  display: flex; align-items: center; justify-content: center;
}
.member-name { font-size: 14px; font-weight: 600; color: #333; }
.member-role { font-size: 12px; color: #888; margin-top: 2px; }
.school-info { display: flex; gap: 20px; padding: 12px 14px; background: #f9fafb; border-radius: 8px; font-size: 13px; color: #666; flex-wrap: wrap; }

/* 联系 */
.contact-list { display: flex; flex-direction: column; gap: 10px; }
.contact-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; background: #f9fafb; border-radius: 8px; }
.contact-icon  { font-size: 18px; }
.contact-label { font-size: 13px; color: #888; width: 40px; }
.contact-value { font-size: 14px; color: #333; font-weight: 500; }

/* 二维码 */
.qr-area { display: flex; gap: 30px; align-items: flex-start; flex-wrap: wrap; }
.qr-box  { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.qr-placeholder {
  width: 120px; height: 120px; border: 2px solid #e0e0e0; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; background: #fafafa;
}
.qr-mock { display: grid; grid-template-rows: repeat(8,1fr); gap: 2px; padding: 8px; }
.qr-row  { display: flex; gap: 2px; }
.qr-cell { width: 10px; height: 10px; border-radius: 1px; background: #e0e0e0; }
.qr-cell.filled { background: #2c3e2f; }
.qr-label { font-size: 13px; font-weight: 600; color: #333; }
.qr-sub   { font-size: 11px; color: #aaa; }
.qr-tips  { flex: 1; min-width: 200px; }
.tip-title { font-size: 14px; font-weight: 600; color: #333; margin-bottom: 10px; }
.tip-step  { font-size: 13px; color: #555; margin-bottom: 6px; }
.tip-code  {
  font-family: monospace; background: #1a1a2e; color: #7dba28;
  padding: 6px 12px; border-radius: 6px; font-size: 12px; margin-bottom: 8px; display: inline-block;
}

/* 背景 */
.bg-text { font-size: 14px; color: #555; line-height: 1.9; }

@media (max-width: 768px) {
  .page-wrapper { margin-left: 0; padding: 20px 16px; }
  .team-grid    { grid-template-columns: repeat(2, 1fr); }
  .hero-card    { flex-direction: column; }
}
</style>
