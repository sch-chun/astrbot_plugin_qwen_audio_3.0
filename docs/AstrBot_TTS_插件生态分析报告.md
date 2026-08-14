# AstrBot TTS 插件生态源码分析报告

> 生成时间：2025-08-14
> 分析范围：GitHub 上所有已知的 AstrBot TTS 插件（共检索到 40+ 个相关仓库，本报告深度分析其中 11 个核心插件）

---

## 一、插件生态总览

### 1.1 生态规模

通过搜索关键词 `astrbot tts`、`astrbot 语音合成`、`astrbot voice`、`astrbot_plugin_tts`，共发现 **40+ 个 TTS 相关仓库**。按照功能定位可分类如下：

| 类别 | 数量 | 代表插件 |
|------|------|----------|
| 单引擎 TTS（GPT-SoVITS） | ~8 | Zhalslar/astrbot_plugin_GPT_SoVITS, w2902171175/astrbot_plugin_GPT-SoVITS |
| 单引擎 TTS（MiMo/小米） | ~8 | Justice-ocr/astrbot_plugin_mimo_tts_clone, QingchenWait/astrbot_plugin_mimo_tts_voiceclone |
| 单引擎 TTS（Qwen3-TTS） | ~3 | Dioxgen/AstrBot-LLM-Qwen3-TTS, Thyran1/astrbot_plugin_qwen3_tts |
| 单引擎 TTS（CosyVoice2） | ~3 | xiewoc/astrbot_plugin_tts_Cosyvoice2, ikeDong/astrbot_plugin_siliconflow_tts |
| 单引擎 TTS（Gemini） | ~2 | KitsuneiMomo/astrbot_plugin_gemini_tts, zgojin/AstrBot_Plugins_GeminiTTS |
| 单引擎 TTS（Edge TTS/免费） | ~2 | 768120982Aa/astrbot_plugin_mimo_tts |
| 情绪路由型 TTS | ~2 | muyouzhi6/astrbot_plugin_tts_emotion_router, charlie237/astrbot_plugin_tts_emotion |
| 翻译+TTS 复合型 | ~2 | miku05231/astrbot_plugin_translate_tts, clown145/astrbot_plugin_tts_llm |
| 输出管道型（TTS 为其中一步） | ~1 | Zhalslar/astrbot_plugin_outputpro |
| 标记系统型（LLM 决策） | ~2 | Dioxgen/AstrBot-LLM-Qwen3-TTS, sch-chun/astrbot_plugin_qwen_audio_3.0 |
| 其他（VOICEVOX/AivisSpeech/VoxCPM2 等） | ~5 | zouyonghe/astrbot_plugin_voicevox, bemlyyyyyyyyyyyy/astrbot_plugin_aivisspeech |
| 语音片段/语音库（非 TTS 合成） | ~6 | luori7hao/astrbot_plugin_xinsanguo_voice, MikCslu/astrbot_plugin_voice_library |
| TTS 辅助（文本过滤等） | ~1 | Luna-channel/astrbot_plugin_tts_sanitizer |

### 1.2 生态发展趋势

- **2025年2-4月**：早期插件以单引擎对接为主（GPT-SoVITS、CosyVoice2、VOICEVOX）
- **2025年8-10月**：开始出现情绪路由、多引擎、LLM 驱动型插件
- **2026年3-8月**：爆发式增长，MiMo/Qwen3-TTS/Gemini 等新引擎涌现，出现 AI 语音导演、背景任务队列等高级架构

---

## 二、逐插件详细分析

### 2.1 Zhalslar/astrbot_plugin_GPT_SoVITS（v3.1.0）

**定位**：模块化 GPT-SoVITS 对接插件，支持自定义音色和情绪

**架构**：
```
main.py (GPTSoVITSPlugin - 入口层)
├── core/config.py    (PluginConfig - 强类型配置树, ConfigNode 基类)
├── core/client.py    (GSVApiClient - HTTP 通信层)
├── core/service.py   (GPTSoVITSService - 业务逻辑层, 含缓存)
├── core/emotion.py   (EmotionJudger - LLM 情感分析)
├── core/entry.py     (EntryManager - 情绪条目管理, 关键词匹配)
└── core/local_data.py (LocalDataManager - 音频缓存管理)
```

**触发机制**（三重）：
1. **`@filter.on_decorating_result(priority=14)`**：自动模式，对 LLM 回复概率触发（`tts_prob`），仅处理纯文本消息，有最大长度限制
2. **`@filter.command("说")`**：指令触发，直接调用 GSV 合成
3. **`@filter.llm_tool()`**：LLM Tool Call 触发，LLM 自主决定何时发送语音

**情绪/语速控制**：
- **LLM 情感判别**：`EmotionJudger` 调用 LLM 分析文本情感，返回 JSON 格式 `{"emotion": "开心"}`
- **关键词匹配降级**：LLM 判别失败时，通过 `EntryManager.match_entry()` 做关键词匹配
- **情绪条目系统**：每个情绪条目包含 `ref_audio_path`、`prompt_text`、`prompt_lang`、`speed_factor`、`fragment_interval`，映射为 GPT-SoVITS 的 API 参数
- 缓存机制：`event.set_extra("emotion", ...)` 避免重复调用 LLM

