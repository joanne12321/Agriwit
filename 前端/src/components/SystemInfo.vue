<template>
  <div class="page-wrapper">
    <div class="page-header">
      <h2>⚙️ 系统信息</h2>
      <p class="sub">云稼集·AgriWit 技术架构说明</p>
    </div>

    <!-- 版本信息 -->
    <div class="info-card">
      <div class="card-title">📦 版本信息</div>
      <div class="info-grid">
        <div class="info-row"><span class="label">系统名称</span><span class="value">云稼集·AgriWit</span></div>
        <div class="info-row"><span class="label">当前版本</span><span class="value"><span class="badge green">v1.0.0</span></span></div>
        <div class="info-row"><span class="label">最后更新</span><span class="value">2026年4月</span></div>
        <div class="info-row"><span class="label">运行状态</span><span class="value"><span class="badge green">● 正常运行</span></span></div>
      </div>
    </div>

    <!-- 技术栈 -->
    <div class="info-card">
      <div class="card-title">🛠️ 技术栈</div>
      <div class="tech-sections">
        <div class="tech-group">
          <div class="tech-group-title">前端</div>
          <div class="tech-tags">
            <span class="tech-tag blue">Vue 3</span>
            <span class="tech-tag blue">Vite</span>
            <span class="tech-tag blue">Vue Router 4</span>
            <span class="tech-tag blue">原生 CSS</span>
            <span class="tech-tag blue">Fetch API</span>
          </div>
        </div>
        <div class="tech-group">
          <div class="tech-group-title">后端</div>
          <div class="tech-tags">
            <span class="tech-tag green">FastAPI</span>
            <span class="tech-tag green">Flask</span>
            <span class="tech-tag green">SQLAlchemy</span>
            <span class="tech-tag green">SQLite</span>
            <span class="tech-tag green">bcrypt</span>
            <span class="tech-tag green">JWT</span>
          </div>
        </div>
        <div class="tech-group">
          <div class="tech-group-title">AI / 数据库</div>
          <div class="tech-tags">
            <span class="tech-tag orange">DeepSeek API</span>
            <span class="tech-tag orange">Neo4j</span>
            <span class="tech-tag orange">Chroma 向量数据库</span>
            <span class="tech-tag orange">rembg / U2Net</span>
            <span class="tech-tag orange">Pillow</span>
          </div>
        </div>
        <div class="tech-group">
          <div class="tech-group-title">架构特色</div>
          <div class="tech-tags">
            <span class="tech-tag purple">Orchestrator-Worker 多Agent</span>
            <span class="tech-tag purple">并行执行</span>
            <span class="tech-tag purple">QA打回机制</span>
            <span class="tech-tag purple">异步任务队列</span>
            <span class="tech-tag purple">语义向量检索</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 服务状态 -->
    <div class="info-card">
      <div class="card-title">🔌 服务端口</div>
      <div class="port-list">
        <div class="port-row">
          <span class="port-num">:5000</span>
          <span class="port-name">main.py</span>
          <span class="port-desc">用户/产品/数据库 (FastAPI)</span>
        </div>
        <div class="port-row">
          <span class="port-num">:5001</span>
          <span class="port-name">ai_service.py</span>
          <span class="port-desc">多Agent文案生成 (Flask)</span>
        </div>
        <div class="port-row">
          <span class="port-num">:5002</span>
          <span class="port-name">tag_service.py</span>
          <span class="port-desc">Neo4j标签库 (Flask)</span>
        </div>
        <div class="port-row">
          <span class="port-num">:5003</span>
          <span class="port-name">image_service.py</span>
          <span class="port-desc">图片处理/抠图 (Flask)</span>
        </div>
        <div class="port-row">
          <span class="port-num">:3000</span>
          <span class="port-name">前端</span>
          <span class="port-desc">Vue3 + Vite 开发服务器</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup></script>

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

.info-grid { display: flex; flex-direction: column; gap: 12px; }
.info-row { display: flex; align-items: center; gap: 16px; padding: 10px 14px; background: #f9fafb; border-radius: 8px; }
.label { font-size: 13px; color: #888; width: 80px; flex-shrink: 0; }
.value { font-size: 14px; color: #333; font-weight: 500; }
.badge { padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.badge.green { background: #e8f5e9; color: #2e7d32; }

.tech-sections { display: flex; flex-direction: column; gap: 16px; }
.tech-group-title { font-size: 13px; color: #888; margin-bottom: 8px; font-weight: 500; }
.tech-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.tech-tag {
  padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500;
}
.tech-tag.blue   { background: #e3f2fd; color: #1565c0; }
.tech-tag.green  { background: #e8f5e9; color: #2e7d32; }
.tech-tag.orange { background: #fff3e0; color: #e65100; }
.tech-tag.purple { background: #f3e5f5; color: #6a1b9a; }

.port-list { display: flex; flex-direction: column; gap: 8px; }
.port-row {
  display: flex; align-items: center; gap: 16px;
  padding: 10px 14px; background: #f9fafb; border-radius: 8px;
  border-left: 3px solid #8bc34a;
}
.port-num  { font-size: 13px; font-weight: 700; color: #8bc34a; width: 50px; flex-shrink: 0; font-family: monospace; }
.port-name { font-size: 13px; font-weight: 600; color: #333; width: 140px; flex-shrink: 0; }
.port-desc { font-size: 12px; color: #888; }

@media (max-width: 768px) { .page-wrapper { margin-left: 0; padding: 20px 16px; } }
</style>
