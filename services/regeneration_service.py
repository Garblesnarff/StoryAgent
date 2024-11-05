class RegenerationService:
    def __init__(self, image_generator, audio_generator):
        self.image_generator = image_generator
        self.audio_generator = audio_generator
    
    def regenerate_image(self, text):
        return self.image_generator.generate_image(text)
    
    def regenerate_audio(self, text):
        return self.audio_generator.generate_audio(text)