**TTS 引擎**：单一 GPT-SoVITS（本地部署 HTTP API），通过 `GSVApiClient` 调用 `/tts`、`/set_gpt_weights`、`/set_sovits_weights`、`/control` 端点

**可扩展性**：单引擎绑定，但模块化程度高，`ConfigNode` 强类型配置树设计优秀

**优点**：
- 架构清晰，配置强类型化（`ConfigNode` 基类 + 类型注解 + 自动写回）
- 三重触发机制覆盖所有场景
- LLM 情感判别 + 关键词匹配的双重保障
- 音频缓存机制避免重复合成

**缺点**：
- 仅支持 GPT-SoVITS 单引擎
- 无多音色/多角色管理
- 无后台异步队列

---

### 2.2 Justice-ocr/astrbot_plugin_mimo_tts_clone（v0.6.1）

**定位**：MiMo 官方 API TTS 音色克隆插件，具备 AI 语音导演、情绪路由、多音色管理、后台任务队列

**架构**：
```
main.py (MimoTTSClonePlugin - 64KB, 极其庞大)
├── core/config.py           (配置归一化 + 构建)
├── core/emotion.py           (EmotionRouter - 情绪路由)
├── core/mimo_official_client.py (MiMo API 客户端)
├── core/style_director.py    (AI 语音导演 - 二次 LLM 调用)
├── core/synthesis_context.py (TTS 上下文构建 + 缓存)
├── core/text_processing.py   (文本清洗 + 分段)
├── core/tts_jobs.py          (TTSJobManager - 后台任务队列)
├── core/tts_reliability.py   (ReliabilityController - 熔断/限流/重试)
├── core/voice_store.py       (VoiceProfile/VoiceStore - 音色管理)
├── core/wav_utils.py         (WAV 合并工具)
├── core/audio_codec.py       (音频编码)
└── pages_api.py              (Pages Web 管理 API)
```

**触发机制**（四重）：
1. **`@filter.on_decorating_result()`**：自动 TTS，概率门控（`auto_tts_probability`），黑白名单（群聊/私聊独立），管理员绕过
2. **`@filter.command("tts")`**：指令触发，支持 `-v 音色名 -e happy -c 风格指令` 参数解析
3. **`@filter.llm_tool(name="mimo_tts_speak")`**：LLM Tool Call，支持 emotion/voice/style 参数
4. **后台延迟队列**：`_defer_background_job_until_message_sent()` 确保文字先于语音发送

**情绪/语速控制**：
- **情绪路由**：`EmotionRouter` 支持四种情绪（happy/sad/angry/neutral），根据情绪映射不同音色
- **AI 语音导演**（核心亮点）：`generate_style_plan()` 调用 LLM 生成风格指令（`style_context`），可优化朗读文本，带 10 分钟 LRU 缓存
- **音色风格标签**：每个 VoiceProfile 有 `style_tags`（如 `[开心]`），前置拼接到文本
- **语速/上下文**：通过 `context` 参数传递风格指令给 MiMo API

**TTS 引擎**：单一 MiMo 官方 API（声音克隆），通过 `MimoOfficialClient` 调用

**可扩展性**：单引擎，但对外暴露 `synthesize_text()` 和 `text_to_speech()` 方法，可被其他插件复用

**工程亮点**：
- **后台任务队列**：`TTSJobManager` 支持持久化、恢复、取消、清理，含工作线程池
- **可靠性控制器**：`ReliabilityController` 实现限流（RPM）、指数退避重试、熔断器
- **平台兼容**：自动检测平台能力，Record 组件不可用时降级为 File
- **多音色管理**：VoiceStore 支持全局/群/用户/情绪四级默认音色
- **Pages WebUI**：完整的音色管理 Web 界面

**优点**：
- 生态中最完整的工程实现，可靠性设计一流
- AI 语音导演是独特的 SubAgent 细化机制
- 四级音色默认值体系极其灵活
- 后台队列 + 熔断 + 持久化恢复，生产级可靠性

**缺点**：
- 单文件 64KB 过于庞大，可维护性差
- 仅支持 MiMo 单引擎
- 配置项极多，上手成本高

---

### 2.3 Zhalslar/astrbot_plugin_outputpro（v2.2.5）

**定位**：AstrBot 输出管道增强插件，TTS 是 13 个管道步骤之一

**架构**：
```
main.py (OutputPlugin - 管道入口)
├── core/config.py     (PluginConfig)
├── core/model.py      (OutContext, StateManager, StepName)
├── core/pipeline.py   (Pipeline - 步骤编排)
└── core/step/         (13 个步骤模块)
    ├── base.py        (BaseStep 抽象基类)
    ├── tts.py         (TTSStep - TTS 步骤)
    ├── split.py       (分段回复)
    ├── typo.py        (错字模拟)
    ├── clean.py       (文本清洗)
    ├── ... 等共 13 个步骤
```

