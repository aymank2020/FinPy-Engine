from hypothesis import settings, Phase

settings.register_profile("ci", max_examples=50, phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target])
settings.load_profile("ci")
