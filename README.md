# astrbot_plugin_qwen_audio_3.0

Qwen Audio 3.0 TTS 插件 —— 基于阿里云百炼 API 的非实时语音合成

## 功能

- 解析 LLM 回复中的 `<tts>...</tts>` 标签，调用 Qwen Audio 3.0 API 生成语音
- 支持 `$` 分隔符，让 AI 自由混合文字和语音
- 支持情感标签：`[excited]` `[sad]` `[angry]` `[laughing]` `[whispers]` 等
- 支持指令控制：通过自然语言描述控制语音表现力
- 支持多种音频格式：wav / mp3 / pcm
- 可配置提示词注入，教 AI 如何正确使用 `<tts>` 标签

## 配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `api_key` | 阿里云百炼 API Key（北京地域） | - |
| `workspace_id` | 百炼 Workspace ID | - |
| `model` | TTS 模型 | `qwen-audio-3.0-tts-flash` |
| `voice` | 系统音色 ID | `longanhuan_v3.6` |
| `instruction` | 指令控制文本（可选） | - |
| `format` | 音频格式 | `wav` |
| `sample_rate` | 采样率 | `24000` |
| `tts_prompt` | 注入 LLM 的 TTS 使用提示词 | 见配置默认值 |

## 使用说明

1. 在 AstrBot 插件管理器中启用插件
2. 填写 API Key 和 Workspace ID
3. LLM 会自动在回复中使用 `<tts>` 标签包裹需要转语音的文本

## 情感标签

在 `<tts>` 文本中使用以下标签控制语音：

**控制类**: `[sad]` `[amazed]` `[angry]` `[excited]` `[serious]` `[whispers]` `[trembling]` `[very slowly]` `[very fast]`

**富语言类**: `[laughing]` `[giggles]` `[sighing]` `[cough]` `[gasp]` `[clears throat]`

示例：`<tts>[excited]太棒了！[laughing]我们一起出去玩吧！</tts>`