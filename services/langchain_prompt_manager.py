from langchain.prompts import PromptTemplate
from langchain.prompts import FewShotPromptTemplate
from langchain.prompts.example_selector import LengthBasedExampleSelector
import logging

logger = logging.getLogger(__name__)

class LangChainPromptManager:
    def __init__(self):
        # Initialize base templates
        self._init_image_prompt_template()
        self._init_story_prompt_template()
        
    def _init_image_prompt_template(self):
        """Initialize the image prompt template"""
        self.image_prompt_template = PromptTemplate(
            input_variables=["story_context", "paragraph_text"],
            template="""
            Given the following story context and a specific paragraph, generate an artistic image prompt
            that captures the essence of the paragraph while maintaining consistency with the overall story.
            
            Story Context:
            {story_context}
            
            Current Paragraph:
            {paragraph_text}
            
            Generate a detailed image prompt that:
            1. Captures the key visual elements from the paragraph
            2. Maintains the story's atmosphere and tone
            3. Includes specific details about lighting, perspective, and mood
            4. Uses artistic and descriptive language
            """
        )
        
    def _init_story_prompt_template(self):
        """Initialize the story generation template"""
        self.story_prompt_template = PromptTemplate(
            input_variables=["genre", "mood", "target_audience", "prompt", "paragraphs"],
            template="""
            Write a {genre} story with a {mood} mood for a {target_audience} audience based on this prompt: {prompt}.
            Create {paragraphs} distinct paragraphs where each naturally flows from the previous one.
            The story should follow the 3 act format.
            
            Requirements:
            1. Each paragraph should be 2-3 sentences
            2. Do not include any segment markers, numbers, or labels
            3. The story should read as one continuous narrative
            4. Maintain consistent tone and pacing throughout
            5. Ensure proper story arc with setup, conflict, and resolution
            """
        )
        
    def format_image_prompt(self, story_context: str, paragraph_text: str) -> str:
        """Format an image generation prompt using the template"""
        try:
            return self.image_prompt_template.format(
                story_context=story_context,
                paragraph_text=paragraph_text
            )
        except Exception as e:
            logger.error(f"Error formatting image prompt: {str(e)}")
            return paragraph_text
            
    def format_story_prompt(self, genre: str, mood: str, target_audience: str, 
                          prompt: str, paragraphs: int) -> str:
        """Format a story generation prompt using the template"""
        try:
            return self.story_prompt_template.format(
                genre=genre,
                mood=mood,
                target_audience=target_audience,
                prompt=prompt,
                paragraphs=paragraphs
            )
        except Exception as e:
            logger.error(f"Error formatting story prompt: {str(e)}")
            return prompt
