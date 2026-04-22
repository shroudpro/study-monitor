<script setup lang="ts">
/**
 * 规则管理组件
 *
 * 支持查看/添加/启停/删除行为规则
 * 集成了 VLM 自然语言规则解析
 */
import { ref, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import type { BehaviorRule, RuleCreateRequest, ParsedRuleItem } from '@/types'

const { getRules, createRule, deleteRule, toggleRule, parseNlRule, loading: apiLoading } = useApi()

const rules = ref<BehaviorRule[]>([])
const showForm = ref(false)
const showNlForm = ref(false)

const nlText = ref('')
const parsedPreview = ref<ParsedRuleItem | null>(null)
const parseError = ref<string | null>(null)

const newRule = ref<RuleCreateRequest>({
  ruleName: '',
  conditionJson: '{"head_turned_away": true, "duration_sec": {">": 10}}',
  outputState: '分心',
})

async function loadRules() {
  rules.value = await getRules()
}

onMounted(() => {
  loadRules()
})

async function handleCreate(ruleData: RuleCreateRequest) {
  const result = await createRule(ruleData)
  if (result) {
    showForm.value = false
    showNlForm.value = false
    parsedPreview.value = null
    nlText.value = ''
    newRule.value = {
      ruleName: '',
      conditionJson: '{"head_turned_away": true, "duration_sec": {">": 10}}',
      outputState: '分心',
    }
    await loadRules()
  }
}

async function handleDelete(id: number) {
  const ok = await deleteRule(id)
  if (ok) await loadRules()
}

async function handleToggle(rule: BehaviorRule) {
  const ok = await toggleRule(rule.id, !rule.enabled)
  if (ok) await loadRules()
}

async function handleParseNl() {
  if (!nlText.value.trim()) return
  parseError.value = null
  parsedPreview.value = null
  
  const res = await parseNlRule(nlText.value)
  if (res && res.success && res.parsedRule) {
    parsedPreview.value = res.parsedRule
  } else {
    parseError.value = res?.error || "无法解析此规则，请检查描述"
  }
}

function confirmParsedRule() {
  if (!parsedPreview.value) return
  handleCreate({
    ruleName: parsedPreview.value.ruleName,
    conditionJson: typeof parsedPreview.value.conditionJson === 'string' ? parsedPreview.value.conditionJson : JSON.stringify(parsedPreview.value.conditionJson),
    outputState: parsedPreview.value.outputState
  })
}

onMounted(loadRules)
</script>

<template>
  <div class="card">
    <div class="card-header">
      <span class="card-title flex items-center">
        行为规则
        <!-- Guide tooltip icon -->
        <div class="tooltip-container ml-2">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-secondary cursor-help">
            <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
          </svg>
          <div class="tooltip-content shadow-lg">
            <div class="font-bold mb-1 border-b pb-1 text-sm">构建无冲突规则指南</div>
            <ul class="text-xs list-disc pl-4 space-y-1">
              <li>可用变量：<strong>不在场、脸不可见、低头、偏头、稳定、持续时间</strong>。</li>
              <li>目标类别：<strong>专注、分心、低效、离开</strong>。</li>
              <li><strong>系统默认规则：</strong>
                <ul class="pl-4 mt-1 list-circle">
                  <li><strong>离开：</strong>不在画面超过 5s</li>
                  <li><strong>分心：</strong>非低头时偏头(东张西望)超过 10s</li>
                  <li><strong>专注：</strong>低头读写(允许静止60s) 或 看屏幕(允许静止30s)</li>
                  <li><strong>低效：</strong>兜底惩罚由于发呆超出容忍时长(>30s 或 >60s)的情况</li>
                </ul>
              </li>
              <li>规则优先级：自定义规则 > 系统默认。</li>
              <li>避免冲突：描述清晰且不重叠。例如有了"低头5s判定分心"，就不要再写"低头10s判定低效"。</li>
            </ul>
            <div class="mt-3 border-t pt-2">
              <div class="font-bold mb-1 text-sm text-primary">⚙️ 手动 JSON 规则参数字典</div>
              <ul class="text-xs list-disc pl-4 space-y-1 text-gray-600">
                <li><code>is_present</code>: 布尔值 (是否检测到人)</li>
                <li><code>face_visible</code>: 布尔值 (是否看到脸)</li>
                <li><code>head_down</code>: 布尔值 (是否低头)</li>
                <li><code>head_turned_away</code>: 布尔值 (是否歪头东张西望)</li>
                <li><code>posture_stable</code>: 布尔值 (姿势是否静止)</li>
                <li><code>duration_sec</code>: 持续时间(秒)。比较符格式如：<code class="bg-gray-100 p-0.5 rounded">{"duration_sec": {">": 5}}</code></li>
              </ul>
              <div class="mt-2 bg-gray-50 p-2 rounded text-xs">
                <strong>实例：手动添加“严重离开”规则</strong><br/>
                如果你想配置一个“人不在超过 30 秒判定离开”的规则：<br/>
                状态选 <code>离开</code>，条件填写：<br/>
                <code class="block mt-1 text-gray-700 whitespace-pre">{"is_present": false, "duration_sec": {">": 30}}</code>
              </div>
            </div>
          </div>
        </div>
      </span>
      <div class="flex gap-2">
        <button
          class="btn btn-sm"
          :class="showNlForm ? 'btn-danger' : 'btn-outline'"
          @click="showNlForm = !showNlForm; showForm = false"
        >
          AI生成
        </button>
        <button
          class="btn btn-sm"
          :class="showForm ? 'btn-danger' : 'btn-primary'"
          @click="showForm = !showForm; showNlForm = false"
        >
          {{ showForm ? '取消' : '+ 手动' }}
        </button>
      </div>
    </div>

    <!-- 自然语言生成规则表单 -->
    <div v-if="showNlForm" class="rule-form animate-slide-in bg-neutral-50 p-3 rounded-md mb-4 border border-neutral-200">
      <div class="font-bold text-sm mb-2 text-primary">自然语言创建规则</div>
      <div class="flex gap-2">
        <input
          v-model="nlText"
          class="input flex-1"
          placeholder="例如：连续转头超过8秒判定为分心"
          @keyup.enter="handleParseNl"
        />
        <button class="btn btn-primary" @click="handleParseNl" :disabled="apiLoading">
          {{ apiLoading ? '解析中...' : '解析' }}
        </button>
      </div>

      <!-- 解析结果预览 -->
      <div v-if="parseError" class="mt-3 text-xs text-error p-2 bg-red-50 rounded border border-red-100">
        {{ parseError }}
      </div>
      <div v-if="parsedPreview" class="mt-3 p-3 bg-white rounded border border-neutral-200 shadow-sm transition-all">
        <div class="text-xs text-secondary mb-2">解析结果预览，请确认无误：</div>
        <div class="grid-preview text-sm font-data">
          <div><span class="text-tertiary">名称:</span> {{ parsedPreview.ruleName }}</div>
          <div><span class="text-tertiary">判定:</span> 
            <span :class="'state-text-' + parsedPreview.outputState">{{ parsedPreview.outputState }}</span>
          </div>
          <div class="col-span-2 mt-1">
            <span class="text-tertiary">条件:</span> 
            <div class="bg-neutral-50 p-2 rounded mt-1 border border-neutral-100 text-xs overflow-x-auto">
              {{ typeof parsedPreview.conditionJson === 'string' ? parsedPreview.conditionJson : JSON.stringify(parsedPreview.conditionJson) }}
            </div>
          </div>
        </div>
        <div class="flex gap-2 mt-3 justify-end">
          <button class="btn btn-sm btn-outline" @click="parsedPreview = null">取消</button>
          <button class="btn btn-sm btn-primary" @click="confirmParsedRule">确认并添加</button>
        </div>
      </div>
    </div>

    <!-- 手动添加规则表单 -->
    <div v-if="showForm" class="rule-form animate-slide-in">
      <input
        v-model="newRule.ruleName"
        class="input"
        placeholder="规则名称，如 phone_distraction_10s"
      />
      <textarea
        v-model="newRule.conditionJson"
        class="input rule-textarea"
        placeholder='JSON 条件，如 {"using_phone": true}'
        rows="3"
      />
      <div class="form-row">
        <select v-model="newRule.outputState" class="input">
          <option value="专注">专注</option>
          <option value="分心">分心</option>
          <option value="低效">低效</option>
          <option value="离开">离开</option>
        </select>
        <button class="btn btn-primary" @click="handleCreate(newRule)">
          保存规则
        </button>
      </div>
    </div>

    <!-- 规则列表 -->
    <div class="rule-list">
      <div
        v-for="rule in rules"
        :key="rule.id"
        class="rule-item"
        :class="{ disabled: !rule.enabled }"
      >
        <div class="rule-info">
          <div class="rule-name data-readout">
            <span class="value">{{ rule.ruleName }}</span>
          </div>
          <div class="rule-meta">
            <span :class="['tag', rule.enabled ? 'tag-enabled' : 'tag-disabled']">
              {{ rule.enabled ? 'ON' : 'OFF' }}
            </span>
            <span class="tag tag-output">
              → {{ rule.outputState }}
            </span>
          </div>
        </div>
        <div class="rule-actions">
          <button
            class="btn btn-sm"
            @click="handleToggle(rule)"
          >
            {{ rule.enabled ? '停用' : '启用' }}
          </button>
          <button
            class="btn btn-sm btn-danger"
            @click="handleDelete(rule.id)"
          >
            删除
          </button>
        </div>
      </div>

      <div v-if="rules.length === 0" class="no-rules data-readout">
        暂无自定义规则，使用系统默认规则
      </div>
    </div>
  </div>
</template>

<style scoped>
.tooltip-container {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.w-4 { width: 16px; }
.h-4 { height: 16px; }
.cursor-help { cursor: help; }

.tooltip-content {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: var(--space-2);
  width: 280px;
  background: white;
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  z-index: 50;
  color: var(--color-neutral-800);
}

.tooltip-container:hover .tooltip-content {
  display: block;
}

.list-disc { list-style-type: disc; }
.space-y-1 > * + * { margin-top: var(--space-1); }
.border-b { border-bottom: 1px solid var(--color-neutral-200); }
.pb-1 { padding-bottom: var(--space-1); }
.mb-1 { margin-bottom: var(--space-1); }
.pl-4 { padding-left: var(--space-4); }

.bg-neutral-50 { background-color: var(--color-neutral-50); }
.p-3 { padding: var(--space-3); }
.rounded-md { border-radius: var(--radius-md); }
.mb-4 { margin-bottom: var(--space-4); }
.border { border: 1px solid var(--color-neutral-200); }
.flex-1 { flex: 1; }
.mt-3 { margin-top: var(--space-3); }
.p-2 { padding: var(--space-2); }
.bg-red-50 { background-color: #fef2f2; }
.border-red-100 { border-color: #fee2e2; }
.bg-white { background-color: white; }
.rounded { border-radius: 4px; }
.shadow-sm { box-shadow: var(--shadow-1); }
.mb-2 { margin-bottom: var(--space-2); }
.grid-preview { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); }
.col-span-2 { grid-column: span 2 / span 2; }
.overflow-x-auto { overflow-x: auto; }
.mt-1 { margin-top: var(--space-1); }

.transition-all { transition: all var(--transition-normal); }

.state-text-专注 { color: var(--color-success); font-weight: bold; }
.state-text-分心 { color: var(--color-error); font-weight: bold; }
.state-text-低效 { color: var(--color-warning); font-weight: bold; }
.state-text-离开 { color: var(--color-neutral-500); font-weight: bold; }

.rule-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-neutral-200);
}

.rule-textarea {
  resize: vertical;
  min-height: 60px;
}

.form-row {
  display: flex;
  gap: var(--space-2);
}

.form-row select {
  flex: 1;
}

.rule-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-height: 300px;
  overflow-y: auto;
}

.rule-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3);
  background: var(--color-bg-body);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  transition: border-color var(--transition-fast);
}

.rule-item:hover {
  border-color: var(--color-neutral-300);
}

.rule-item.disabled {
  opacity: 0.5;
}

.rule-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.rule-name {
  font-size: var(--text-sm);
  font-weight: 600;
}

.rule-meta {
  display: flex;
  gap: var(--space-2);
}

.rule-actions {
  display: flex;
  gap: var(--space-1);
}

.no-rules {
  text-align: center;
  padding: var(--space-6);
  color: var(--color-neutral-500);
}

.tag-output {
  border-color: var(--color-neutral-300);
  color: var(--color-neutral-900);
}
</style>
