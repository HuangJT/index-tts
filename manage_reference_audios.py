#!/usr/bin/env python3
"""
参考音频管理工具
用于管理reference_audios目录中的音频文件
"""

import os
import shutil
import argparse
from pathlib import Path
import torchaudio

REFERENCE_DIR = "reference_audios"

def list_audios():
    """列出所有参考音频"""
    if not os.path.exists(REFERENCE_DIR):
        print(f"❌ 目录 {REFERENCE_DIR} 不存在")
        return
    
    files = []
    for file in os.listdir(REFERENCE_DIR):
        if file.lower().endswith(('.mp3', '.wav', '.flac', '.m4a')):
            file_path = os.path.join(REFERENCE_DIR, file)
            stat = os.stat(file_path)
            
            # 尝试获取音频信息
            try:
                info = torchaudio.info(file_path)
                duration = info.num_frames / info.sample_rate
                sample_rate = info.sample_rate
                channels = info.num_channels
            except:
                duration = None
                sample_rate = None
                channels = None
            
            files.append({
                'name': file,
                'size': stat.st_size,
                'duration': duration,
                'sample_rate': sample_rate,
                'channels': channels
            })
    
    if not files:
        print("📁 没有找到音频文件")
        return
    
    print(f"📁 参考音频列表 ({len(files)} 个文件):")
    print("-" * 80)
    for file in files:
        size_mb = file['size'] / (1024 * 1024)
        print(f"🎵 {file['name']}")
        print(f"   大小: {size_mb:.2f} MB")
        if file['duration']:
            print(f"   时长: {file['duration']:.2f} 秒")
            print(f"   采样率: {file['sample_rate']} Hz")
            print(f"   声道数: {file['channels']}")
        print()

def add_audio(source_path: str, target_name: str = None):
    """添加音频文件"""
    if not os.path.exists(source_path):
        print(f"❌ 源文件不存在: {source_path}")
        return
    
    os.makedirs(REFERENCE_DIR, exist_ok=True)
    
    if target_name is None:
        target_name = os.path.basename(source_path)
    
    target_path = os.path.join(REFERENCE_DIR, target_name)
    
    if os.path.exists(target_path):
        response = input(f"⚠️  文件 {target_name} 已存在，是否覆盖? (y/N): ")
        if response.lower() != 'y':
            print("❌ 操作取消")
            return
    
    try:
        shutil.copy2(source_path, target_path)
        print(f"✅ 音频文件已添加: {target_name}")
        
        # 显示文件信息
        try:
            info = torchaudio.info(target_path)
            duration = info.num_frames / info.sample_rate
            print(f"   时长: {duration:.2f} 秒")
            print(f"   采样率: {info.sample_rate} Hz")
            print(f"   声道数: {info.num_channels}")
        except:
            pass
            
    except Exception as e:
        print(f"❌ 复制失败: {e}")

def remove_audio(filename: str):
    """删除音频文件"""
    file_path = os.path.join(REFERENCE_DIR, filename)
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {filename}")
        return
    
    response = input(f"⚠️  确定要删除 {filename}? (y/N): ")
    if response.lower() != 'y':
        print("❌ 操作取消")
        return
    
    try:
        os.remove(file_path)
        print(f"✅ 文件已删除: {filename}")
    except Exception as e:
        print(f"❌ 删除失败: {e}")

def rename_audio(old_name: str, new_name: str):
    """重命名音频文件"""
    old_path = os.path.join(REFERENCE_DIR, old_name)
    new_path = os.path.join(REFERENCE_DIR, new_name)
    
    if not os.path.exists(old_path):
        print(f"❌ 文件不存在: {old_name}")
        return
    
    if os.path.exists(new_path):
        print(f"❌ 目标文件名已存在: {new_name}")
        return
    
    try:
        os.rename(old_path, new_path)
        print(f"✅ 文件已重命名: {old_name} -> {new_name}")
    except Exception as e:
        print(f"❌ 重命名失败: {e}")

def main():
    parser = argparse.ArgumentParser(description="参考音频管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list命令
    subparsers.add_parser('list', help='列出所有参考音频')
    
    # add命令
    add_parser = subparsers.add_parser('add', help='添加音频文件')
    add_parser.add_argument('source', help='源音频文件路径')
    add_parser.add_argument('--name', help='目标文件名（可选）')
    
    # remove命令
    remove_parser = subparsers.add_parser('remove', help='删除音频文件')
    remove_parser.add_argument('filename', help='要删除的文件名')
    
    # rename命令
    rename_parser = subparsers.add_parser('rename', help='重命名音频文件')
    rename_parser.add_argument('old_name', help='原文件名')
    rename_parser.add_argument('new_name', help='新文件名')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_audios()
    elif args.command == 'add':
        add_audio(args.source, args.name)
    elif args.command == 'remove':
        remove_audio(args.filename)
    elif args.command == 'rename':
        rename_audio(args.old_name, args.new_name)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()