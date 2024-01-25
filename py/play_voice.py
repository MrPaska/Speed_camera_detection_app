from kivy.core.audio import SoundLoader

voice0 = "../voices/momentinis.mp3"
voice1 = "../voices/vidutinis.mp3"
sound0 = SoundLoader.load(voice0)
sound1 = SoundLoader.load(voice1)


def play_voice(digit):
    sound = sound0 if digit == 0 else sound1
    try:
        sound.play()
    except Exception as e:
        print(e)