**触发机制**：
- **管道步骤触发**：`TTSStep` 在 `Pipeline` 中按优先级执行
- **条件**：仅当消息链只含一个 Plain 且文本长度 < `threshold` 且 `random() < prob` 时触发
- **双重引擎**：
  1. 优先使用配置的 `TTSProvider`（AstrBot 框架内置 TTS 提供商）
  2. 降级使用 QQ 机器人 `get_ai_record()`（QQ 原生语音）
  3. 跨平台中转：通过 QQ 机器人生成语音，再转码适配目标平台（如 Telegram 转 ogg）

**情绪/语速控制**：无（仅基础文本转语音）

**TTS 引擎**：
- AstrBot 框架 `TTSProvider`（通过 `provider_id` 配置）
- QQ 原生 `get_ai_record(character, group_id, text)`
- 跨平台中转转码

**可扩展性**：管道架构本身高度可扩展，TTS 作为一个 Step 可被替换/禁用

**优点**：
- 管道架构设计优雅，13 个步骤可独立开关
- 跨平台语音中转是独特能力
- 与框架 TTSProvider 集成

**缺点**：
- TTS 功能较基础，无情绪控制
- 不支持自定义 TTS 引擎接入

---

### 2.4 miku05231/astrbot_plugin_translate_tts（v1.1.0）

**定位**：LLM 回复翻译 + 多引擎语音合成

**架构**：单文件（14KB），无模块拆分

**触发机制**：
- **`@filter.on_decorating_result()`**：拦截 LLM 回复，自动翻译 + TTS
- 跳过指令响应（以 `/` 开头的消息）
- 文本长度限制（`text_length_limit`），超长跳过

**情绪/语速控制**：无

**TTS 引擎**（六引擎支持，核心亮点）：
```python
providers = {
    "gpt_sovits": self._tts_gpt_sovits,   # GPT-SoVITS 本地 API
    "edge_tts": self._tts_edge_tts,        # Edge TTS（免费）
    "openai_tts": self._tts_openai,        # OpenAI TTS API
    "fish_audio": self._tts_fish_audio,   # Fish Audio API
    "azure_tts": self._tts_azure,           # Azure TTS（SSML）
    "qwen_tts": self._tts_qwen,             # Qwen3-TTS API
    "qwen_local": self._tts_qwen_local,   # Qwen3 本地
}
```
通过配置 `tts_provider` 选择引擎，每种引擎独立实现 `_tts_xxx()` 方法

**翻译机制**：
- 使用当前对话 LLM 进行翻译（`context.llm_generate()`）
- 支持自定义翻译提示词
- 输出模式：`dual_output`（文字+语音）、`voice_only`（仅语音）

**可扩展性**：Provider 字典模式，新增引擎只需添加一个方法 + 字典条目

**优点**：
- 六引擎支持是生态中最多的
- 翻译 + TTS 的组合场景实用
- 引擎切换简单（改配置即可）

**缺点**：
- 无情绪控制
- 无概率触发/冷却机制
- 单文件架构，无错误恢复
- Azure TTS 使用 SSML 但未暴露情绪控制

---

### 2.5 w2902171175/astrbot_plugin_GPT-SoVITS（v1.7.1）

**定位**：本地 GPT-SoVITS TTS 插件，单文件实现

**架构**：单文件（11KB），`GPTSoVITSTTSLocal` 类

**触发机制**：
- **`@filter.on_decorating_result()`**：概率触发（`prob`）+ 冷却机制（`cooldown`）
- 文本截断（`text_limit`）
- 会话状态管理（`_session_state`）

**情绪/语速控制**：
- 支持语速参数（`speed_facter`）
- 无情绪控制

**TTS 引擎**：单一 GPT-SoVITS（`/infer_classic` 接口），返回 `audio_url` 后下载

**可扩展性**：单引擎绑定

**优点**：
- 实现简单直接，适合快速部署
- 概率 + 冷却 + 截断三重门控

**缺点**：
- 无情绪控制
- 无模块化设计
- 无缓存机制
- 无 LLM Tool Call 支持

---

### 2.6 Dioxgen/AstrBot-LLM-Qwen3-TTS（v1.0.0）

**定位**：LLM 控制的 Qwen3-TTS 语音合成插件

**架构**：
```
main.py
├── TextSplitter         (智能文本分段器)
├── Qwen3TTSGradioClient (Gradio 端口调用客户端)
└── Qwen3TTSPlugin       (插件主类)
```

**触发机制**（双模式）：
1. **标记系统**：LLM 在回复中添加 `[TTS]` 标记，插件解析后触发 TTS
2. **概率控制**：可配置忽略标记，纯概率触发（`gradio_tts_probability`）
- 字数范围限制（`tts_min_length` ~ `tts_max_length`），过短/过长跳过

