"""
语义服务 — 对应概要设计 2.3.5

NOTE: 接入 Ollama 运行本地 Qwen2.5-1.5B (由于 Qwen3 未出，使用 Qwen2.5 大致相同规模模型)
支持：
1. 状态解释生成
2. 自然语言规则解析
"""

import logging
import json
import httpx
import time

from app.schema.schemas import SemanticExplainResponse, NlRuleParseResponse, AbstractedState, StudyChatResponse
from app.config import OLLAMA_API_URL, OLLAMA_MODEL_NAME

logger = logging.getLogger(__name__)

TIMEOUT_SEC = 10.0
CHAT_TIMEOUT_SEC = 45.0


class SemanticService:
    """
    语义增强服务
    
    使用本地 Ollama Qwen 模型生成解释和解析规则。
    具备降级能力（网络错误/未启动时）。
    """

    def __init__(self) -> None:
        self._isAvailable = True

    @property
    def isAvailable(self) -> bool:
        return self._isAvailable

    async def _callOllama(self, prompt: str, timeout: float = TIMEOUT_SEC) -> str:
        """底层调用 Ollama API (异步版本，防止阻塞 WebSocket 视频流)"""
        payload = {
            "model": OLLAMA_MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
        try:
            async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
                response = await client.post(OLLAMA_API_URL, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama 调用失败: {e}")
            raise

    async def explain(self, currentState: str, abstractedState: AbstractedState, matchedRule: str | None, context: str = "") -> SemanticExplainResponse:
        """
        生成当前状态的语义解释
        """
        # 降级模板
        templates = {
            "专注": "系统检测到用户正在使用电脑或阅读书籍，且未发现分心行为，判定为专注状态。",
            "分心": "系统检测到用户正在使用手机，或头部严重偏移，因此判定为分心状态。",
            "低效": "系统检测到用户在座位上，但未检测到明显的学习行为或姿势异常，判定为低效状态。",
            "离开": "系统未检测到用户在摄像头画面中，判定为离开状态。",
        }
        template_text = templates.get(currentState, f"当前状态为「{currentState}」。")

        prompt = f"""你是一个友好的学习行为分析助手。请根据下方的判定状态和传感器数据，用不超过30个字的一句话，向用户解释为什么现在是这个状态。

当前判定状态：【{currentState}】
(匹配到的规则：{matchedRule or '系统默认规则'})

当前的实时传感器数据：
- 是否检测到人：{"是" if abstractedState.isPresent else "否"}
- 是否低头：{"是" if abstractedState.headDown else "否"}
- 是否东张西望(转头)：{"是" if abstractedState.headTurnedAway else "否"}
- 身体是否静止发呆：{"是" if abstractedState.postureStable else "否"}
- 静止发呆持续时间：{abstractedState.inactiveDuration:.1f} 秒
- 彻底离开画面时间：{abstractedState.awayDuration:.1f} 秒

这里有一些系统解释逻辑的参考：
- 如果状态是“离开”，通常是因为检测不到人。
- 如果状态是“分心”，通常是因为东张西望(转头)。
- 如果状态是“低效”，通常是因为静止发呆的时间太长了（没低头时超过30秒，低头时超过60秒）。
- 如果状态是“专注”，代表目前既没有离开，也没有乱看，且发呆时间在正常范围内。

要求：
1. 你的回答必须是一句通顺的中文，不要有任何换行，不要输出 Markdown。
2. 解释必须严格贴合上方给出的“实时传感器数据”。如果不贴合，你会受到惩罚。

参考范例：
范例1：当前判定状态为【分心】，是否转头为“是”。回答：“系统检测到您正在东张西望，注意力发生偏移。”
范例2：当前判定状态为【低效】，静止发呆持续时间为“35秒”。回答：“您已经发呆超过 30 秒了，请迅速调整回学习状态。”
范例3：当前判定状态为【专注】，是否低头为“是”。回答：“您正在低头伏案学习，请保持当前的专注力。”

请输出你的回答："""

        try:
            explanation = await self._callOllama(prompt)
            # 清理可能的 markdown 等
            explanation = explanation.replace("```", "").replace("\n", "").strip()
            return SemanticExplainResponse(
                state=currentState,
                explanation=explanation,
                source="vlm"
            )
        except Exception:
            return SemanticExplainResponse(
                state=currentState,
                explanation=template_text,
                source="template"
            )

    
    async def chat(
        self,
        message: str,
        currentState: str,
        stableDuration: float | None = None,
        abstractedState: AbstractedState | None = None,
    ) -> StudyChatResponse:
        """
        学习陪伴对话：优先调用本地 Ollama，失败时使用模板回复。
        """
        prompt = self._buildPlainChatPrompt(message)
        fallback_reply = self._buildPlainChatFallback(message)

        try:
            reply = await self._callOllama(prompt, timeout=CHAT_TIMEOUT_SEC)
            reply = self._cleanChatReply(reply)

            if not reply:
                reply = fallback_reply

            return StudyChatResponse(
                reply=reply,
                source="ollama",
                state=currentState,
                timestamp=time.time(),
            )
        except Exception as e:
            logger.warning(f"Study chat fallback: {e}")
            return StudyChatResponse(
                reply=fallback_reply,
                source="template",
                state=currentState,
                timestamp=time.time(),
            )

    def _buildPlainChatPrompt(self, message: str) -> str:
        """Build a normal text-chat prompt for the local Ollama model."""
        return f"""你是一个普通的中文文本对话助手。
请直接回应用户刚刚输入的内容，保持自然、简洁、友好。
不要复述学习状态，不要提到摄像头、检测结果或监控系统。
如果用户只是打招呼，就自然打招呼；如果用户提问，就回答问题；如果信息不足，可以问一个简短的澄清问题。
不要使用 Markdown，不要分条，控制在 1 到 3 句话。

用户消息：{message}

助手回复："""

    def _cleanChatReply(self, reply: str) -> str:
        """Normalize model output so the chat box receives plain text."""
        cleaned = reply.replace("```", "").strip()
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        return " ".join(lines)

    def _buildPlainChatFallback(self, message: str) -> str:
        """Fallback used when Ollama is unavailable."""
        normalized = message.strip().lower()

        if any(keyword in normalized for keyword in ["你好", "hello", "hi", "嗨"]):
            return "你好，我在。你可以直接和我聊天，也可以问我一个具体问题。"

        if any(keyword in normalized for keyword in ["谢谢", "thanks", "thank you"]):
            return "不客气，我会继续在这里陪你。"

        if message.strip().endswith(("?", "？")):
            return "这个问题我收到了，但当前本地模型暂时不可用。你可以稍后再试一次。"

        return "我收到了。当前本地模型暂时不可用，等 Ollama 恢复后就可以继续正常对话。"

    
    async def parseRule(self, ruleText: str) -> dict:
        """
        将自然语言规则解析为结构化规则
        """
        logger.info(f"自然语言规则解析: {ruleText}")

        prompt = f"""你是一个配置规则转化器。用户的系统支持根据传感器状态监控学习。用户的输入是自然语言描述的规则。你要将它转换为严格的 JSON 格式。

可用的传感器条件参数：
- head_turned_away: 布尔值 (头部是否明显偏离屏幕)
- head_down: 布尔值 (是否低头读写)
- face_visible: 布尔值 (脸部是否可见)
- is_present: 布尔值 (是否在场)
- posture_stable: 布尔值 (姿态是否稳定)
- duration_sec: 比较对象。例如 {{"min": 10}} 对应代码逻辑中的持续时间判断。
  （注：在 conditionJson 中请使用 {{"duration_sec": {{">": 10}}}} 这种格式）

输出的状态种类只能是："专注", "分心", "低效", "离开"。

用户输入："{ruleText}"

请根据输入，猜测规则名称（英文小写加下划线，例如 rule_distracted_10s）、条件和输出状态，并严格且**只输出 JSON 字符串**，不要包含任何前后缀或其他自然语言，不要用```包裹。格式示例：
{{"ruleName": "rule_name", "conditionJson": "{{\\"head_down\\": true, \\"duration_sec\\": {{\\">\\": 5}}}}", "outputState": "低效"}}
"""

        try:
            import re
            result_str = await self._callOllama(prompt)
            # 使用正则提取包裹的 JSON 以防模型输出多余解释废话
            match = re.search(r'\{.*\}', result_str, re.DOTALL)
            if match:
                result_str = match.group(0)
            
            parsed = json.loads(result_str)
            return {
                "success": True,
                "parsedRule": {
                    "ruleName": parsed.get("ruleName", "custom_rule"),
                    "conditionJson": parsed.get("conditionJson", "{}"),
                    "outputState": parsed.get("outputState", "未知"),
                },
                "rawText": ruleText
            }
        except Exception as e:
            logger.error(f"解析规则失败: {e}")
            return {
                "success": False,
                "error": "VLM 无法正确解析规则内容，请检查描述是否清晰或稍后再试。",
                "rawText": ruleText
            }

# 全局单例
semanticService = SemanticService()
