# IndexTTS HTTP API 文档

## 概述

IndexTTS HTTP API 提供了完整的文本转语音服务，支持参考音频上传、语音合成以及音频参数控制（音调、语速、音量）。

## 服务启动

### 方式1：仅启动API服务
```bash
python api_server.py --host 0.0.0.0 --port 8000
```

### 方式2：同时启动API和Web界面
```bash
python start_services.py --mode both
```

### 方式3：使用不同端口
```bash
python start_services.py --api-port 8001 --webui-port 7861
```

## API 接口

### 基础信息

- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`
- **响应格式**: JSON

### 1. 健康检查

**GET** `/health`

检查API服务器状态和模型加载情况。

**响应示例**:
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

### 2. 列出参考音频

**GET** `/reference_audios`

获取所有可用的参考音频文件列表。

**响应示例**:
```json
{
  "reference_audios": [
    {
      "filename": "和小美清楚主播.mp3",
      "size": 1024000,
      "modified": 1640995200.0
    },
    {
      "filename": "陈心心大气主播.mp3",
      "size": 2048000,
      "modified": 1640995300.0
    }
  ]
}
```

### 3. 上传参考音频

**POST** `/upload_reference_audio`

上传新的参考音频文件。

**请求参数**:
- `file`: 音频文件 (multipart/form-data)

**支持格式**: MP3, WAV, FLAC, M4A

**响应示例**:
```json
{
  "message": "参考音频 TVB女声.mp3 上传成功",
  "filename": "TVB女声.mp3"
}
```

### 4. 语音合成 (核心接口)

**POST** `/synthesize`

使用参考音频合成语音，支持音调、语速、音量控制。

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `text` | string | ✅ | - | 要合成的文本 |
| `reference_audio` | string | ✅ | - | 参考音频文件名 |
| `output_format` | string | ❌ | "mp3" | 输出音频格式("mp3"或"wav") |
| `pitch_shift` | float | ❌ | 0.0 | 音调调整(半音，-12到12) |
| `speed_rate` | float | ❌ | 1.0 | 语速倍率(0.5到2.0) |
| `volume_gain` | float | ❌ | 0.0 | 音量增益(dB，-20到20) |
| `infer_mode` | string | ❌ | "fast" | 推理模式("normal"或"fast") |
| `do_sample` | boolean | ❌ | true | 是否使用采样 |
| `top_p` | float | ❌ | 0.8 | Top-p采样参数 |
| `top_k` | integer | ❌ | 30 | Top-k采样参数 |
| `temperature` | float | ❌ | 1.0 | 温度参数 |
| `repetition_penalty` | float | ❌ | 10.0 | 重复惩罚 |
| `max_mel_tokens` | integer | ❌ | 600 | 最大mel token数 |

**请求示例**:
```json
{
  "text": "大家好，我现在正在测试IndexTTS的API接口功能。",
  "reference_audio": "和小美清楚主播.mp3",
  "output_format": "mp3",
  "pitch_shift": 2.0,
  "speed_rate": 1.2,
  "volume_gain": 3.0,
  "infer_mode": "fast"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "语音合成成功",
  "audio_url": "/audio/tts_1640995400000.wav",
  "duration": 5.2,
  "processing_time": 3.8
}
```

### 5. 获取音频文件

**GET** `/audio/{filename}`

下载生成的音频文件。

**响应**: 音频文件流 (audio/wav)

### 6. 删除音频文件

**DELETE** `/audio/{filename}`

删除指定的音频文件。

**响应示例**:
```json
{
  "message": "音频文件 tts_1640995400000.wav 删除成功"
}
```

## 使用示例

### Python 示例

```python
import requests

# 1. 上传参考音频
with open("reference.wav", "rb") as f:
    files = {"file": ("reference.wav", f, "audio/wav")}
    response = requests.post("http://localhost:8000/upload_reference_audio", files=files)

# 2. 合成语音 (MP3格式)
data = {
    "text": "你好，这是一个测试。",
    "reference_audio": "reference.wav",
    "output_format": "mp3", # 输出MP3格式
    "pitch_shift": 1.0,    # 提高1个半音
    "speed_rate": 1.1,     # 语速加快10%
    "volume_gain": 2.0     # 音量增加2dB
}
response = requests.post("http://localhost:8000/synthesize", json=data)
result = response.json()

# 3. 下载音频
if result["success"]:
    audio_response = requests.get(f"http://localhost:8000{result['audio_url']}")
    with open("output.wav", "wb") as f:
        f.write(audio_response.content)
```

### cURL 示例

```bash
# 上传参考音频
curl -X POST "http://localhost:8000/upload_reference_audio" \
  -F "file=@reference.wav"

# 合成语音 (MP3格式)
curl -X POST "http://localhost:8000/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，这是一个测试。",
    "reference_audio": "reference.wav",
    "output_format": "mp3",
    "pitch_shift": 1.0,
    "speed_rate": 1.1,
    "volume_gain": 2.0
  }'

# 下载音频
curl -O "http://localhost:8000/audio/tts_1640995400000.wav"
```

## 目录结构

```
project/
├── reference_audios/          # 参考音频存储目录
│   ├── 和小美清楚主播.mp3
│   ├── 陈心心大气主播.mp3
│   └── TVB女声.mp3
├── outputs/api/               # API生成的音频文件
├── api_server.py             # API服务器
├── start_services.py         # 服务启动脚本
├── api_example.py            # 使用示例
└── webui.py                  # 原有的Gradio界面
```

## 音频参数说明

### 输出格式 (output_format)
- **MP3格式** (默认)
  - 文件更小，适合网络传输
  - 压缩格式，轻微质量损失
  - 比特率：192kbps
  - 兼容性好，支持所有主流播放器

- **WAV格式**
  - 无损音质，文件较大
  - 适合高质量音频需求
  - 采样率：24kHz
  - 适合后期处理

### 音调调整 (pitch_shift)
- 单位：半音 (semitone)
- 范围：-12.0 到 12.0
- 正值：提高音调
- 负值：降低音调
- 示例：2.0 表示提高2个半音

### 语速调整 (speed_rate)
- 单位：倍率
- 范围：0.5 到 2.0
- 1.0：正常语速
- >1.0：加快语速
- <1.0：放慢语速
- 示例：1.2 表示语速加快20%

### 音量调整 (volume_gain)
- 单位：分贝 (dB)
- 范围：-20.0 到 20.0
- 正值：增加音量
- 负值：降低音量
- 示例：3.0 表示音量增加3分贝

## 推理模式

### Fast模式 (推荐)
- 适合长文本
- 速度快，内存占用优化
- 质量略有损失但可接受

### Normal模式
- 适合短文本
- 质量最佳
- 速度较慢

## 错误处理

API使用标准HTTP状态码：

- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

错误响应格式：
```json
{
  "detail": "错误描述信息"
}
```

## 性能优化建议

1. **参考音频缓存**: 相同参考音频会被自动缓存，提高后续合成速度
2. **批量处理**: 对于大量文本，建议分批处理
3. **参数调优**: 根据需求调整`max_mel_tokens`等参数
4. **硬件要求**: 建议使用GPU加速，CPU模式较慢

## 注意事项

1. 参考音频质量直接影响合成效果
2. 音频参数调整可能影响合成质量
3. 长文本建议使用fast模式
4. 定期清理生成的音频文件以节省存储空间