# 基础镜像：使用包含 nvcc 的 devel 版本，确保编译 CUDA 扩展时可找到工具
FROM --platform=linux/amd64 nvidia/cuda:12.8.1-cudnn-devel-ubuntu22.04

# 环境变量：适配阿里云函数计算
ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/root/miniconda3/bin:${PATH}" \
    TORCH_CUDA_ARCH_LIST="8.6;9.0" \
    CAPORT=9000

# 关键修改：更换Ubuntu源为阿里云镜像（解决网络超时）
RUN sed -i "s@archive.ubuntu.com@mirrors.aliyun.com@g" /etc/apt/sources.list && \
    sed -i "s@security.ubuntu.com@mirrors.aliyun.com@g" /etc/apt/sources.list && \
    # 解决GPG签名问题
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A4B469963BF863CC && \
    # 先更新源，再安装依赖（添加--fix-missing处理部分包下载失败）
    apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
        wget \
        ffmpeg \
        build-essential \
        ninja-build && \
    # 清理缓存，减小镜像体积
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


# 安装Miniconda（更换为官方源或正确的国内镜像）
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh && \
    bash miniconda.sh -b -p /root/miniconda3 && \
    rm miniconda.sh && \
    /root/miniconda3/bin/conda init bash && \
    # 配置conda国内镜像（使用清华源，稳定可靠）
    /root/miniconda3/bin/conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main && \
    /root/miniconda3/bin/conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free && \
    /root/miniconda3/bin/conda config --set show_channel_urls yes

# 创建并激活Conda环境
RUN /root/miniconda3/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    /root/miniconda3/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r && \
    /root/miniconda3/bin/conda create -n index-tts python=3.10 -y && \
    echo ". /root/miniconda3/etc/profile.d/conda.sh && conda activate index-tts" >> ~/.bashrc

    # 安装PyTorch及其他依赖
RUN /root/miniconda3/bin/conda run -n index-tts \
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128 -i https://mirrors.aliyun.com/pypi/simple/ && \
    /root/miniconda3/bin/conda run -n index-tts \
    conda install -c conda-forge pynini==2.1.6 -y && \
    /root/miniconda3/bin/conda run -n index-tts \
    pip install WeTextProcessing --no-deps -i https://mirrors.aliyun.com/pypi/simple/



# 复制代码并安装项目依赖
WORKDIR /workspace/index-tts
COPY . .

# 安装项目依赖时，确保 TORCH_CUDA_ARCH_LIST 正确（适配阿里云 GPU 架构）
RUN /root/miniconda3/bin/conda run -n index-tts \
    pip install -e . -i https://mirrors.aliyun.com/pypi/simple/ && \
    /root/miniconda3/bin/conda run -n index-tts \
    pip install -e ".[webui]" --no-build-isolation -i https://mirrors.aliyun.com/pypi/simple/ && \
    /root/miniconda3/bin/conda run -n index-tts pip cache purge

    
# 安装deepspeed（可选，按需保留）
RUN /root/miniconda3/bin/conda run -n index-tts \
    pip install deepspeed -i https://mirrors.aliyun.com/pypi/simple/

# 暴露CAPort（必须与函数计算配置一致，默认9000）
EXPOSE $CAPORT

# 启动命令：适配HTTP Server要求（监听9000、Keep-Alive、120秒内启动）
CMD ["/bin/bash", "-c", ". /root/miniconda3/etc/profile.d/conda.sh && conda activate index-tts && python webui.py --model_dir checkpoints --host 0.0.0.0 --port $CAPORT"]