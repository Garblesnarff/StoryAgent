from utils.ai_agents import BrainstormingAgent, StoryStructureAgent, SceneCreationAgent
import logging

logging.basicConfig(level=logging.INFO)

brainstorming_agent = BrainstormingAgent()
story_structure_agent = StoryStructureAgent()
scene_creation_agent = SceneCreationAgent()

def generate_book_spec(topic):
    logging.info(f"Generating book specification for topic: {topic}")
    log_line = brainstorming_agent.generate_log_line(topic)
    book_spec = f"Topic: {topic}\nLog Line: {log_line}"
    logging.info("Book specification generated successfully")
    return book_spec

def generate_outline(book_spec):
    logging.info("Generating story outline")
    log_line = book_spec.split("Log Line: ")[1]
    outline = story_structure_agent.generate_5_act_structure(log_line)
    logging.info("Story outline generated successfully")
    return outline

def generate_scene(book_spec, outline, act, chapter, scene_number):
    logging.info(f"Generating scene for Act {act}, Chapter {chapter}, Scene {scene_number}")
    scene_content = scene_creation_agent.generate_scene(outline, act, chapter, scene_number)
    paragraphs = [p.strip() for p in scene_content.split('\n\n') if p.strip()]
    logging.info(f"Generated {len(paragraphs)} paragraphs for the scene")
    return paragraphs

def generate_chapter_scenes(book_spec, outline, act, chapter):
    logging.info(f"Generating scenes for Act {act}, Chapter {chapter}")
    scenes = scene_creation_agent.generate_chapter_scenes(outline, act, chapter)
    logging.info(f"Generated scenes for Chapter {chapter}")
    return scenes
