import numpy as np
import torch

from silero_vad import load_silero_vad, get_speech_timestamps


class SileroVAD:
    def __init__(self):
        self.model = load_silero_vad()

    def is_speech(self, audio: np.ndarray, sample_rate: int) -> bool:
        """
        Parameters
        ----------
        audio
            float32 numpy array in range [-1.0, 1.0]

        sample_rate
            Usually 16000

        Returns
        -------
        bool
            True if this chunk contains speech.
        """

        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        audio_tensor = torch.from_numpy(audio)

        speech = get_speech_timestamps(
            audio_tensor,
            self.model,
            sampling_rate=sample_rate,
            threshold=0.65,
            min_speech_duration_ms=250,
            # min_silence_duration_ms=500,
        )

        return len(speech) > 0 # return True or False based on Speach.