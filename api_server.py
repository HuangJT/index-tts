#!/usr/bin/env python3
"""
IndexTTS HTTP API Server
支持通过HTTP API调用TTS服务，包含音调、音速、音量控制
"""

import os
import sys
import time
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "indextts"))

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import torchaudio
import torch
from pydub import AudioSegment
from pydub.effects import speedup

from indextts.infer import IndexTTS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="IndexTTS API Server",
    description="IndexTTS HTTP API服务，支持参考音频合成和音频参数控制",
    version="1.0.0"
)

# 全局变量
tts_model: Optional[IndexTTS] = None
REFERENCE_AUDIO_DIR = "reference_audios"
OUTPUT_DIR = "outputs/api"

# 创建必要的目录
os.makedirs(REFERENCE_AUDIO_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("prompts", exist_ok=True)

class TTSRequest(BaseModel):
    """TTS请求模型"""
    text: str = Field(..., description="要合成的文本")
    reference_audio: str = Field(..., description="参考音频文件名（不含路径）")
    output_format: str = Field(default="mp3", description="输出音频格式：mp3或wav")
    pitch_shift: float = Field(default=0.0, description="音调调整（半音，范围-12到12）")
    speed_rate: float = Field(default=1.0, description="语速倍率（范围0.5到2.0）")
    volume_gain: float = Field(default=0.0, description="音量增益（dB，范围-20到20）")
    infer_mode: str = Field(default="fast", description="推理模式：normal或fast")
    # GPT生成参数
    do_sample: bool = Field(default=True, description="是否使用采样")
    top_p: float = Field(default=0.8, description="Top-p采样参数")
    top_k: int = Field(default=30, description="Top-k采样参数")
    temperature: float = Field(default=1.0, description="温度参数")
    repetition_penalty: float = Field(default=10.0, description="重复惩罚")
    max_mel_tokens: int = Field(default=600, description="最大mel token数")

class TTSResponse(BaseModel):
    """TTS响应模型"""
    success: bool
    message: str
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    processing_time: Optional[float] = None

def init_tts_model():
    """初始化TTS模型"""
    global tts_model
    try:
        model_dir = "checkpoints"
        config_path = "checkpoints/config.yaml"
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        logger.info("正在加载IndexTTS模型...")
        tts_model = IndexTTS(
            model_dir=model_dir,
            cfg_path=config_path
        )
        logger.info("IndexTTS模型加载完成")
        
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        raise

def apply_audio_effects(audio_path: str, pitch_shift: float, speed_rate: float, volume_gain: float, output_format: str = "wav") -> str:
    """
    应用音频效果：音调、语速、音量调整，并转换为指定格式
    """
    try:
        # 加载音频
        audio = AudioSegment.from_wav(audio_path)
        
        # 音量调整
        if volume_gain != 0.0:
            audio = audio + volume_gain
        
        # 语速调整
        if speed_rate != 1.0:
            # 限制语速范围
            speed_rate = max(0.5, min(2.0, speed_rate))
            if speed_rate > 1.0:
                audio = speedup(audio, playback_speed=speed_rate)
            elif speed_rate < 1.0:
                # 减速：通过重采样实现
                new_sample_rate = int(audio.frame_rate * speed_rate)
                audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate})
                audio = audio.set_frame_rate(audio.frame_rate)
        
        # 音调调整（使用ffmpeg实现更好的效果）
        if pitch_shift != 0.0:
            # 限制音调范围
            pitch_shift = max(-12.0, min(12.0, pitch_shift))
            
            # 计算音调调整比例
            pitch_ratio = 2 ** (pitch_shift / 12.0)
            
            # 使用pydub的pitch shift（简单实现）
            # 注意：这是一个简化的实现，实际项目中建议使用更专业的音频处理库
            new_sample_rate = int(audio.frame_rate * pitch_ratio)
            audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate})
            audio = audio.set_frame_rate(22050)  # 恢复到标准采样率
        
        # 根据输出格式保存音频
        if output_format.lower() == "mp3":
            output_path = audio_path.replace('.wav', '_processed.mp3')
            audio.export(output_path, format="mp3", bitrate="192k")
        else:
            output_path = audio_path.replace('.wav', '_processed.wav')
            audio.export(output_path, format="wav")
        
        return output_path
        
    except Exception as e:
        logger.error(f"音频效果处理失败: {e}")
        return audio_path  # 返回原始文件

def convert_audio_format(input_path: str, output_format: str) -> str:
    """
    转换音频格式
    """
    try:
        # 加载音频
        audio = AudioSegment.from_wav(input_path)
        
        # 生成输出路径
        base_path = os.path.splitext(input_path)[0]
        if output_format.lower() == "mp3":
            output_path = f"{base_path}.mp3"
            audio.export(output_path, format="mp3", bitrate="192k")
        else:
            output_path = f"{base_path}.wav"
            audio.export(output_path, format="wav")
        
        # 删除原始WAV文件（如果转换为MP3）
        if output_format.lower() == "mp3" and input_path != output_path:
            try:
                os.remove(input_path)
            except:
                pass
        
        return output_path
        
    except Exception as e:
        logger.error(f"音频格式转换失败: {e}")
        return input_path

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    init_tts_model()

