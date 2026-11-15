"""Make realistic ambient sounds and infected voices with a local AI sound model (on the GPU).

Runs in its own environment (PyTorch + diffusers, outside the project):

    C:\\Users\\doboh\\ai_tools\\stable_audio\\.venv\\Scripts\\python.exe tools/sounds/make_ambient_ai.py [--model audioldm2|stable] [name ...]

Models:
- audioldm2 (default): cvssp/audioldm2, no login needed, licence CC BY-NC-SA 4.0 (non-commercial,
  credit the authors, share alike) - fine for this school project, recorded in docs/references/ASSETS.md.
  16 kHz mono.
- stable: stabilityai/stable-audio-open-1.0, better quality, 44.1 kHz stereo, but needs a Hugging
  Face login with the model's licence accepted.

Writes assets/sounds/ai_<name>.wav. Each recipe is a text prompt, a length and a fixed seed, so the
same file comes back. The game's short effects stay synthesized (make_sfx.py); this is for what
synthesis can't do: voices, wind with debris, distant crowds.
"""

import sys
from pathlib import Path

import soundfile
import torch

OUT = Path(__file__).resolve().parents[2] / "assets" / "sounds"
NEGATIVE = "music, melody, singing, speech, low quality, distortion"

RECIPES = {
    # name: (prompt, seconds, seed)
    "wind_ruins": ("cold wind blowing through a ruined empty city street, loose sheet metal rattling, "
                   "distant debris, desolate ambience", 10.0, 11),
    "siren_far": ("a single civil defense siren wailing very far away in an empty city, echoing", 10.0, 12),
    "subway_tunnel": ("dark empty subway tunnel ambience, low rumble, dripping water, distant metal creaks",
                      10.0, 13),
    "infected_groan_1": ("a sick zombie groaning and wheezing, raspy throat, close, horror creature", 3.0, 21),
    "infected_groan_2": ("a hoarse undead creature growling low and breathing heavily, horror", 3.0, 22),
    "infected_scream": ("a zombie shrieking as it spots its prey, short distorted scream, horror", 2.0, 23),
}


def make_audioldm2():
    from diffusers import AudioLDM2Pipeline
    # A local copy (downloaded file by file with curl, since the hub client kept stalling) wins.
    local = Path(r"C:\Users\doboh\ai_tools\models\audioldm2")
    source = str(local) if (local / "model_index.json").exists() else "cvssp/audioldm2"
    pipe = AudioLDM2Pipeline.from_pretrained(source, torch_dtype=torch.float16).to("cuda")

    def run(prompt, seconds, seed):
        audio = pipe(prompt, negative_prompt=NEGATIVE, num_inference_steps=200, audio_length_in_s=seconds,
                     num_waveforms_per_prompt=1, generator=torch.Generator("cuda").manual_seed(seed)).audios[0]
        return audio, 16000
    return run


def make_stable():
    from diffusers import StableAudioPipeline
    pipe = StableAudioPipeline.from_pretrained("stabilityai/stable-audio-open-1.0",
                                               torch_dtype=torch.float16).to("cuda")

    def run(prompt, seconds, seed):
        audio = pipe(prompt, negative_prompt=NEGATIVE, num_inference_steps=100, audio_end_in_s=seconds,
                     num_waveforms_per_prompt=1, generator=torch.Generator("cuda").manual_seed(seed)).audios[0]
        return audio.T.float().cpu().numpy(), pipe.vae.sampling_rate
    return run


def main(args):
    model = "audioldm2"
    if args and args[0] == "--model":
        model, args = args[1], args[2:]
    run = make_stable() if model == "stable" else make_audioldm2()
    OUT.mkdir(parents=True, exist_ok=True)
    for name in args or RECIPES:
        prompt, seconds, seed = RECIPES[name]
        audio, rate = run(prompt, seconds, seed)
        soundfile.write(OUT / f"ai_{name}.wav", audio, rate)
        print("saved", f"ai_{name}", f"{seconds:.0f}s", model)


if __name__ == "__main__":
    main(sys.argv[1:])
