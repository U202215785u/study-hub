#!/usr/bin/env python3
"""
Qwen-3-ASR-Flash 语音识别模块 (共享模块)

支持功能：
1. URL 和本地音频文件识别
2. 上下文增强提高识别准确率
3. 多语言识别
4. 语种检测
"""

import os
import dashscope
from typing import Optional, Union
from pathlib import Path


class QwenASR:
    """Qwen-3-ASR-Flash 语音识别器"""

    def __init__(self, api_key: Optional[str] = None, model: str = "qwen3-asr-flash"):
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("未设置 DASHSCOPE_API_KEY，请在环境变量中设置或传入 api_key 参数")

        self.model = model
        dashscope.api_key = self.api_key

    def recognize_audio(
        self,
        audio_input: Union[str, Path],
        context: Optional[str] = None,
        language: Optional[str] = None,
        enable_lid: bool = True,
        enable_itn: bool = False
    ) -> dict:
        try:
            if isinstance(audio_input, Path):
                audio_input = str(audio_input)

            if os.path.exists(audio_input):
                audio_input = f"file://{os.path.abspath(audio_input)}"

            messages = [
                {
                    "role": "system",
                    "content": [
                        {"text": context or ""}
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {"audio": audio_input}
                    ]
                }
            ]

            asr_options = {
                "enable_lid": enable_lid,
                "enable_itn": enable_itn
            }

            if language:
                asr_options["language"] = language

            response = dashscope.MultiModalConversation.call(
                api_key=self.api_key,
                model=self.model,
                messages=messages,
                result_format="message",
                asr_options=asr_options
            )

            if response.status_code != 200:
                raise Exception(f"API调用失败: {response.message}")

            result = {
                "success": True,
                "text": "",
                "language": None,
                "usage": response.usage,
                "request_id": response.request_id
            }

            if response.output and response.output.choices:
                choice = response.output.choices[0]
                if choice.message and choice.message.content:
                    result["text"] = choice.message.content[0].get("text", "")

                if choice.message.annotations:
                    for annotation in choice.message.annotations:
                        if annotation.get("type") == "audio_info":
                            result["language"] = annotation.get("language")

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "language": None
            }

    def recognize_url(
        self,
        audio_url: str,
        context: Optional[str] = None,
        language: Optional[str] = None,
        enable_lid: bool = True,
        enable_itn: bool = False
    ) -> dict:
        return self.recognize_audio(
            audio_input=audio_url,
            context=context,
            language=language,
            enable_lid=enable_lid,
            enable_itn=enable_itn
        )

    def recognize_file(
        self,
        file_path: Union[str, Path],
        context: Optional[str] = None,
        language: Optional[str] = None,
        enable_lid: bool = True,
        enable_itn: bool = False
    ) -> dict:
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            return {
                "success": False,
                "error": f"文件不存在: {file_path}",
                "text": "",
                "language": None
            }

        return self.recognize_audio(
            audio_input=file_path,
            context=context,
            language=language,
            enable_lid=enable_lid,
            enable_itn=enable_itn
        )


def create_asr_instance(api_key: Optional[str] = None, model: str = "qwen3-asr-flash") -> QwenASR:
    return QwenASR(api_key=api_key, model=model)