**情绪/语速控制**：无（仅基础音色文件传递）

**TTS 引擎**：单一 Qwen3-TTS（通过 Gradio Client 调用本地部署服务）

**可扩展性**：单引擎绑定

**工程亮点**：
- 线程池执行同步 Gradio 调用（`ThreadPoolExecutor`）
- 路径安全性校验（防止目录遍历攻击）
- 智能文本分段（按标点符号切分）
- 音频文件自动清理

**优点**：
- `[TTS]` 标记系统让 LLM 自主决策何时发语音
- 双模式（标记/概率）灵活切换
- 安全性考虑周到（路径校验）

**缺点**：
- 无情绪控制
- Gradio 同步调用可能阻塞
- 无缓存机制

---

### 2.7 Thyran1/astrbot_plugin_qwen3_tts（v1.0.0）

**定位**：Qwen3-TTS + 高级消息分段回复插件

**架构**：单文件（28KB），功能丰富

**触发机制**：
- **`@filter.on_decorating_result(priority=-100000000000000000)`**：最低优先级（最后执行）
- 双 TTS 模式：
  1. Gradio TTS（本地 Qwen3-TTS）+ 概率控制
  2. 框架 TTS（AstrBot 内置 `TTSProvider`）+ 概率控制
- 字数范围限制

**情绪/语速控制**：无

**TTS 引擎**：双引擎（Gradio Qwen3-TTS + 框架 TTSProvider）

**核心亮点 - 消息分段系统**：
- 支持标点符号切分（强制 + 概率切分）
- 括号/引号平衡算法（不在引号内切分）
- 分段延迟策略（随机/按字数/固定）
- 最大分段数限制
- 分段间逐条发送 + 延迟

**可扩展性**：双引擎但不可动态切换，分段系统可独立使用

**优点**：
- 消息分段系统极其精细，支持概率切分和括号平衡
- 双 TTS 引擎（Gradio + 框架）
- 分段延迟策略多样化

**缺点**：
- 代码复杂度高，单文件 28KB
- 无情绪控制
- 无 LLM Tool Call 支持

---

### 2.8 muyouzhi6/astrbot_plugin_tts_emotion_router（v3.2.3）

**定位**：情绪路由型 TTS 插件，支持 SiliconFlow/MiniMax/MiMo 三引擎，18 种中文情绪

**架构**：
```
main.py (TTSEmotionRouter - 61KB, 生态中最大)
├── core/
│   ├── config.py          (ConfigManager - 28KB 配置管理)
│   ├── constants.py       (EMOTIONS, EMOTION_KEYWORDS, MIMO 标签映射等)
│   ├── marker.py           (EmotionMarkerProcessor - 情绪标记系统)
│   ├── tts_processor.py    (TTSProcessor - 核心合成逻辑)
│   ├── segmented_tts.py    (SegmentedTTSProcessor - 分段 TTS)
│   ├── text_splitter.py    (TextSplitter)
│   ├── session.py          (SessionState - 会话状态管理)
│   ├── hooks.py            (LLM 钩子)
│   └── compat.py           (跨版本兼容层)
├── emotion/classifier.py  (HeuristicClassifier - 启发式情绪分类)
├── tts/
│   ├── provider_siliconflow.py (SiliconFlowTTS)
│   ├── provider_minimax.py      (MiniMaxTTS)
│   └── provider_mimo.py         (MiMoTTS)
└── utils/
    ├── audio.py
    ├── extract.py         (CodeAndLinkExtractor)
    └── text_sanitizer.py  (SpeechTextSanitizer)
```

**触发机制**（四重）：
1. **`@filter.on_decorating_result(priority=-1000)`**：自动 TTS，概率 + 长度 + 冷却 + 混合内容检查
2. **`@filter.command("tts_say")`**：手动指令触发
3. **`@filter.llm_tool(name="tts_speak")`**：LLM Tool Call
4. **`@filter.on_llm_request()`**：在 LLM 请求前注入情绪标记提示词
5. **`@filter.on_llm_response(priority=1)`**：在 LLM 响应后解析情绪标记

**情绪/语速控制**（生态中最丰富）：
- **18 种中文情绪**：`EMOTIONS` 常量定义完整情绪列表
- **情绪标记系统**：`EmotionMarkerProcessor` 支持 LLM 在回复头部添加情绪标签（如 `[开心]文本...`），自动剥离
- **启发式分类器**：`HeuristicClassifier` 通过关键词匹配自动判别情绪
- **情绪路由**：不同情绪映射不同音色（`voice_map`）和语速（`speed_map`）
- **MiniMax 表达标签**：支持 `(laughs)`、`(sighs)` 等语气词标签，注入到 system_prompt 指导 LLM
- **MiMo 风格指令**：支持 `overall_tone`、`timbre_positioning`、`persona_accent`、`dialect`、`role_play` 等参数
- **MiMo 语音导演**：`director_enable`、`director_role`、`director_scene`、`director_instruction`、`director_context` 配置项
- **临时语音指令**：从用户消息中提取情绪/风格/音色/导演指令（如"用冰糖的音色说"、"语音导演：用悲伤的语气说"）
- **停顿标记**：`<#x#>` 控制停顿秒数
- **性能标签**：MiMo 的 `performance_tags`（如叹气、哽咽、轻笑）

