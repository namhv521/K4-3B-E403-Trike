"""TTS stage kept separate so the agent can replace providers later."""


def generate_tts(lesson, client, output_path):
    return client.synthesize_free(lesson["narration"], output_path)
