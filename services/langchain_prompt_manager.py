from langchain.prompts import PromptTemplate
from langchain.prompts import FewShotPromptTemplate
from langchain.prompts.example_selector import LengthBasedExampleSelector
import logging

logger = logging.getLogger(__name__)

class LangChainPromptManager:
    def __init__(self):
        # Initialize example data for few-shot learning
        self._init_example_data()
        # Initialize base templates
        self._init_image_prompt_template()
        self._init_story_prompt_template()
        
    def _init_example_data(self):
        """Initialize example data for few-shot learning"""
        self.image_prompt_examples = [
            {
                "story_context": "A mysterious forest where magic exists",
                "paragraph_text": "The ancient trees whispered secrets to those who listened",
                "image_prompt": "A mystical forest scene with towering ancient trees, dappled sunlight filtering through dense canopy, creating an ethereal atmosphere with subtle hints of magical energy in the air."
            },
            {
                "story_context": "A futuristic city with advanced technology",
                "paragraph_text": "Neon lights reflected off the chrome buildings, painting the streets in vibrant colors",
                "image_prompt": "A high-angle view of a cyberpunk cityscape at night, with gleaming chrome skyscrapers, neon signs casting colorful reflections, and hover vehicles weaving between buildings."
            }
        ]
        
        # Initialize example selector
        self.example_selector = LengthBasedExampleSelector(
            examples=self.image_prompt_examples,
            example_prompt=PromptTemplate(
                input_variables=["story_context", "paragraph_text", "image_prompt"],
                template="Story Context: {story_context}\nParagraph: {paragraph_text}\nImage Prompt: {image_prompt}"
            ),
            max_length=2000
        )
        
    def _init_image_prompt_template(self):
        """Initialize the image prompt template with few-shot learning"""
        example_prompt = PromptTemplate(
            input_variables=["story_context", "paragraph_text", "image_prompt"],
            template="Story Context: {story_context}\nParagraph: {paragraph_text}\nImage Prompt: {image_prompt}"
        )
        
        self.image_prompt_template = FewShotPromptTemplate(
            example_selector=self.example_selector,
            example_prompt=example_prompt,
            prefix="""Generate an artistic image prompt that captures the essence of a paragraph while maintaining consistency with the overall story. Follow these examples:""",
            suffix="""Now, generate an image prompt for:

Story Context: {story_context}

Current Paragraph: {paragraph_text}

The prompt should:
1. Capture key visual elements
2. Maintain story atmosphere
3. Include specific details about lighting, perspective, and mood
4. Use artistic and descriptive language""",
            input_variables=["story_context", "paragraph_text"]
        )
        
    def _init_story_prompt_template(self):
        """Initialize the story generation template with enhanced structure"""
        self.story_prompt_template = PromptTemplate(
            input_variables=["genre", "mood", "target_audience", "prompt", "paragraphs"],
            template="""
            Create a compelling {genre} story with a {mood} mood tailored for a {target_audience} audience.
            
            Story Prompt: {prompt}
            Required Paragraphs: {paragraphs}
            
            Story Requirements:
            1. Follow a clear three-act structure:
               - Act 1: Setup and hook
               - Act 2: Rising action and conflict
               - Act 3: Resolution and conclusion
            
            2. Each paragraph should:
               - Contain 2-3 well-crafted sentences
               - Flow naturally from the previous one
               - Advance the story meaningfully
               - Maintain consistent tone and pacing
            
            3. Technical Guidelines:
               - Exclude segment markers or labels
               - Write as one continuous narrative
               - Ensure proper story arc
               - Use vivid, engaging language
               - Include sensory details where appropriate
            
            4. Emotional Elements:
               - Incorporate the specified mood throughout
               - Create emotional resonance for the target audience
               - Develop meaningful character moments
            """
        )
        
    def format_image_prompt(self, story_context: str, paragraph_text: str) -> str:
        """Format an image generation prompt using the template with validation"""
        try:
            prompt = self.image_prompt_template.format(
                story_context=story_context,
                paragraph_text=paragraph_text
            )
            return self._validate_prompt(prompt)
        except Exception as e:
            logger.error(f"Error formatting image prompt: {str(e)}")
            return self._validate_prompt(paragraph_text)
            
    def format_story_prompt(self, genre: str, mood: str, target_audience: str, 
                          prompt: str, paragraphs: int) -> str:
        """Format a story generation prompt using the template with validation"""
        try:
            prompt = self.story_prompt_template.format(
                genre=genre,
                mood=mood,
                target_audience=target_audience,
                prompt=prompt,
                paragraphs=paragraphs
            )
            return self._validate_prompt(prompt)
        except Exception as e:
            logger.error(f"Error formatting story prompt: {str(e)}")
            return self._validate_prompt(prompt)
            
    def _validate_prompt(self, prompt: str) -> str:
        """Validate and clean the generated prompt"""
        if not prompt or len(prompt.strip()) < 10:
            raise ValueError("Generated prompt is too short or empty")
        
        # Remove excessive whitespace
        prompt = " ".join(prompt.split())
        
        # Ensure prompt ends with proper punctuation
        if not prompt.strip()[-1] in ".!?":
            prompt = prompt.strip() + "."
            
        return prompt