**TTS 引擎**（三引擎 Provider 模式）：
```python
if provider == "minimax":    return MiniMaxTTS(...)
if provider == "mimo":       return MiMoTTS(...)
return SiliconFlowTTS(...)   # 默认
```
每个 Provider 独立实现，配置签名监控自动重建客户端

**可扩展性**：Provider 模式，添加新引擎只需新建 Provider 类 + 在 `_create_tts_client()` 中注册

**工程亮点**：
- **会话状态管理**：SessionState 追踪最近语音文本、pending 情绪/风格/音色/导演指令
- **语音上下文注入**：将最近语音文本注入 LLM 上下文（`_inject_recent_spoken_assistant_context`）
- **分段 TTS**：SegmentedTTSProcessor 支持分段合成 + 间隔控制
- **Voice-Only 模式**：发送语音后抑制下一条 LLM 纯文本回复
- **会话黑白名单**：支持全局开关 + UMO 级别白名单/黑名单
- **去重签名**：`_build_inflight_sig()` 防止同一文本重复合成
- **后台清理**：定时清理临时音频文件和过期会话
- **历史记录**：语音发送后将文本写入对话历史

**优点**：
- 生态中功能最丰富的 TTS 插件
- 三引擎 Provider 模式可扩展
- 18 种情绪 + 标记系统 + 启发式分类的多层情绪控制
- MiMo 语音导演是完整的 SubAgent 细化机制
- 会话管理、上下文注入、历史记录一体化

**缺点**：
- 单文件 61KB，可维护性差
- 配置项极多（ConfigManager 28KB）
- MiMo 特有功能与通用逻辑耦合

---

### 2.9 sch-chun/astrbot_plugin_qwen_audio_3.0（主人自己的插件）

**定位**：基于阿里云百炼 API 的 Qwen Audio 3.0 TTS 插件

**架构**：单文件（8.6KB），简洁清晰

**触发机制**：
- **`<tts>...</tts>` 标记系统**：LLM 在回复中使用 `<tts>` 标签包裹需要语音合成的内容
- **`@on_llm_request()`**：在 LLM 请求前注入 `tts_prompt` 提示词，指导 LLM 使用 `<tts>` 标签
- **`@on_decorating_result(priority=13)`**：解析回复中的 `<tts>` 标签，将标签内文本合成语音，非标签文本保留为纯文本
- **分段处理**：`_split_by_tts_tags()` 将文本拆分为 `text` 段和 `tts` 段，逐段处理

**情绪/语速控制**：
- 支持 `instruction` 参数（Qwen Audio 3.0 的风格指令）
- 支持 `voice` 参数切换音色
- 支持 `sample_rate` 配置

**TTS 引擎**：单一 Qwen Audio 3.0（阿里云百炼 API，非实时语音合成）

**可扩展性**：单引擎绑定

**优点**：
- `<tts>` 标记系统设计简洁优雅，LLM 可精确控制哪些内容需要语音
- `$` 边界分隔符处理，避免标记残留
- 单文件架构清晰，易于理解和维护
- 与 LLM 的协作模式自然（通过 prompt 引导 + 标签解析）

**缺点**：
- 无情绪路由
- 无概率触发
- 无 LLM Tool Call
- 无多引擎支持
- 无缓存机制
- 无后台异步处理

---

### 2.10 clown145/astrbot_plugin_tts_llm（v1.3.7）

**定位**：LLM 驱动的情感 TTS 插件，支持情感注入、翻译、多角色管理

**架构**：
```
main.py (LlmTtsPlugin - 30KB)
├── emotion_manager.py  (EmotionManager - 角色/情感管理)
├── tts_engine.py       (TTSEngine - TTS 合成引擎)
└── external_apis.py    (translate_text - 翻译 API)
```

**触发机制**：
- **`@filter.on_llm_request()`**：注入情感提示词到 system_prompt，引导 LLM 输出 `[emotion=xxx]` 标签
- **`@filter.on_llm_response()`**：解析 LLM 回复中的 `[emotion=xxx]` 标签和 `$翻译$` 内容
- **指令触发**：`/tts-llm`（开启）、`/tts-w`（自动情感识别）、`/合成 角色名 情感名 文本`
- **群组级开关**：`/ttg`（开启群语音）、白名单/黑名单

