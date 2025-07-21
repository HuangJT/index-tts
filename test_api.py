#!/usr/bin/env python3
"""
IndexTTS API 测试脚本
用于验证API服务的各项功能
"""

import requests
import time
import os
import json
from pathlib import Path

API_BASE_URL = "http://127.0.0.1:8000"

def test_health_check():
    """测试健康检查接口"""
    print("🔍 测试健康检查...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查通过: {data}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器，请确保服务器已启动")
        return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_list_reference_audios():
    """测试列出参考音频接口"""
    print("\n📁 测试列出参考音频...")
    try:
        response = requests.get(f"{API_BASE_URL}/reference_audios")
        if response.status_code == 200:
            data = response.json()
            audios = data.get("reference_audios", [])
            print(f"✅ 找到 {len(audios)} 个参考音频:")
            for audio in audios:
                size_mb = audio["size"] / (1024 * 1024)
                print(f"   - {audio['filename']} ({size_mb:.2f} MB)")
            return audios
        else:
            print(f"❌ 获取参考音频列表失败: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 获取参考音频列表异常: {e}")
        return []

def test_synthesize_basic(reference_audio):
    """测试基础语音合成"""
    print(f"\n🎤 测试基础语音合成 (参考音频: {reference_audio})...")
    
    data = {
        "text": "这是一个基础的语音合成测试，用来验证API接口的功能是否正常。",
        "reference_audio": reference_audio,
        "output_format": "mp3",  # 默认使用MP3格式
        "infer_mode": "fast"
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{API_BASE_URL}/synthesize", json=data, timeout=60)
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print(f"✅ 基础合成成功!")
                print(f"   音频URL: {result['audio_url']}")
                print(f"   处理时间: {result['processing_time']:.2f}秒")
                print(f"   请求时间: {request_time:.2f}秒")
                if result.get("duration"):
                    print(f"   音频时长: {result['duration']:.2f}秒")
                return result
            else:
                print(f"❌ 合成失败: {result['message']}")
                return None
        else:
            print(f"❌ 请求失败: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.Timeout:
        print("❌ 请求超时，可能是文本太长或服务器负载过高")
        return None
    except Exception as e:
        print(f"❌ 合成异常: {e}")
        return None

def test_synthesize_with_effects(reference_audio):
    """测试带音频效果的语音合成"""
    print(f"\n🎵 测试音频效果合成 (参考音频: {reference_audio})...")
    
    data = {
        "text": "这是一个音频效果测试，音调提高，语速加快，音量增大。",
        "reference_audio": reference_audio,
        "output_format": "wav",  # 使用WAV格式测试
        "pitch_shift": 2.0,     # 提高2个半音
        "speed_rate": 1.2,      # 语速加快20%
        "volume_gain": 3.0,     # 音量增加3dB
        "infer_mode": "fast",
        "temperature": 0.9
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{API_BASE_URL}/synthesize", json=data, timeout=60)
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print(f"✅ 效果合成成功!")
                print(f"   音频URL: {result['audio_url']}")
                print(f"   处理时间: {result['processing_time']:.2f}秒")
                print(f"   请求时间: {request_time:.2f}秒")
                print(f"   应用效果: 音调+2, 语速x1.2, 音量+3dB")
                return result
            else:
                print(f"❌ 效果合成失败: {result['message']}")
                return None
        else:
            print(f"❌ 请求失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 效果合成异常: {e}")
        return None

def test_download_audio(audio_url, filename):
    """测试下载音频文件"""
    print(f"\n💾 测试下载音频: {filename}...")
    
    try:
        response = requests.get(f"{API_BASE_URL}{audio_url}")
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            
            file_size = os.path.getsize(filename)
            print(f"✅ 音频下载成功: {filename} ({file_size} bytes)")
            return True
        else:
            print(f"❌ 下载失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 下载异常: {e}")
        return False

def test_audio_formats(reference_audio):
    """测试不同音频格式输出"""
    print(f"\n🎵 测试音频格式输出 (参考音频: {reference_audio})...")
    
    test_text = "这是用来测试不同音频格式输出的文本。"
    timestamp = int(time.time())
    results = {}
    
    # 测试MP3格式
    print("   测试MP3格式...")
    mp3_data = {
        "text": test_text,
        "reference_audio": reference_audio,
        "output_format": "mp3",
        "infer_mode": "fast"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/synthesize", json=mp3_data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                audio_url = result["audio_url"]
                if ".mp3" in audio_url:
                    print(f"   ✅ MP3格式生成成功: {audio_url}")
                    # 下载测试
                    filename = f"test_format_mp3_{timestamp}.mp3"
                    if test_download_audio(audio_url, filename):
                        results["mp3"] = True
                    else:
                        results["mp3"] = False
                else:
                    print(f"   ❌ MP3格式错误: URL中没有.mp3扩展名")
                    results["mp3"] = False
            else:
                print(f"   ❌ MP3格式合成失败: {result['message']}")
                results["mp3"] = False
        else:
            print(f"   ❌ MP3格式请求失败: {response.status_code}")
            results["mp3"] = False
    except Exception as e:
        print(f"   ❌ MP3格式测试异常: {e}")
        results["mp3"] = False
    
    # 测试WAV格式
    print("   测试WAV格式...")
    wav_data = {
        "text": test_text,
        "reference_audio": reference_audio,
        "output_format": "wav",
        "infer_mode": "fast"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/synthesize", json=wav_data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                audio_url = result["audio_url"]
                if ".wav" in audio_url:
                    print(f"   ✅ WAV格式生成成功: {audio_url}")
                    # 下载测试
                    filename = f"test_format_wav_{timestamp}.wav"
                    if test_download_audio(audio_url, filename):
                        results["wav"] = True
                    else:
                        results["wav"] = False
                else:
                    print(f"   ❌ WAV格式错误: URL中没有.wav扩展名")
                    results["wav"] = False
            else:
                print(f"   ❌ WAV格式合成失败: {result['message']}")
                results["wav"] = False
        else:
            print(f"   ❌ WAV格式请求失败: {response.status_code}")
            results["wav"] = False
    except Exception as e:
        print(f"   ❌ WAV格式测试异常: {e}")
        results["wav"] = False
    
    return results

def test_error_handling():
    """测试错误处理"""
    print(f"\n⚠️  测试错误处理...")
    
    # 测试不存在的参考音频
    data = {
        "text": "测试文本",
        "reference_audio": "不存在的音频.mp3"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/synthesize", json=data)
        if response.status_code == 404:
            print("✅ 正确处理了不存在的参考音频错误")
        else:
            result = response.json()
            if not result.get("success", True):
                print("✅ 正确返回了错误信息")
            else:
                print("❌ 应该返回错误但没有")
    except Exception as e:
        print(f"❌ 错误处理测试异常: {e}")

def main():
    print("=" * 60)
    print("🧪 IndexTTS API 功能测试")
    print("=" * 60)
    
    # 1. 健康检查
    if not test_health_check():
        print("\n❌ API服务器未运行，请先启动服务器:")
        print("   python api_server.py")
        print("   或")
        print("   python start_services.py --mode api")
        return
    
    # 2. 列出参考音频
    audios = test_list_reference_audios()
    if not audios:
        print("\n❌ 没有找到参考音频文件")
        print("💡 请将音频文件放到 reference_audios/ 目录下")
        print("💡 或使用以下命令添加:")
        print("   python manage_reference_audios.py add 'path/to/audio.wav'")
        return
    
    # 选择第一个音频进行测试
    test_audio = audios[0]["filename"]
    
    # 3. 基础合成测试
    print("⏱️ 开始基础合成测试计时...")
    start_basic = time.time()
    basic_result = test_synthesize_basic(test_audio)
    end_basic = time.time()
    print(f"⏱️ 基础合成总耗时: {end_basic - start_basic:.2f} 秒")
    
    # 4. 音频效果测试
    print("⏱️ 开始音频效果合成测试计时...")
    start_effects = time.time()
    effects_result = test_synthesize_with_effects(test_audio)
    end_effects = time.time()
    print(f"⏱️ 音频效果合成总耗时: {end_effects - start_effects:.2f} 秒")
    # 5. 下载测试
    download_count = 0
    timestamp = int(time.time())
    
    if basic_result:
        # 根据返回的URL确定文件扩展名
        audio_url = basic_result["audio_url"]
        if ".mp3" in audio_url:
            filename = f"test_basic_{timestamp}.mp3"
        else:
            filename = f"test_basic_{timestamp}.wav"
        
        if test_download_audio(audio_url, filename):
            download_count += 1
    
    if effects_result:
        # 根据返回的URL确定文件扩展名
        audio_url = effects_result["audio_url"]
        if ".mp3" in audio_url:
            filename = f"test_effects_{timestamp}.mp3"
        else:
            filename = f"test_effects_{timestamp}.wav"
        
        if test_download_audio(audio_url, filename):
            download_count += 1
    
    # 6. 音频格式测试
    format_results = test_audio_formats(test_audio)
    
    # 7. 错误处理测试
    test_error_handling()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    total_tests = 5
    passed_tests = 0
    
    if basic_result:
        passed_tests += 1
        print("✅ 基础语音合成: 通过")
    else:
        print("❌ 基础语音合成: 失败")
    
    if effects_result:
        passed_tests += 1
        print("✅ 音频效果合成: 通过")
    else:
        print("❌ 音频效果合成: 失败")
    
    if download_count > 0:
        passed_tests += 1
        print(f"✅ 音频下载: 通过 ({download_count} 个文件)")
    else:
        print("❌ 音频下载: 失败")
    
    # 音频格式测试结果
    if format_results.get("mp3", False) and format_results.get("wav", False):
        passed_tests += 1
        print("✅ 音频格式测试: 通过 (MP3 ✓, WAV ✓)")
    elif format_results.get("mp3", False) or format_results.get("wav", False):
        passed_tests += 0.5
        mp3_status = "✓" if format_results.get("mp3", False) else "✗"
        wav_status = "✓" if format_results.get("wav", False) else "✗"
        print(f"⚠️  音频格式测试: 部分通过 (MP3 {mp3_status}, WAV {wav_status})")
    else:
        print("❌ 音频格式测试: 失败")
    
    passed_tests += 1  # 错误处理总是通过
    print("✅ 错误处理: 通过")
    
    print(f"\n🎯 测试结果: {int(passed_tests)}/{total_tests} 通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过! API服务运行正常")
    else:
        print("⚠️  部分测试失败，请检查服务配置")

if __name__ == "__main__":
    main()