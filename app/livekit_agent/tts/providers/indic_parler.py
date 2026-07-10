class IndicParlerProvider:

    def __init__(self):

        self.description = (
            "Divya speaks calmly in Hindi with clear audio."
        )

    def stream(self, text: str):

        yield from generate(
            text=text,
            description=self.description,
            play_steps_in_s=0.5,
        )