**情绪/语速控制**（LLM 驱动型）：
- **LLM 情感注入**：在 system_prompt 中注入可用情感列表，LLM 自主选择情感并输出 `[emotion=xxx]` 标签
- **自动情感识别模式**（w 模式）：LLM 同时完成翻译 + 情感识别，输出 `翻译文本[情感名]` 格式
- **角色-情感注册系统**：用户通过 `/注册感情` 指令注册角色和情感，每个情感对应不同的参考音频
- **情感切换**：`/sw 角色名 情感名` 切换当前会话情感
- **HuggingFace Space 保活**：定时 ping 防止 TTS 服务休眠

**TTS 引擎**：通过 `TTSEngine` 封装（具体引擎在 tts_engine.py 中，推测为 GPT-SoVITS 或类似）

**可扩展性**：中等，角色/情感管理模块化，但 TTS 引擎单绑定

**优点**：
- LLM 驱动的情感选择是创新的 SubAgent 模式
- 角色-情感注册系统灵活
- 群组级开关 + 白名单/黑名单
- Space 保活机制实用

**缺点**：
- `[emotion=xxx]` 标签可能被 LLM 误用
- 翻译 + 情感识别耦合，流程复杂
- 无缓存机制
- 无后台异步处理

---

### 2.11 victical/astrbot_plugin_genie-tts（v1.0.0）

**定位**：基于 Genie TTS 的语音合成插件，支持模型加载/卸载和音频后处理

**架构**：单文件（25KB），`GenieTTSPlugin` 类

**触发机制**：
- **`@filter.on_decorating_result()`**：自动触发
- 概率门控（`prob`）+ 长度限制（`text_limit`）+ 冷却机制（`cooldown`）
- 会话级开关：全局启用/白名单模式 + 会话级启用/禁用
- 仅处理 LLM 响应

**情绪/语速控制**：无

**TTS 引擎**：单一 Genie TTS（本地 HTTP API，`/load_character`、`/set_reference_audio`、`/tts`、`/unload_character`）

**工程亮点**：
- **模型生命周期管理**：自动加载/卸载模型，模型未加载时自动重新初始化
- **音频静音裁剪**：使用 pydub 检测并裁剪音频首尾静音
- **重试机制**：音频生成失败自动重试（`retry_attempts`）
- **LLM 翻译**：可选将 TTS 文本翻译为中文后随语音一起发送

**可扩展性**：单引擎绑定

**优点**：
- 模型生命周期管理完善
- 音频后处理（静音裁剪）是独特能力
- 会话级开关灵活

**缺点**：
- 无情绪控制
- 无 LLM Tool Call
- 无缓存机制
- 同步 HTTP 调用（`requests` 库）

---

## 三、对比分析表格

### 3.1 核心能力对比

| 插件 | 触发机制 | TTS 引擎 | 情绪控制 | 可扩展性 | 代码架构 |
|------|----------|----------|----------|----------|----------|
| **Zhalslar/GPT_SoVITS** | 概率+指令+Tool Call | GPT-SoVITS | LLM判别+关键词匹配+条目系统 | 单引擎 | 模块化(6文件) |
| **Justice-ocr/MiMo** | 概率+指令+Tool Call+后台队列 | MiMo | 情绪路由+AI导演+风格标签 | 单引擎(对外暴露API) | 模块化(12+文件) |
| **Zhalslar/outputpro** | 管道步骤+概率 | 框架TTSProvider+QQ原生 | 无 | 管道可扩展 | 模块化(13步骤) |
| **miku05231/translate_tts** | 自动拦截 | GPT-SoVITS/Edge/OpenAI/Fish/Azure/Qwen | 无 | **六引擎Provider字典** | 单文件 |
| **w2902171175/GPT-SoVITS** | 概率+冷却 | GPT-SoVITS | 无 | 单引擎 | 单文件 |
| **Dioxgen/Qwen3-TTS** | **[TTS]标记+概率** | Qwen3-TTS(Gradio) | 无 | 单引擎 | 三模块 |
| **Thyran1/qwen3_tts** | 自动+概率 | Qwen3-TTS+框架TTS | 无 | 双引擎 | 单文件 |
| **muyouzhi6/emotion_router** | 概率+指令+Tool Call+LLM钩子 | **SiliconFlow/MiniMax/MiMo** | **18种情绪+标记+启发式+导演** | **三引擎Provider模式** | 模块化(15+文件) |
| **sch-chun/qwen_audio** | **`<tts>`标记系统** | Qwen Audio 3.0 | instruction参数 | 单引擎 | 单文件 |
| **clown145/tts_llm** | LLM注入+指令 | TTS(封装) | **LLM情感注入+角色注册** | 中等 | 四模块 |
| **victical/genie_tts** | 概率+冷却+会话开关 | Genie TTS | 无 | 单引擎 | 单文件 |

### 3.2 触发机制对比

