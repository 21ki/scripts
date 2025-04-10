"""
title: QwenLM OCR
author: konbakuyomu
description: This project is a reverse-engineered implementation of QwenLM's OCR functionality. By calling QwenLM's API, you can extract text content from images.
version: 1.1.0
licence: MIT
link https://linux.do/t/topic/367945
"""

from pydantic import BaseModel, Field
import aiohttp
import asyncio
from typing import Callable, Awaitable, Any, Optional
import base64
import re
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Pipeline:
    class Valves(BaseModel):
        # api base url
        base_api_url: str = Field(
            default="https://test-qwen-cor.aughumes8.workers.dev",
            description="ocr api base url",
        )
        # token or cookie
        ocr_api_token: str = Field(
            default="", description="OCR API token"
        )

    def __init__(self):
        self.valves = self.Valves()

    async def default_event_emitter(self, event: Any) -> None:
        """Default event emitter that logs events."""
        logger.debug(f"Event emitted: {event}")

    async def pipe(
        self,
        body: dict,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
        user: Optional[dict] = None,
        user_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Processing logic for 3 recognition methods:
        1) Local file upload -> return imageId -> request /recognize
        2) Direct via URL
        3) Direct via Base64

        Args:
            body: The request body containing messages or file information
            __event_emitter__: Optional callback function for emitting status events
            user: Optional user information
            user_message: Optional user message
            **kwargs: Additional keyword arguments
        """
        # Use default event emitter if none provided
        event_emitter = __event_emitter__ or self.default_event_emitter

        try:
            # If user_message is provided, add it to the body
            if user_message:
                if not body.get("messages"):
                    body["messages"] = []
                body["messages"].append({"content": user_message})

            # 1. If local file detected, upload first -> then recognize
            image_file_path = self._extract_file_path(body)
            if image_file_path and os.path.exists(image_file_path):
                method = "File Upload"
                await event_emitter(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Local file detected, processing via {method}, please wait...",
                            "done": False,
                        },
                    }
                )

                try:
                    # Build complete upload URL
                    upload_url = f"{self.valves.base_api_url}/proxy/upload"
                    upload_headers = {
                        "x-custom-cookie": self.valves.ocr_api_token or "api",
                        "Authorization": f"Bearer {self.valves.ocr_api_token}" if self.valves.ocr_api_token else None
                    }
                    upload_headers = {k: v for k, v in upload_headers.items() if v is not None}

                    form_data = aiohttp.FormData()
                    form_data.add_field(
                        name="file",
                        value=open(image_file_path, "rb"),
                        filename=os.path.basename(image_file_path),
                        content_type="application/octet-stream",
                    )

                    timeout = aiohttp.ClientTimeout(total=30)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.post(
                            upload_url, headers=upload_headers, data=form_data
                        ) as resp:
                            resp.raise_for_status()
                            upload_result = await resp.json()
                            logger.debug(f"Upload response: {upload_result}")

                    # Get imageId from response, then call /recognize
                    image_id = upload_result.get("id")
                    if not image_id:
                        return "Upload successful, but no valid ID received. Please check backend response."

                    # Build complete recognition URL
                    recognize_url = f"{self.valves.base_api_url}/recognize"
                    recognize_headers = {
                        "x-custom-cookie": self.valves.ocr_api_token or "api",
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.valves.ocr_api_token}" if self.valves.ocr_api_token else None
                    }
                    recognize_headers = {k: v for k, v in recognize_headers.items() if v is not None}
                    
                    payload = {"imageId": image_id}

                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.post(
                            recognize_url, headers=recognize_headers, json=payload
                        ) as resp:
                            resp.raise_for_status()
                            ocr_result = await resp.json()
                            logger.debug(f"Recognition response: {ocr_result}")

                    # Notify completion
                    await event_emitter(
                        {
                            "type": "status",
                            "data": {
                                "description": "✅ Image recognition completed!",
                                "done": True,
                            },
                        }
                    )
                    return self._format_ocr_result(ocr_result)

                except Exception as e:
                    logger.error(f"Error during file processing: {str(e)}", exc_info=True)
                    await event_emitter(
                        {
                            "type": "status",
                            "data": {
                                "description": f"❌ File upload or recognition failed: {e}",
                                "done": True,
                            },
                        }
                    )
                    return f"File upload or recognition failed: {e}"

            else:
                # 2. If no local file, try URL / Base64 methods
                user_provided_image_url = self._extract_user_input_image_url(body)
                if user_provided_image_url:
                    method = "URL (User Input)"
                    ocr_api_url = f"{self.valves.base_api_url}/api/recognize/url"
                    payload = {"imageUrl": user_provided_image_url}
                else:
                    image_url = self._extract_image_url(body)
                    base64_image = self._extract_base64_image(body)

                    if image_url:
                        method = "URL"
                        ocr_api_url = f"{self.valves.base_api_url}/api/recognize/url"
                        payload = {"imageUrl": image_url}
                    elif base64_image:
                        method = "Base64"
                        ocr_api_url = f"{self.valves.base_api_url}/api/recognize/base64"
                        payload = {"base64Image": base64_image}
                    else:
                        return "No valid image provided (Local file / URL / Base64)."

                # Notify start of recognition
                await event_emitter(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Processing image via {method}, please wait...",
                            "done": False,
                        },
                    }
                )

                # Send request
                try:
                    headers = {
                        "Content-Type": "application/json",
                        "x-custom-cookie": self.valves.ocr_api_token or "api",
                        "Authorization": f"Bearer {self.valves.ocr_api_token}" if self.valves.ocr_api_token else None
                    }
                    headers = {k: v for k, v in headers.items() if v is not None}

                    timeout = aiohttp.ClientTimeout(total=30)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.post(
                            ocr_api_url, headers=headers, json=payload
                        ) as response:
                            response.raise_for_status()
                            ocr_result = await response.json()
                            logger.debug(f"OCR response: {ocr_result}")

                    # Process complete
                    await event_emitter(
                        {
                            "type": "status",
                            "data": {
                                "description": "✅ Image recognition completed!",
                                "done": True,
                            },
                        }
                    )
                    return self._format_ocr_result(ocr_result)

                except Exception as e:
                    logger.error(f"Error during OCR request: {str(e)}", exc_info=True)
                    # Error occurred
                    await event_emitter(
                        {
                            "type": "status",
                            "data": {
                                "description": f"❌ OCR API request failed: {e}",
                                "done": True,
                            },
                        }
                    )
                    return f"OCR API request failed: {e}"
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}", exc_info=True)
            return f"Pipeline error: {str(e)}"

    #
    # Helper methods below, not involving request body changes
    #
    def _extract_user_input_image_url(self, body: dict) -> Optional[str]:
        """Extract possible image URL from user message text."""
        messages = body.get("messages", [])
        if not messages:
            return None
        last_message = messages[-1]
        content = last_message.get("content", "")
        if isinstance(content, str):
            urls = self._find_image_urls_in_text(content)
            if urls:
                return urls[0]
        return None

    def _find_image_urls_in_text(self, text: str) -> list:
        """Use regex to find image URLs with common extensions in text."""
        image_url_pattern = re.compile(
            r"(https?://[^\s]+?\.(?:png|jpg|jpeg|gif|bmp|tiff|webp))", re.IGNORECASE
        )
        return image_url_pattern.findall(text)

    def _extract_image_url(self, body: dict) -> Optional[str]:
        """Parse image URL from body (if message structure is list)."""
        messages = body.get("messages", [])
        if messages:
            last_message = messages[-1]
            if isinstance(last_message.get("content"), list):
                for content_item in last_message["content"]:
                    if content_item.get("type") == "image_url":
                        return content_item["image_url"].get("url")
        return None

    def _extract_base64_image(self, body: dict) -> Optional[str]:
        """Extract base64 encoded image from body."""
        messages = body.get("messages", [])
        if messages:
            last_message = messages[-1]
            content = last_message.get("content")
            if isinstance(content, str):
                if content.startswith("data:image") and "base64," in content:
                    base64_data = content.split("base64,")[-1]
                    if self._is_base64(base64_data):
                        return base64_data
                elif self._is_base64(content):
                    return content
        return None

    def _is_base64(self, s: str) -> bool:
        """Check if string is valid Base64 encoding."""
        try:
            if not re.fullmatch(r"[A-Za-z0-9+/]+={0,2}", s):
                return False
            base64.b64decode(s, validate=True)
            return True
        except Exception:
            return False

    def _extract_file_path(self, body: dict) -> Optional[str]:
        """Example method to extract local file path from body."""
        messages = body.get("messages", [])
        if messages:
            last_message = messages[-1]
            file_path = last_message.get("file_path")
            if file_path and os.path.isfile(file_path):
                return file_path
        return None

    def _format_ocr_result(self, ocr_result: dict) -> str:
        """Format recognition result based on API response."""
        if ocr_result.get("success"):
            return f"Recognition Result:\n{ocr_result.get('result', 'No text detected.')}"
        else:
            return f"OCR API returned error: {ocr_result.get('error', 'Unknown error')}"
