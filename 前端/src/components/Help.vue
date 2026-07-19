<template>
  <div class="page-wrapper">
    <div class="page-header">
      <h2>🙋 帮助支持</h2>
      <p class="sub">使用说明 · 常见问题解答</p>
    </div>

    <!-- 快速上手 -->
    <div class="info-card">
      <div class="card-title">🚀 快速上手（5步开始使用）</div>
      <div class="steps">
        <div class="step" v-for="(step, i) in steps" :key="i">
          <div class="step-num">{{ i + 1 }}</div>
          <div class="step-content">
            <div class="step-title">{{ step.title }}</div>
            <div class="step-desc">{{ step.desc }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- FAQ -->
    <div class="info-card">
      <div class="card-title">❓ 常见问题</div>
      <div class="faq-list">
        <div v-for="(faq, i) in faqs" :key="i" class="faq-item">
          <div class="faq-q" @click="faq.open = !faq.open">
            <span>{{ faq.q }}</span>
            <span class="faq-arrow" :class="{ open: faq.open }">▼</span>
          </div>
          <div class="faq-a" v-if="faq.open">{{ faq.a }}</div>
        </div>
      </div>
    </div>

    <!-- 功能说明 -->
    <div class="info-card">
      <div class="card-title">📋 功能说明</div>
      <div class="feature-list">
        <div class="feature-item" v-for="f in features" :key="f.name">
          <span class="feature-icon">{{ f.icon }}</span>
          <div>
            <div class="feature-name">{{ f.name }}</div>
            <div class="feature-desc">{{ f.desc }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const steps = [
  { title: '注册账号', desc: '点击左下角头像，填写企业/个人信息，完成两步注册' },
  { title: '登记产品', desc: '注册第二步填写主推产品信息，选择关键词标签，建议上传产品图片' },
  { title: '选择偏好', desc: '在创作页选择平台、风格、节日、目标用户等，越精确效果越好' },
  { title: '生成文案', desc: '点击右下角发送按钮，AI 多 Agent 工作流自动生成文案和海报' },
  { title: '调整下载', desc: '在结果页查看文案和海报，可输入进一步要求重新生成，满意后下载' },
]

const faqs = reactive([
  { q: '为什么文案总是在写我的平台而不是产品？', a: '这通常是因为产品信息没有完整登记。请确认已完成注册第二步（产品信息登记），填写产品名称、产地和关键词。', open: false },
  { q: '历史记录找不到了？', a: '历史记录存在浏览器本地（localStorage），按用户账号隔离。换浏览器或清除浏览器数据会导致历史丢失。', open: false },
  { q: '可以同时给多个平台生成文案吗？', a: '目前每次生成针对一个主平台。可以生成完后在"输入进一步需求"框里输入"改成适合抖音的风格"来切换风格。', open: false },
  { q: '如何让 AI 记住我的公司信息？', a: '进入工具箱页面，在"个人/公司信息补充"中填写获奖经历、种植年限等信息，AI 下次生成时会智能调用。', open: false },
  { q: '字数可以自定义吗？', a: '可以，在文本框中直接输入"生成200字的文案"，系统会自动识别字数要求。', open: false },
])

const features = [
  { icon: '✍️', name: '多 Agent 文案生成', desc: '6个AI Agent协同工作：读取档案→分析地域→加载标签→创作文案→质检→推荐标签' },
  { icon: '🖼️', name: 'AI 抠图合成海报', desc: '自动识别产品主体，去除背景，与模板合成海报，支持3种滤镜' },
  { icon: '🏷️', name: 'Neo4j 标签知识图谱', desc: '从知识图谱中精选最适合平台和地域文化的推荐标签' },
  { icon: '🧠', name: '特征记忆学习', desc: '每次对话中提到的产品特点自动存入数据库，下次生成时自动调用' },
  { icon: '📱', name: '实时排版预览', desc: '生成后可在手机框样式中预览文案、海报和标签的组合效果' },
  { icon: '📋', name: '历史记录', desc: '每次生成自动保存，包含文案、海报和标签，可随时恢复' },
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

/* 步骤 */
.steps { display: flex; flex-direction: column; gap: 12px; }
.step { display: flex; gap: 16px; align-items: flex-start; }
.step-num {
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg,#8bc34a,#6a994e);
  color: white; font-size: 13px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.step-title { font-size: 14px; font-weight: 600; color: #333; margin-bottom: 3px; }
.step-desc  { font-size: 13px; color: #888; line-height: 1.5; }

/* FAQ */
.faq-list { display: flex; flex-direction: column; gap: 8px; }
.faq-item  { border: 1px solid #e8e8e8; border-radius: 10px; overflow: hidden; }
.faq-q {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 16px; cursor: pointer; font-size: 14px; font-weight: 500; color: #333;
  transition: background .2s;
}
.faq-q:hover { background: #f9fafb; }
.faq-arrow { font-size: 12px; color: #aaa; transition: transform .2s; }
.faq-arrow.open { transform: rotate(180deg); }
.faq-a { padding: 12px 16px; background: #f9fafb; font-size: 13px; color: #666; line-height: 1.7; border-top: 1px solid #e8e8e8; }

/* 功能列表 */
.feature-list { display: flex; flex-direction: column; gap: 12px; }
.feature-item { display: flex; gap: 14px; align-items: flex-start; padding: 12px 14px; background: #f9fafb; border-radius: 10px; }
.feature-icon { font-size: 22px; flex-shrink: 0; }
.feature-name { font-size: 14px; font-weight: 600; color: #333; margin-bottom: 3px; }
.feature-desc { font-size: 13px; color: #888; line-height: 1.5; }

@media (max-width: 768px) { .page-wrapper { margin-left: 0; padding: 20px 16px; } }
</style>