@app.get("/")
async def root():
    """根路径"""
    return {"message": "IndexTTS API Server is running"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "model_loaded": tts_model is not None}

@app.get("/reference_audios")
async def list_reference_audios():
    """列出所有可用的参考音频"""
    try:
        audio_files = []
        for file in os.listdir(REFERENCE_AUDIO_DIR):
            if file.lower().endswith(('.mp3', '.wav', '.flac', '.m4a')):
                file_path = os.path.join(REFERENCE_AUDIO_DIR, file)
                stat = os.stat(file_path)
                audio_files.append({
                    "filename": file,
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })
        
        return {"reference_audios": audio_files}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取参考音频列表失败: {str(e)}")

@app.post("/upload_reference_audio")
async def upload_reference_audio(file: UploadFile = File(...)):
    """上传参考音频文件"""
    try:
        # 检查文件类型
        if not file.filename.lower().endswith(('.mp3', '.wav', '.flac', '.m4a')):
            raise HTTPException(status_code=400, detail="不支持的音频格式")
        
        # 保存文件
        file_path = os.path.join(REFERENCE_AUDIO_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {"message": f"参考音频 {file.filename} 上传成功", "filename": file.filename}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@app.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """
    合成语音
    """
    if tts_model is None:
        raise HTTPException(status_code=500, detail="TTS模型未加载")
    
    start_time = time.time()
    
    try:
        # 检查参考音频文件是否存在
        reference_path = os.path.join(REFERENCE_AUDIO_DIR, request.reference_audio)
        if not os.path.exists(reference_path):
            raise HTTPException(status_code=404, detail=f"参考音频文件不存在: {request.reference_audio}")
        
        # 验证输出格式
        output_format = request.output_format.lower()
        if output_format not in ["mp3", "wav"]:
            output_format = "mp3"  # 默认为mp3
        
        # 生成输出文件名（先生成WAV，后续可能转换格式）
        timestamp = int(time.time() * 1000)
        temp_filename = f"tts_{timestamp}.wav"
        temp_path = os.path.join(OUTPUT_DIR, temp_filename)
        
        # 执行TTS合成
        logger.info(f"开始合成语音: {request.text[:50]}...")
        
        generation_kwargs = {
            "do_sample": request.do_sample,
            "top_p": request.top_p,
            "top_k": request.top_k,
            "temperature": request.temperature,
            "repetition_penalty": request.repetition_penalty,
            "max_mel_tokens": request.max_mel_tokens
        }
        
        if request.infer_mode == "fast":
            result_path = tts_model.infer_fast(
                audio_prompt=reference_path,
                text=request.text,
                output_path=temp_path,
                **generation_kwargs
            )
        else:
            result_path = tts_model.infer(
                audio_prompt=reference_path,
                text=request.text,
                output_path=temp_path,
                **generation_kwargs
            )
        
        # 应用音频效果或格式转换
        if request.pitch_shift != 0.0 or request.speed_rate != 1.0 or request.volume_gain != 0.0:
            logger.info("应用音频效果...")
            result_path = apply_audio_effects(
                result_path, 
                request.pitch_shift, 
                request.speed_rate, 
                request.volume_gain,
                output_format
            )
        elif output_format != "wav":
            # 如果没有音频效果但需要格式转换
            logger.info(f"转换音频格式为: {output_format}")
            result_path = convert_audio_format(result_path, output_format)
        
        # 获取音频时长
        try:
            audio_info = torchaudio.info(result_path)
            duration = audio_info.num_frames / audio_info.sample_rate
        except:
            duration = None
        
        processing_time = time.time() - start_time
        
        logger.info(f"语音合成完成，耗时: {processing_time:.2f}秒")
        
        return TTSResponse(
            success=True,
            message="语音合成成功",
            audio_url=f"/audio/{os.path.basename(result_path)}",
            duration=duration,
            processing_time=processing_time
        )
    
    except Exception as e:
        logger.error(f"语音合成失败: {e}")
        return TTSResponse(
            success=False,
            message=f"语音合成失败: {str(e)}",
            processing_time=time.time() - start_time
        )

@app.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """获取生成的音频文件"""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="音频文件不存在")
    
    # 根据文件扩展名确定媒体类型
    if filename.lower().endswith('.mp3'):
        media_type = "audio/mpeg"
    elif filename.lower().endswith('.wav'):
        media_type = "audio/wav"
    else:
        media_type = "audio/wav"  # 默认为wav
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=filename
    )

@app.delete("/audio/{filename}")
async def delete_audio_file(filename: str):
    """删除音频文件"""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="音频文件不存在")
    
    try:
        os.remove(file_path)
        return {"message": f"音频文件 {filename} 删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="IndexTTS API Server")
    parser.add_argument("--host", default="0.0.0.0", help="服务器地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="开发模式，自动重载")
    
    args = parser.parse_args()
    
    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )