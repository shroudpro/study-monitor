<script setup lang="ts">
/**
 * 视频流展示组件
 *
 * 通过 WebSocket 接收后端推送的标注帧，显示实时摄像头画面
 */
defineProps<{
  frame: string
  isConnected: boolean
}>()

const emit = defineEmits<{
  startCamera: []
}>()
</script>

<template>
  <div class="card">
    <div class="card-header">
      <span class="card-title">实时监测画面</span>
      <span v-if="isConnected" class="data-readout">
        <span class="value">LIVE</span>
      </span>
    </div>

    <div class="video-container">
      <!-- 有视频帧时显示 -->
      <img
        v-if="frame"
        :src="'data:image/jpeg;base64,' + frame"
        alt="实时检测画面"
      />

      <!-- 无视频帧时显示占位 -->
      <div v-else class="video-placeholder">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="video-placeholder-icon">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6.827 6.175A2.31 2.31 0 015.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 00-1.134-.175 2.31 2.31 0 01-1.64-1.055l-.822-1.316a2.192 2.192 0 00-1.736-1.039 48.774 48.774 0 00-5.232 0 2.192 2.192 0 00-1.736 1.039l-.821 1.316z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 12.75a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0zM18.75 10.5h.008v.008h-.008V10.5z" />
        </svg>
        <span class="text-sm text-secondary font-medium">等待摄像头连接...</span>
        <button
          class="btn btn-primary"
          @click="emit('startCamera')"
          style="margin-top: var(--space-4);"
        >
          启动检测
        </button>
      </div>

      <!-- 视频底部覆盖层 -->
      <div v-if="frame" class="video-overlay">
        <span class="text-sm text-neutral-100 font-medium tracking-wider">
          <span>640×480</span>
          <span class="text-xs text-neutral-300 ml-1"> @ 15fps</span>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.video-container {
  position: relative;
  width: 100%;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-neutral-900);
  border: 1px solid var(--color-neutral-200);
  aspect-ratio: 16 / 10;
}

.video-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.video-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: var(--space-3) var(--space-4);
  background: linear-gradient(transparent, rgba(17, 24, 39, 0.9));
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}

.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  gap: var(--space-2);
  color: var(--color-neutral-500);
}

.video-placeholder-icon {
  width: 48px;
  height: 48px;
  opacity: 0.5;
  margin-bottom: var(--space-2);
}

.font-medium { font-family: var(--font-data); font-weight: 500; }
.tracking-wider { letter-spacing: 0.05em; }
.ml-1 { margin-left: var(--space-1); }
.text-neutral-100 { color: var(--color-neutral-100); }
.text-neutral-300 { color: var(--color-neutral-300); }
</style>
