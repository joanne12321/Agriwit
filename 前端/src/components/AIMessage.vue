<template>
  <div class="ai-message">
    <div class="ai-avatar" aria-label="AI头像"></div>
    <div class="ai-message-content">
      <div class="ai-text">
        <slot name="text">默认文本</slot>
      </div>
      <div class="ai-images-container">
        <div class="view-10">
          <div class="img-wrapper">
            <slot name="img1"></slot>
          </div>
          <div class="view-11">
            <slot name="img2"></slot>
          </div>
          <div class="view-12">
            <slot name="img3"></slot>
          </div>
        </div>
        <div class="ai-tools-container">
          <div class="ai-tools">
            <button class="view-13" @click="$emit('smartLayout')">智能排版</button>
            <button class="view-14" @click="$emit('aiMatting')">AI抠图</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineEmits(['smartLayout', 'aiMatting'])
</script>

<style scoped>
.ai-message {
  display: flex;
  align-items: flex-start;
  width: 100%;
  margin-bottom: 10px;
}

.ai-avatar {
  width: 48px;
  height: 48px;
  min-width: 48px;
  background: linear-gradient(135deg, #7dba28 0%, #51830a 100%);
  border-radius: 50%;
  margin-right: 20px;
  box-shadow: 0 6px 16px rgba(125, 186, 40, 0.2);
  position: relative;
  overflow: hidden;
  animation: pulse 3s infinite ease-in-out;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.03); }
}

.ai-avatar::before {
  content: '';
  position: absolute;
  width: 60%;
  height: 60%;
  background-color: white;
  border-radius: 50%;
  opacity: 0.2;
  filter: blur(2px);
}

.ai-avatar::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.3) 0%, transparent 70%);
}

.ai-message-content {
  flex: 1;
  max-width: calc(100% - 70px);
  background-color: #f9fafb;
  border-radius: 4px 18px 18px 18px;
  padding: 28px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  position: relative;
  border: 1px solid #e5e7eb;
}

.ai-message-content::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 24px;
  width: 16px;
  height: 16px;
  background-color: #f9fafb;
  transform: rotate(45deg);
  border-left: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;
}

.ai-text {
  font-family: "Inter", Helvetica;
  font-weight: 400;
  color: #4b5563;
  font-size: 17px;
  line-height: 1.7;
  margin-bottom: 28px;
}

.ai-images-container {
  width: 100%;
  margin-top: 20px;
  padding: 24px;
  background-color: #f8f9fa;
  border-radius: 14px;
  border: 1px solid #e9ecef;
  box-shadow: inset 0 2px 8px rgba(0,0,0,0.03);
  transition: all 0.3s;
}

.ai-images-container:hover {
  border-color: #dee2e6;
  box-shadow: inset 0 2px 12px rgba(0,0,0,0.05);
}

.view-10 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 20px;
}

.img-wrapper,
.view-11,
.view-12 {
  flex: 1;
  height: 180px;
  background-color: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.4s;
  border: 1px solid #f1f3f5;
}

.img-wrapper:hover,
.view-11:hover,
.view-12:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  z-index: 2;
  border-color: #7dba28;
}

.ai-tools-container {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
}

.ai-tools {
  display: flex;
  gap: 16px;
}

.view-13,
.view-14 {
  width: 120px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #7dba28 0%, #51830a 100%);
  border-radius: 10px;
  border: none;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(125, 186, 40, 0.3);
  font-family: "Inter", Helvetica;
  font-weight: 500;
  color: #ffffff;
  font-size: 16px;
}

.view-13:hover,
.view-14:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(125, 186, 40, 0.4);
}
</style>