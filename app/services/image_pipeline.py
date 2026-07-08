import json
import os
import tempfile
import uuid
import time

from pathlib import Path
from typing import Any

import requests
import torch

from PIL import Image

from transformers import (
    AutoProcessor,
    Qwen2_5_VLForConditionalGeneration,
)

from app.core.logger import logger


PLANTNET_URL = (
    "https://my-api.plantnet.org/v2/identify/all"
)

API_KEY = os.getenv(
    "PLANTNET_API_KEY",
    "2b10JO0aVOvSz0oouFEVcXnS"
)

CONFIDENCE_THRESHOLD = 0.80

QWEN_MODEL_ID = (
    "Qwen/Qwen2.5-VL-3B-Instruct"
)


class ImagePipeline:

    def __init__(self):

        self.processor = None
        self.model = None

    def load_models(self):

        if self.model is not None:
            return

        logger.info(
            "Loading Qwen Vision Model"
        )

        self.processor = (
            AutoProcessor.from_pretrained(
                QWEN_MODEL_ID
            )
        )

        self.model = (
            Qwen2_5_VLForConditionalGeneration
            .from_pretrained(
                QWEN_MODEL_ID
            )
        )

        logger.info(
            "Qwen Vision Loaded"
        )

    # async def process(
    #     self,
    #     image_bytes: bytes,
    # ):

    #     temp_path = Path(
    #         tempfile.gettempdir()
    #     ) / f"{uuid.uuid4()}.jpg"

    #     with open(
    #         temp_path,
    #         "wb",
    #     ) as f:

    #         f.write(image_bytes)

    #     crop_result = self.identify_crop(
    #         str(temp_path)
    #     )

    #     crop_name = crop_result.get(
    #         "crop_name",
    #         "Unknown"
    #     )

    #     symptoms = (
    #         self.extract_symptoms(
    #             str(temp_path),
    #             crop_name,
    #         )
    #     )

    #     try:

    #         symptoms = json.loads(
    #             symptoms
    #         )

    #     except Exception:

    #         symptoms = {
    #             "plant_part": "",
    #             "visible_symptoms": [],
    #             "visible_damage": [],
    #             "severity": "",
    #         }

    #     return {

    #         "crop_name":
    #             crop_result.get(
    #                 "crop_name",
    #                 "Unknown",
    #             ),

    #         "scientific_name":
    #             crop_result.get(
    #                 "scientific_name",
    #                 "",
    #             ),

    #         "crop_confidence":
    #             crop_result.get(
    #                 "confidence",
    #                 0,
    #             ),

    #         **symptoms,
    #     }

    import time

    async def process(
        self,
        image_bytes: bytes,
    ):

        total_start = time.time()

        temp_path = Path(
            tempfile.gettempdir()
        ) / f"{uuid.uuid4()}.jpg"

        with open(
            temp_path,
            "wb",
        ) as f:

            f.write(image_bytes)

        # ==========================
        # PlantNet Timing
        # ==========================

        start = time.time()

        crop_result = self.identify_crop(
            str(temp_path)
        )

        logger.info(
            "PlantNet completed",
            seconds=round(
                time.time() - start,
                2
            )
        )

        crop_name = crop_result.get(
            "crop_name",
            "Unknown"
        )

        # ==========================
        # Qwen Timing
        # ==========================

        start = time.time()

        symptoms = (
            self.extract_symptoms(
                str(temp_path),
                crop_name,
            )
        )

        logger.info(
            "Qwen completed",
            seconds=round(
                time.time() - start,
                2
            )
        )

        try:

            symptoms = json.loads(
                symptoms
            )

        except Exception:

            symptoms = {
                "plant_part": "",
                "visible_symptoms": [],
                "visible_damage": [],
                "severity": "",
            }

        logger.info(
            "Image Pipeline completed",
            seconds=round(
                time.time() - total_start,
                2
            )
        )

        return {

            "crop_name":
                crop_result.get(
                    "crop_name",
                    "Unknown",
                ),

            "scientific_name":
                crop_result.get(
                    "scientific_name",
                    "",
                ),

            "crop_confidence":
                crop_result.get(
                    "confidence",
                    0,
                ),

            **symptoms,
        }

    def identify_crop(
        self,
        image_path: str,
    ):

        url = (
            f"{PLANTNET_URL}"
            f"?api-key={API_KEY}"
        )

        with open(
            image_path,
            "rb",
        ) as image_file:

            files = {
                "images": (
                    Path(
                        image_path
                    ).name,
                    image_file,
                    "image/jpeg",
                )
            }

            response = requests.post(
                url,
                files=files,
                data={
                    "organs": "leaf"
                },
                timeout=30,
            )

        response.raise_for_status()

        result = response.json()

        if not result.get(
            "results"
        ):
            return {
                "crop_name":
                    "Unknown"
            }

        best = result[
            "results"
        ][0]

        species = best.get(
            "species",
            {},
        )

        common_names = (
            species.get(
                "commonNames",
                []
            )
        )

        crop_name = (
            common_names[0]
            if common_names
            else species.get(
                "scientificNameWithoutAuthor",
                "Unknown"
            )
        )

        return {
            "crop_name":
                crop_name,

            "scientific_name":
                species.get(
                    "scientificNameWithoutAuthor",
                    ""
                ),

            "confidence":
                best.get(
                    "score",
                    0
                ),
        }

    def extract_symptoms(
        self,
        image_path: str,
        crop_name: str,
    ):

        image = (
            Image.open(
                image_path
            )
            .convert("RGB")
        )

        image.thumbnail(
            (1024, 1024)
        )

        prompt = f"""
Crop Name: {crop_name}

Return ONLY JSON

{{
  "plant_part":"",
  "visible_symptoms":[],
  "visible_damage":[],
  "severity":""
}}

Only visible observations.
Do not diagnose.
"""

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image"
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ]

        text = (
            self.processor
            .apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        )

        inputs = (
            self.processor(
                text=[text],
                images=[image],
                return_tensors="pt",
            )
        )

        inputs = {
            k: v.to(
                self.model.device
            )
            for k, v in inputs.items()
        }

        output = (
            self.model.generate(
                **inputs,
                max_new_tokens=100,
                do_sample=False,
            )
        )

        trimmed = [

            out[
                len(inp):
            ]

            for inp, out
            in zip(
                inputs[
                    "input_ids"
                ],
                output,
            )
        ]

        response = (
            self.processor
            .batch_decode(
                trimmed,
                skip_special_tokens=True,
            )[0]
        )

        return (
            response
            .replace(
                "```json",
                ""
            )
            .replace(
                "```",
                ""
            )
            .strip()
        )


image_pipeline = (
    ImagePipeline()
)