| 触发类型 | 插件 | 实现方式 |
|----------|------|----------|
| **概率触发** | Zhalslar/GPT_SoVITS, w2902171175, Justice-ocr, muyouzhi6, victical | `random.random() > prob` 跳过 |
| **指令触发** | Zhalslar/GPT_SoVITS, Justice-ocr, clown145, victical | `@filter.command()` |
| **LLM Tool Call** | Zhalslar/GPT_SoVITS, Justice-ocr, muyouzhi6 | `@filter.llm_tool()` |
| **标记系统-[TTS]** | Dioxgen | 正则匹配 `[TTS]` 标记 |
| **标记系统-`<tts>`** | sch-chun | 正则匹配 `<tts>...</tts>` |
| **标记系统-[emotion=]** | clown145 | 正则匹配 `[emotion=xxx]` |
| **情绪头部标记** | muyouzhi6 | `[开心]文本...` 头部标签 |
| **LLM 请求注入** | clown145, muyouzhi6, sch-chun | `@filter.on_llm_request()` 注入提示词 |
| **后台队列** | Justice-ocr | TTSJobManager + 持久化 |
| **管道步骤** | Zhalslar/outputpro | Pipeline + Step 模式 |

### 3.3 情绪/语速控制对比

| 控制方式 | 插件 | 详细说明 |
|----------|------|----------|
| **LLM 情感判别** | Zhalslar/GPT_SoVITS | 调用 LLM 返回 JSON `{"emotion":"开心"}`，缓存结果 |
| **关键词匹配** | Zhalslar/GPT_SoVITS, muyouzhi6 | EntryManager/HeuristicClassifier 关键词→情绪映射 |
| **情绪标记系统** | muyouzhi6 | LLM 在回复头部添加 `[开心]`，自动剥离 |
| **LLM 情感注入** | clown145 | system_prompt 注入情感列表，LLM 输出 `[emotion=xxx]` |
| **情绪路由** | Justice-ocr, muyouzhi6 | 情绪→音色+语速映射表 |
| **AI 语音导演** | Justice-ocr | 二次 LLM 调用生成风格指令（SubAgent） |
| **MiMo 语音导演** | muyouzhi6 | director_role/scene/instruction/context 配置 |
| **MiniMax 表达标签** | muyouzhi6 | `(laughs)` `(sighs)` 等语气词标签 |
| **停顿标记** | muyouzhi6 | `<#x#>` 控制停顿秒数 |
| **语速控制** | Zhalslar/GPT_SoVITS, muyouzhi6, w2902171175 | speed_factor/speed_map 参数 |
| **instruction 参数** | sch-chun | Qwen Audio 3.0 风格指令 |

### 3.4 SubAgent 细化能力对比

| 插件 | SubAgent 机制 | 实现方式 |
|------|---------------|----------|
| **Justice-ocr/MiMo** | ✅ AI 语音导演 | `generate_style_plan()` 调用 LLM 生成 style_context + 优化朗读文本，10分钟 LRU 缓存 |
| **muyouzhi6/emotion_router** | ✅ MiMo 语音导演 | director_enable + director_role/scene/instruction/context，注入到 MiMo API |
| **clown145/tts_llm** | ✅ LLM 情感+翻译 | LLM 同时完成翻译 + 情感识别，输出 `翻译文本[情感名]` |
| **Zhalslar/GPT_SoVITS** | ✅ LLM 情感判别 | `EmotionJudger` 调用 LLM 分析情感，结果缓存 |
| **muyouzhi6/emotion_router** | ✅ 临时语音指令 | 从用户消息中提取情绪/风格/音色/导演指令 |
| 其他 | ❌ 无 | — |

---

## 四、对主人 TTS 插件的设计建议

基于以上 11 个插件的源码分析，针对 `sch-chun/astrbot_plugin_qwen_audio_3.0` 提出以下设计建议：

### 4.1 保留现有优势

当前 `<tts>...</tts>` 标记系统设计简洁优雅，应保留为核心触发机制。这种方式的优点是 LLM 可精确控制哪些内容需要语音合成，而非全量或概率触发。

### 4.2 建议增强的方向

#### 4.2.1 多触发机制融合（参考 Zhalslar/GPT_SoVITS）

```
当前：<tts> 标记系统
建议：<tts> 标记 + 概率触发 + LLM Tool Call + 指令触发
```

- 保留 `<tts>` 标记作为主触发机制
- 增加 `@filter.llm_tool(name="qwen_tts_speak")` 让 LLM 可主动调用
- 增加 `@filter.command("说")` 指令触发
- 增加可选的概率触发模式（`enable_probability_control`），参考 Dioxgen 的双模式设计

#### 4.2.2 情绪控制体系（参考 muyouzhi6 + Zhalslar/GPT_SoVITS）

```
当前：仅 instruction 参数
建议：三层情绪控制体系
```

1. **LLM 情绪标记**：在 `<tts emotion="happy">...</tts>` 标签中增加 `emotion` 属性
2. **LLM 情感判别**：可选调用 LLM 分析文本情感（参考 `EmotionJudger`），将结果映射为 `instruction` 参数
3. **关键词匹配降级**：LLM 判别失败时通过关键词匹配（参考 `EntryManager`）

