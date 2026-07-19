// useImagePipeline.js  ── 放在 src/composables/ 目录
// 在 Creation.vue 里 import { useImagePipeline } from '@/composables/useImagePipeline'

import { ref } from 'vue'

const IMG_API = 'http://localhost:5003'

export function useImagePipeline() {
    const isProcessing   = ref(false)
    const progress       = ref(0)       // 0-100
    const progressStep   = ref('')      // "正在抠图…" / "生成滤镜版本 2/4…"
    const posterVersions = ref(null)
    const cutoutBase64   = ref('')
    const errorMsg       = ref('')

    let pollTimer = null

    // ── 轮询任务进度 ──
    const pollTask = (taskId, resolve, reject) => {
        pollTimer = setInterval(async () => {
            try {
                const res  = await fetch(`${IMG_API}/api/task/${taskId}`)
                const data = await res.json()

                progress.value     = data.progress || 0
                progressStep.value = data.step     || ''

                if (data.status === 'done') {
                    clearInterval(pollTimer)
                    posterVersions.value = data.poster_versions
                    cutoutBase64.value   = data.cutout_base64 || ''
                    isProcessing.value   = false
                    resolve(data)
                } else if (data.status === 'error') {
                    clearInterval(pollTimer)
                    isProcessing.value = false
                    errorMsg.value     = data.error || '处理失败'
                    reject(new Error(data.error))
                }
            } catch (e) {
                clearInterval(pollTimer)
                isProcessing.value = false
                errorMsg.value     = '图片服务连接失败'
                reject(e)
            }
        }, 1000)   // 每秒轮询一次
    }

    // ── 主函数：提交任务 ──
    const runPipeline = (imageBase64, templateId, filters = ['original', 'warm', 'vivid', 'vintage']) => {
        return new Promise(async (resolve, reject) => {
            isProcessing.value   = true
            progress.value       = 0
            progressStep.value   = '正在提交任务…'
            posterVersions.value = null
            errorMsg.value       = ''

            try {
                const res  = await fetch(`${IMG_API}/api/image/full-pipeline`, {
                    method:  'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body:    JSON.stringify({
                        image_base64: imageBase64,
                        template_id:  templateId || 'green_gradient',
                        size:         [1080, 1080],
                        position:     'center',
                        filters
                    })
                })
                const data = await res.json()

                if (data.task_id) {
                    progressStep.value = '任务已提交，处理中…'
                    pollTask(data.task_id, resolve, reject)
                } else {
                    throw new Error(data.error || '提交失败')
                }
            } catch (e) {
                isProcessing.value = false
                errorMsg.value     = e.message
                reject(e)
            }
        })
    }

    const cancel = () => {
        if (pollTimer) clearInterval(pollTimer)
        isProcessing.value = false
        progress.value     = 0
        progressStep.value = ''
    }

    return { isProcessing, progress, progressStep, posterVersions, cutoutBase64, errorMsg, runPipeline, cancel }
}