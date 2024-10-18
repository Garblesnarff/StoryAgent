import os
from groq import Groq
import google.generativeai as genai

groq_api_key = os.environ.get('GROQ_API_KEY')
gemini_api_key = os.environ.get('GEMINI_API_KEY')

groq_client = Groq(api_key=groq_api_key)
genai.configure(api_key=gemini_api_key)

class BrainstormingAgent:
    def __init__(self):
        self.model = "gemma2-9b-it"

    def generate_log_line(self, topic):
        prompt = f"Generate a log line and characters for a story based on the topic: '{topic}'. Use Blake Snyder's format: On the verge of a stasis=death moment, a flawed protagonist has a catalyst and breaks into Act Two; but when the midpoint happens, they must learn the theme stated, before Act Three leads to the finale where the flawed protagonist defeats (or doesn't defeat) the antagonistic force."
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert storyteller."},
                {"role": "user", "content": prompt}
            ],
            model=self.model,
        )
        return completion.choices[0].message.content

class StoryStructureAgent:
    def __init__(self):
        self.model = "llama-3.1-70b-versatile"

    def generate_5_act_structure(self, log_line):
        prompt = f'''Based on this log line: '{log_line}', generate a detailed 5-act story structure. 
        create a detailed character profile for each character in the story.
        For each act, provide 3-5 chapters, and for each chapter, provide a brief description.
        
        Format:
        Act 1: Exposition
        - Chapter 1: [Brief description]
        - Chapter 2: [Brief description]
        - Chapter 3: [Brief description]
        (Continue for Acts 2-5)'''

        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert story structure creator."},
                {"role": "user", "content": prompt}
            ],
            model=self.model,
        )
        return completion.choices[0].message.content

class SceneCreationAgent:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_chapter_scenes(self, act_structure, act_number, chapter_number):
        prompt = f'''
        Based on this 5-act story structure:
        {act_structure}
        
        Generate 3 detailed scenes for Act {act_number}, Chapter {chapter_number}. 
        For each scene, provide:
        1. Scene setting
        2. Characters involved
        3. Main action or conflict
        4. Outcome or cliffhanger
        
        Format:
        Scene 1:
        [Scene details]

        Scene 2:
        [Scene details]

        Scene 3:
        [Scene details]
        '''
        response = self.model.generate_content(prompt)
        return response.text

    def generate_scene(self, act_structure, act_number, chapter_number, scene_number):
        prompt = f'''
        Based on this 5-act story structure:
        {act_structure}
        
        Generate a detailed scene for Act {act_number}, Chapter {chapter_number}, Scene {scene_number}. 
        Include:
        1. Vivid description of the setting
        2. Character interactions and dialogue
        3. Conflict or tension in the scene
        4. How this scene advances the overall plot
        
        Aim for 3-5 paragraphs of engaging, show-don't-tell storytelling.
        '''
        response = self.model.generate_content(prompt)
        return response.text