#### 4.2.3 模块化架构（参考 Zhalslar/GPT_SoVITS + muyouzhi6）

```
当前：单文件 8.6KB
建议：模块化拆分
```

```
astrbot_plugin_qwen_audio_3.0/
├── main.py                  # 插件入口
├── core/
│   ├── config.py            # 配置管理
│   ├── client.py            # Qwen Audio API 客户端
│   ├── tts_parser.py        # <tts> 标签解析器
│   ├── emotion.py           # 情绪判别（可选）
│   └── cache.py             # 音频缓存
└── _conf_schema.json        # 配置 schema
```

#### 4.2.4 音频缓存机制（参考 Zhalslar/GPT_SoVITS）

GPT-SoVITS 插件的 `LocalDataManager` 实现了基于参数哈希的音频缓存，避免相同文本重复合成。建议：
- 对 `text + voice + instruction` 参数组合做哈希
- 缓存音频文件到 `data_dir/audio/`
- 设置过期时间（如 24 小时）

#### 4.2.5 文本预处理（参考 muyouzhi6 + Justice-ocr）

- **文本清洗**：移除颜文字、特殊符号、代码块、链接（参考 `SpeechTextSanitizer`）
- **智能分段**：长文本按标点符号分段合成后合并（参考 `TextSplitter` + `merge_wav_files`）
- **字数限制**：最小/最大字数范围检查

#### 4.2.6 后台异步处理（参考 Justice-ocr）

当前 `<tts>` 标签解析在 `on_decorating_result` 中同步执行，长文本合成会阻塞消息发送。建议：
- 文本先发送，语音后台合成后补发
- 使用 `event.send()` + `after_message_sent` 钩子

#### 4.2.7 会话级开关（参考 muyouzhi6 + victical）

- 全局开关 + 会话级白名单/黑名单
- `/tts_on` `/tts_off` 指令
- 群聊/私聊独立控制

### 4.3 最佳实践综合推荐

| 维度 | 最佳实践来源 | 推荐方案 |
|------|-------------|----------|
| 触发机制 | sch-chun + Dioxgen + Zhalslar | `<tts>` 标记 + LLM Tool Call + 指令触发 |
| 情绪控制 | muyouzhi6 + Zhalslar | 标签属性 `emotion` + LLM 判别 + 关键词降级 |
| 架构设计 | Zhalslar/GPT_SoVITS | 模块化 + ConfigNode 强类型配置 |
| 缓存机制 | Zhalslar/GPT_SoVITS | 参数哈希 → 文件缓存 |
| 文本处理 | muyouzhi6 | 清洗 + 分段 + 字数范围 |
| 可靠性 | Justice-ocr | 后台队列 + 重试 + 熔断 |
| 多引擎 | miku05231 + muyouzhi6 | Provider 字典/接口模式 |
| 会话管理 | muyouzhi6 + victical | 全局开关 + 会话级白名单 |
| 音频后处理 | victical | 静音裁剪 + 格式转换 |

### 4.4 推荐的优先级排序

1. **高优先级**：模块化拆分 + 音频缓存 + 文本预处理（基础工程能力）
2. **中优先级**：情绪控制体系 + 会话级开关（用户体验提升）
3. **低优先级**：后台异步处理 + 多引擎支持 + AI 语音导演（高级功能）

---

## 五、生态总结

### 5.1 生态成熟度

AstrBot TTS 插件生态已从 2025 年初的"单引擎对接"发展到 2026 年中期的"情绪路由 + AI 导演 + 后台队列"的复杂架构。生态中出现了三种典型的设计范式：

1. **简单对接型**（w2902171175, victical）：单文件 + 概率触发 + 单引擎
2. **标记系统型**（sch-chun, Dioxgen, clown145）：LLM 标记 + 解析 + 合成
3. **综合平台型**（Justice-ocr, muyouzhi6）：多引擎 + 情绪路由 + AI 导演 + 后台队列

### 5.2 技术趋势

1. **LLM 驱动决策**：从概率触发 → 标记系统 → LLM Tool Call，让 LLM 自主决策何时发语音
2. **情绪控制深化**：从无 → 关键词匹配 → LLM 判别 → 情绪标记 → AI 语音导演
3. **多引擎支持**：从单引擎 → Provider 字典 → Provider 接口模式
4. **工程可靠性**：从同步调用 → 后台队列 → 熔断器 → 持久化恢复
5. **SubAgent 细化**：AI 语音导演是最新趋势，通过二次 LLM 调用细化语音参数

### 5.3 生态短板

1. **缺乏统一标准**：各插件触发机制、配置格式、API 设计各异，无统一规范
2. **单文件膨胀**：最复杂的插件单文件 61KB，可维护性差
3. **测试缺失**：几乎无插件包含单元测试
4. **文档不足**：多数插件仅有 README，无架构文档
5. **跨插件协作**：缺乏插件间 TTS 服务复用的标准接口（仅 Justice-ocr 对外暴露了方法）

---

*报告完*
