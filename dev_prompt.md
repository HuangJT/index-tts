# https://deepwiki.com/search/webui_a655da27-b547-4229-9a87-ff6a90d0cffc
# 部署成服务器
你询问的是如何在IndexTTS中设置参考音频文件存储位置，并通过HTTP API调用进行语音合成。

## 参考音频文件存储位置

根据IndexTTS的代码实现，你应该将参考音频文件存放在 `prompts` 目录下： [1](#9-0) 

Web界面会自动创建这个目录，并从中读取音频文件： [2](#9-1) 

## 具体操作步骤

### 1. 创建音频存储目录并放置文件
```bash
# 在IndexTTS项目根目录下创建prompts目录（如果不存在）
mkdir -p prompts

# 将你的音频文件复制到prompts目录
cp "和小美清楚主播.mp3" prompts/
cp "陈心心大气主播.mp3" prompts/
cp "TVB女声.mp3" prompts/
```

### 2. 启动Web服务
```bash
python webui.py --host 0.0.0.0 --port 7860
``` [3](#9-2) 

### 3. HTTP API调用方式

IndexTTS的Web界面使用Gradio框架，支持HTTP API调用。你可以通过以下方式调用：

```python
import requests
import json

# API端点
url = "http://your-server:7860/api/predict"

# 调用参数
data = {
    "data": [
        "prompts/和小美清楚主播.mp3",  # 参考音频文件路径
        "你好，这是测试文本",           # 要合成的文本
        "批次推理",                    # 推理模式
        120,                          # 分句最大Token数
        4,                           # 分句分桶最大容量
        True,                        # do_sample
        0.8,                         # top_p
        30,                          # top_k
        1.0,                         # temperature
        0.0,                         # length_penalty
        3,                           # num_beams
        10.0,                        # repetition_penalty
        600                          # max_mel_tokens
    ],
    "fn_index": 0  # 对应gen_single函数
}

response = requests.post(url, json=data)
result = response.json()
```

## 关于音调、音速、音量控制

**重要说明**：根据当前的IndexTTS代码实现，系统**不直接支持**音调、音速、音量的独立控制参数。 [4](#9-3) [5](#9-4) 

当前支持的参数主要是GPT生成相关的参数：
- `temperature`: 控制生成的随机性
- `top_p`, `top_k`: 采样参数
- `repetition_penalty`: 重复惩罚
- `max_mel_tokens`: 最大生成长度

## 替代方案

如果需要音调、音速、音量控制，你可能需要：

1. **后处理方式**：使用音频处理库（如librosa、pydub）对生成的音频进行后处理
2. **修改源码**：在BigVGAN vocoder部分添加相关控制参数

## Python API直接调用

你也可以直接使用Python API而不是HTTP接口：

```python
from indextts.infer import IndexTTS

tts = IndexTTS(model_dir="checkpoints", cfg_path="checkpoints/config.yaml")

# 直接使用文件名（相对于项目根目录）
tts.infer(
    audio_prompt="prompts/和小美清楚主播.mp3",
    text="你好，这是测试文本",
    output_path="output.wav"
)
``` [6](#9-5) 

## Notes

IndexTTS的设计重点是零样本语音克隆，通过参考音频自动学习音色特征。如果需要更精细的音频控制（音调、音速、音量），建议在生成后使用专门的音频处理工具进行调整。

Wiki pages you might want to explore:
- [Installation and Setup (index-tts/index-tts)](/wiki/index-tts/index-tts#2)
- [Python API (index-tts/index-tts)](/wiki/index-tts/index-tts#3.3)


# 改造支持传入音色id进行复刻
你询问的是IndexTTS类中音频缓存的存储位置和格式。让我详细解释一下缓存机制的实现。

## 缓存存储位置

IndexTTS的音频缓存**不是存储在本地文件系统中**，而是直接存储在**内存中**作为类的实例变量。 [1](#3-0) 

具体来说，缓存包含两个变量：
- `self.cache_audio_prompt`: 存储音频文件路径的字符串
- `self.cache_cond_mel`: 存储处理后的mel频谱图张量

## 缓存内容格式

缓存的内容是经过处理的**mel频谱图张量**，而不是原始音频文件。处理过程包括：

1. 加载音频文件并转换为单声道
2. 重采样到24kHz
3. 提取mel频谱特征
4. 转换为PyTorch张量并移动到指定设备 [2](#3-1) 

## 缓存生命周期

这个缓存是**临时的内存缓存**，具有以下特点：

- **会话级别**：只在IndexTTS实例存在期间有效
- **单一音频**：同时只能缓存一个音频文件的特征
- **自动更新**：当传入不同的`audio_prompt`路径时会自动替换缓存 [3](#3-2) 

## 技术限制

由于缓存设计的限制：
- 程序重启后缓存会丢失
- 无法同时管理多个音色的缓存
- 缓存基于文件路径字符串匹配，移动文件会导致缓存失效

这种设计主要是为了在同一会话中使用相同音色进行多次合成时提高性能，避免重复的音频预处理计算。

## Notes

如果需要持久化缓存或多音色管理功能，需要对IndexTTS类进行重构，添加文件系统缓存或数据库存储机制。当前的内存缓存设计适合单次会话中的批量合成场景。

Wiki pages you might want to explore:
- [System Architecture (index-tts/index-tts)](/wiki/index-tts/index-tts#1.2)
- [GPT-based Acoustic Model (index-tts/index-tts)](/wiki/index-tts/index-tts#4.3)