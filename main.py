import re
import httpx
import traceback
from pathlib import Path
from datetime import datetime

from astrbot.api.event import AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api.event.filter import on_llm_request, on_decorating_result
from astrbot.api.message_components import Plain, Record
from astrbot.core.provider.entities import ProviderRequest
from astrbot.core.utils.astrbot_path import get_astrbot_data_path
from astrbot.core import logger

# ─── TTS 标签正则 ───
TTS_PATTERN = re.compile(r"<tts>(.*?)</tts>", re.DOTALL)
TTS_START_TAG = "<tts>"
TTS_END_TAG = "</tts>"
BOUNDARY_SEPARATORS = "$"
BOUNDARY_SEPARATOR_PATTERN = re.compile(rf"[{re.escape(BOUNDARY_SEPARATORS)}]+$")
LEADING_BOUNDARY_SEPARATOR_PATTERN = re.compile(
    rf"^[{re.escape(BOUNDARY_SEPARATORS)}]+"
)

# ─── Qwen Audio 3.0 TTS API 端点 ───
QWEN_AUDIO_TTS_API = "https://{workspace_id}.cn-beijing.maas.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer"


class QwenAudioTTSPlugin(Star):
    """Qwen Audio 3.0 TTS 插件 —— 基于阿里云百炼 API 的非实时语音合成"""

    def __init__(self, context: Context, config: dict = None):
        super().__init__(context, config)
        self.config = config or {}
        self._own_name = "astrbot_plugin_qwen_audio_3.0"

    # ─── 辅助方法 ───

    @staticmethod
    def _trim_boundary_separators(text: str, *, leading: bool = False) -> str:
        if leading:
            return LEADING_BOUNDARY_SEPARATOR_PATTERN.sub("", text)
        return BOUNDARY_SEPARATOR_PATTERN.sub("", text)

    @classmethod
    def _append_text_segment(cls, segments: list[dict], text: str) -> None:
        stripped = text.strip()
        if not stripped:
            return
        if segments and segments[-1]["type"] == "tts":
            stripped = cls._trim_boundary_separators(stripped, leading=True).strip()
        stripped = cls._trim_boundary_separators(stripped).strip()
        if stripped:
            segments.append({"type": "text", "content": stripped})

    @classmethod
    def _split_by_tts_tags(cls, text: str) -> list[dict]:
        """将文本按 <tts>...</tts> 标签拆分成段落列表。"""
        segments = []
        cursor = 0
        text_length = len(text)

        while cursor < text_length:
            start = text.find(TTS_START_TAG, cursor)
            end = text.find(TTS_END_TAG, cursor)

            if start == -1 and end == -1:
                cls._append_text_segment(segments, text[cursor:])
                break
            if end != -1 and (start == -1 or end < start):
                cls._append_text_segment(segments, text[cursor:end])
                cursor = end + len(TTS_END_TAG)
                continue
            if start > cursor:
                cls._append_text_segment(segments, text[cursor:start])
            if start == -1:
                break
            end = text.find(TTS_END_TAG, start + len(TTS_START_TAG))
            if end == -1:
                cls._append_text_segment(segments, text[start + len(TTS_START_TAG):])
                break
            tts_content = text[start + len(TTS_START_TAG): end].strip()
            tts_content = cls._trim_boundary_separators(
                cls._trim_boundary_separators(tts_content, leading=True),
            ).strip()
            if tts_content:
                segments.append({"type": "tts", "content": tts_content})
            cursor = end + len(TTS_END_TAG)

        if not segments:
            stripped = text.replace(TTS_START_TAG, "").replace(TTS_END_TAG, "").strip()
            if stripped:
                segments.append({"type": "text", "content": stripped})
        return segments

    # ─── 配置获取 ───

    def _get_cfg(self, key: str, default=None):
        return self.config.get(key, default)

    # ─── LLM 请求前注入 TTS 提示词 ───

    @on_llm_request()
    async def on_llm_req(self, event: AstrMessageEvent, request: ProviderRequest):
        tts_prompt = self._get_cfg("tts_prompt", "")
        if not tts_prompt:
            return
        request.system_prompt += f"\n{tts_prompt}"

    # ─── 结果装饰：处理 TTS 标签 ───

    @on_decorating_result(priority=13)
    async def on_decorate(self, event: AstrMessageEvent):
        result = event.get_result()
        if not result or not result.chain:
            return

        has_tts_tag = any(
            isinstance(comp, Plain)
            and (TTS_START_TAG in comp.text or TTS_END_TAG in comp.text)
            for comp in result.chain
        )
        if not has_tts_tag:
            return

        new_chain = []
        modified = False
        for comp in result.chain:
            if isinstance(comp, Plain) and (
                TTS_START_TAG in comp.text or TTS_END_TAG in comp.text
            ):
                components = await self._process_tts_text(comp.text)
                new_chain.extend(components)
                modified = True
            else:
                new_chain.append(comp)

        if modified:
            result.chain = new_chain

    async def _process_tts_text(self, text: str) -> list:
        segments = self._split_by_tts_tags(text)
        components = []
        for seg in segments:
            if seg["type"] == "text":
                components.append(Plain(seg["content"]))
            elif seg["type"] == "tts":
                audio_component = await self._synthesize(seg["content"])
                if audio_component:
                    components.append(audio_component)
                else:
                    components.append(Plain(seg["content"]))
        return components

    # ─── 核心 TTS 合成 ───

    async def _synthesize(self, text: str) -> Record | None:
        api_key = self._get_cfg("api_key", "")
        workspace_id = self._get_cfg("workspace_id", "")
        model = self._get_cfg("model", "qwen-audio-3.0-tts-flash")
        voice = self._get_cfg("voice", "longanhuan_v3.6")
        instruction = self._get_cfg("instruction", "")
        format_type = self._get_cfg("format", "wav")
        sample_rate = self._get_cfg("sample_rate", 24000)

        if not api_key or not workspace_id:
            logger.error("Qwen Audio TTS: api_key 或 workspace_id 未配置")
            return None

        url = QWEN_AUDIO_TTS_API.format(workspace_id=workspace_id)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "input": {
                "text": text,
                "voice": voice,
                "format": format_type,
                "sample_rate": sample_rate,
            },
        }
        if instruction:
            payload["input"]["instruction"] = instruction

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            # 响应格式: {"output": {"audio": {"url": "...", "expires_at": "..."}}}
            audio_url = data.get("output", {}).get("audio", {}).get("url")
            if not audio_url:
                logger.error(f"TTS API 未返回音频 URL: {data}")
                return None

            # 下载音频文件
            audio_path = await self._download_audio(audio_url, format_type)
            if not audio_path:
                return None

            return Record.fromFileSystem(audio_path, text=text)

        except Exception as e:
            logger.error(f"TTS 合成失败: {e}")
            logger.debug(traceback.format_exc())
            return None

    async def _download_audio(self, url: str, fmt: str) -> str | None:
        """下载音频到 AstrBot data 目录并返回本地路径。"""
        try:
            data_dir = Path(get_astrbot_data_path()) / "qwen_audio_tts"
            data_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"tts_{timestamp}.{fmt}"
            filepath = data_dir / filename

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                filepath.write_bytes(resp.content)

            logger.info(f"TTS 音频已保存: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"下载音频失败: {e}")
            return None