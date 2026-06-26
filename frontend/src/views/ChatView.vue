<script setup>
// 智能问答页: SSE 流式 + markdown 渲染 + 思考过程折叠 + 工具调用展示
import { ref, nextTick, computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { chatStream } from '../api'

marked.setOptions({ breaks: true })

const messages = ref([])
const input = ref('')
const sending = ref(false)
const listRef = ref(null)
const abortCtrl = ref(null)

const toolLabel = {
  recommend: '位次推荐',
  score_to_rank: '位次换算',
  get_school_detail: '查学校详情',
  search_schools_by_text: '语义检索',
  get_thresholds: '查阈值',
}

function render(md) {
  return DOMPurify.sanitize(marked.parse(md || ''))
}

function scroll() {
  nextTick(() => {
    if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
  })
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: text })
  const assistant = {
    role: 'assistant', content: '', thinking: '', tools: [], streaming: true,
  }
  messages.value.push(assistant)
  sending.value = true
  scroll()

  // 历史 = 本轮 user/assistant 占位之前的对话(不含 tool 内部消息)
  const history = messages.value
    .slice(0, -2)
    .filter((m) => m.content)
    .map((m) => ({ role: m.role, content: m.content }))

  abortCtrl.value = new AbortController()
  try {
    await chatStream(
      text,
      history,
      (ev) => {
        if (ev.type === 'thinking') assistant.thinking += ev.text
        else if (ev.type === 'delta') { assistant.content += ev.text; scroll() }
        else if (ev.type === 'tool') assistant.tools.push(ev.name)
        else if (ev.type === 'done') assistant.streaming = false
        else if (ev.type === 'error') {
          assistant.content = (assistant.content ? assistant.content + '\n\n' : '') + '⚠️ ' + ev.message
          assistant.streaming = false
        }
      },
      abortCtrl.value.signal,
    )
  } catch (e) {
    if (e.name !== 'AbortError') {
      assistant.content = (assistant.content ? assistant.content + '\n\n' : '') + '⚠️ 网络错误: ' + e.message
    }
    assistant.streaming = false
  } finally {
    assistant.streaming = false
    sending.value = false
    abortCtrl.value = null
    scroll()
  }
}

function stop() {
  if (abortCtrl.value) abortCtrl.value.abort()
}

function onEnter(e) {
  if (e.shiftKey) return // 换行
  e.preventDefault()
  send()
}

const empty = computed(() => messages.value.length === 0)
const examples = [
  '我考720分能上哪些学校？',
  '孩子不自觉，想找个管得严的公办校，中考720有什么推荐？',
  '天津一中怎么样？有住宿吗？',
  '考700分在市内六区排多少名？',
]
</script>

<template>
  <div class="chat-page">
    <div ref="listRef" class="chat-messages">
      <!-- 空状态 -->
      <div v-if="empty" class="empty">
        <el-icon class="empty-icon"><ChatRound /></el-icon>
        <h2>智能问答</h2>
        <p class="muted">问我分数能上哪些学校、某校详情、按"管得严/校风自由"筛学校……<br />我会调用位次匹配与语义检索给你靠谱的回答。</p>
        <div class="examples">
          <el-button v-for="ex in examples" :key="ex" size="small" round @click="input = ex; send()">
            {{ ex }}
          </el-button>
        </div>
      </div>

      <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
        <div class="avatar">
          <el-icon v-if="m.role === 'user'"><User /></el-icon>
          <el-icon v-else><Promotion /></el-icon>
        </div>
        <div class="bubble">
          <template v-if="m.role === 'assistant'">
            <details v-if="m.thinking" class="thinking">
              <summary>思考过程</summary>
              <div class="thinking-text">{{ m.thinking }}</div>
            </details>
            <div v-if="m.tools.length" class="tools">
              <el-tag v-for="(t, j) in m.tools" :key="j" size="small" type="info" effect="plain">
                🔍 {{ toolLabel[t] || t }}
              </el-tag>
            </div>
            <div class="content" v-html="render(m.content)"></div>
            <span v-if="m.streaming && !m.content" class="waiting">思考中…</span>
            <span v-if="m.streaming && m.content" class="cursor">▍</span>
          </template>
          <template v-else>
            <div class="content user-content">{{ m.content }}</div>
          </template>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <el-input
        v-model="input"
        type="textarea"
        :rows="2"
        :disabled="sending"
        resize="none"
        placeholder="输入你的问题，Enter 发送，Shift+Enter 换行"
        @keydown.enter="onEnter"
      />
      <el-button v-if="!sending" type="primary" :icon="'Promotion'" :disabled="!input.trim()" @click="send">
        发送
      </el-button>
      <el-button v-else type="danger" plain @click="stop">停止</el-button>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  height: calc(100vh - 60px);
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  padding: 16px 20px 20px;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}
.empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 8px;
}
.empty-icon { font-size: 2.6rem; color: var(--el-color-primary); margin-bottom: 4px; }
.empty h2 { margin: 0; font-size: 1.4rem; }
.empty p { margin: 4px 0 12px; line-height: 1.7; }
.examples { display: flex; flex-direction: column; gap: 8px; align-items: center; }

.msg {
  display: flex;
  gap: 10px;
  margin-bottom: 18px;
  align-items: flex-start;
}
.msg.user { flex-direction: row-reverse; }
.avatar {
  width: 34px; height: 34px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.05rem;
  flex-shrink: 0;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}
.msg.user .avatar { background: #e8ecf3; color: var(--c-text-2); }
.bubble {
  max-width: 78%;
  padding: 12px 16px;
  border-radius: 14px;
  background: #fff;
  box-shadow: var(--shadow-card);
  border: 1px solid var(--c-border);
}
.msg.user .bubble {
  background: var(--el-color-primary);
  color: #fff;
  border-color: transparent;
}
.content { line-height: 1.7; font-size: 0.95rem; word-break: break-word; }
.content :deep(p) { margin: 6px 0; }
.content :deep(p:first-child) { margin-top: 0; }
.content :deep(p:last-child) { margin-bottom: 0; }
.content :deep(table) { border-collapse: collapse; margin: 8px 0; font-size: 0.88rem; }
.content :deep(th), .content :deep(td) { border: 1px solid var(--c-border); padding: 4px 10px; }
.content :deep(th) { background: #f7f8fb; }
.content :deep(h3), .content :deep(h4) { margin: 10px 0 6px; }
.content :deep(ul), .content :deep(ol) { padding-left: 22px; margin: 6px 0; }
.content :deep(code) { background: #f3f4f7; padding: 1px 5px; border-radius: 4px; font-size: 0.85em; }
.msg.user .content :deep(table), .msg.user .content :deep(th) { border-color: rgba(255,255,255,0.4); }
.user-content { white-space: pre-wrap; }

.thinking { margin-bottom: 8px; }
.thinking summary {
  cursor: pointer;
  font-size: 0.8rem;
  color: var(--c-muted);
  user-select: none;
}
.thinking-text {
  margin-top: 6px;
  font-size: 0.82rem;
  color: var(--c-muted);
  line-height: 1.6;
  white-space: pre-wrap;
  max-height: 240px;
  overflow-y: auto;
  padding: 8px 10px;
  background: #f7f8fb;
  border-radius: 8px;
}
.tools { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.waiting { color: var(--c-muted); font-size: 0.85rem; }
.cursor { color: var(--el-color-primary); animation: blink 1s steps(2) infinite; }
@keyframes blink { 50% { opacity: 0; } }

.chat-input {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--c-border);
}
.chat-input :deep(.el-textarea__inner) { border-radius: 10px; }
</style>
