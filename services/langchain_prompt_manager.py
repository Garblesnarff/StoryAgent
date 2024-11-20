from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.prompts.example_selector import LengthBasedExampleSelector
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_community.cache import SQLiteCache
import logging
from typing import Dict, List, Optional
import json
import os

logger = logging.getLogger(__name__)

class LangChainPromptManager:
    def __init__(self):
        # Initialize caching with SQLite for persistence
        cache_dir = ".cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        self.cache = SQLiteCache(database_path=f"{cache_dir}/prompt_cache.db")
        
        # Initialize example data for few-shot learning
        self._init_example_data()
        # Initialize base templates
        self._init_image_prompt_template()
        self._init_story_prompt_template()
        # Initialize structured output parser
        self._init_output_parser()
        
    def _init_example_data(self):
        """Initialize example data for few-shot learning with rich descriptions"""
        self.image_prompt_examples = [
            {
                "story_context": "A mysterious forest where ancient magic exists",
                "paragraph_text": "The ancient trees whispered secrets to those who listened, their gnarled branches reaching like fingers through the misty air",
                "image_prompt": "A mystical forest scene with towering ancient trees, twisted bark textures visible in detail. Ethereal mist weaves between trunks, creating depth. Dappled sunlight filters through a dense emerald canopy, casting mysterious shadows. Hints of magical energy manifest as subtle, glowing particles in the air. Low-angle perspective emphasizing the trees' majesty. Soft, diffused lighting creates a dreamy atmosphere."
            },
            {
                "story_context": "A futuristic cyberpunk metropolis",
                "paragraph_text": "Neon lights reflected off the chrome buildings, painting the streets in vibrant colors while hover-cars streamed between the towering structures",
                "image_prompt": "A high-angle view of a cyberpunk cityscape at night. Gleaming chrome skyscrapers with distinct architectural details. Multiple layers of neon signs in blues, purples, and reds cast colorful reflections on wet streets. Streams of hover vehicles with visible light trails weave between buildings. Volumetric lighting effects show light pollution in the air. Detailed urban elements include floating advertisements and holographic displays."
            },
            {
                "story_context": "A serene coastal sunset",
                "paragraph_text": "Waves lapped gently against the shore as the sun dipped below the horizon, painting the sky in brilliant shades of gold and crimson",
                "image_prompt": "A panoramic coastal scene during golden hour. Detailed water surface with gentle ripples catching golden light. Dramatic sky with layered clouds in rich golds, oranges, and crimsons. Sun positioned low on horizon creating long reflections on water. Beach texture visible with small shells and subtle sand patterns. Atmospheric perspective showing distance through color gradation. Composition follows rule of thirds with horizon line placement."
            }
        ]
        
        # Initialize example selector with improved matching
        self.example_selector = LengthBasedExampleSelector(
            examples=self.image_prompt_examples,
            example_prompt=PromptTemplate(
                input_variables=["story_context", "paragraph_text", "image_prompt"],
                template="Story Context: {story_context}\nParagraph: {paragraph_text}\nImage Prompt: {image_prompt}"
            ),
            max_length=3000
        )
        
    def _init_output_parser(self):
        """Initialize structured output parser with comprehensive schema"""
        self.response_schemas = [
            ResponseSchema(
                name="visual_elements",
                description="Key visual elements to be included in the scene, including main subjects, background elements, and important details"
            ),
            ResponseSchema(
                name="composition",
                description="Specific composition guidelines including perspective, framing, focal points, and use of rule of thirds"
            ),
            ResponseSchema(
                name="lighting",
                description="Detailed lighting information including main light sources, shadows, highlights, and any special lighting effects"
            ),
            ResponseSchema(
                name="color_palette",
                description="Primary and secondary colors to be used, including specific mood-enhancing color combinations"
            ),
            ResponseSchema(
                name="atmosphere",
                description="Overall mood and atmosphere including weather, time of day, and environmental effects"
            ),
            ResponseSchema(
                name="artistic_style",
                description="Specific artistic style guidelines including texture details, brush stroke suggestions, and rendering technique preferences"
            ),
            ResponseSchema(
                name="technical_details",
                description="Additional technical specifications including depth of field, motion effects, and post-processing suggestions"
            )
        ]
        self.output_parser = StructuredOutputParser.from_response_schemas(self.response_schemas)
        
    def _init_image_prompt_template(self):
        """Initialize the image prompt template with enhanced instructions"""
        example_prompt = PromptTemplate(
            input_variables=["story_context", "paragraph_text", "image_prompt"],
            template="Story Context: {story_context}\nParagraph: {paragraph_text}\nImage Prompt: {image_prompt}"
        )
        
        self.image_prompt_template = FewShotPromptTemplate(
            example_selector=self.example_selector,
            example_prompt=example_prompt,
            prefix="""Generate a detailed artistic image prompt that captures the essence of a paragraph while maintaining consistency with the overall story. Follow this structured approach:

1. Visual Analysis:
   - Identify primary and secondary subjects
   - Note key environmental elements
   - List important details that establish context

2. Compositional Planning:
   - Determine optimal perspective and viewing angle
   - Plan foreground, midground, and background elements
   - Consider framing and focal points

3. Atmospheric Elements:
   - Define the lighting scenario and its effects
   - Plan color palette and mood
   - Include environmental effects (weather, time of day, etc.)

4. Technical Specifications:
   - Specify artistic style and rendering approach
   - Include camera-like parameters (depth of field, motion effects)
   - Note any special effects or post-processing needs

Follow these detailed examples:""",
            suffix="""Now, generate a comprehensive image prompt for:

Story Context: {story_context}

Current Paragraph: {paragraph_text}

Your prompt must include:
1. Detailed description of all visual elements
2. Specific composition guidelines
3. Comprehensive lighting setup
4. Clear color palette choices
5. Atmospheric details
6. Artistic style specifications
7. Technical requirements

Structure your response according to these requirements:
{format_instructions}""",
            input_variables=["story_context", "paragraph_text", "format_instructions"]
        )
        
    def _init_story_prompt_template(self):
        """Initialize the story generation template with enhanced structure"""
        self.story_prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert storyteller who carefully plans and structures narratives.
            Follow a methodical approach to story creation:
            1. Plan the story arc
            2. Develop character motivations
            3. Create vivid scenes
            4. Maintain consistent pacing"""),
            ("user", """Create a compelling {genre} story with a {mood} mood tailored for a {target_audience} audience.
            
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
            """)
        ])
        
    def format_image_prompt(self, story_context: str, paragraph_text: str) -> str:
        """Format an image generation prompt using the template with validation and caching"""
        cache_key = f"{story_context}:{paragraph_text}"
        
        try:
            cached_result = self.cache.lookup(cache_key)
            if cached_result:
                return cached_result
                
            format_instructions = self.output_parser.get_format_instructions()
            prompt = self.image_prompt_template.format(
                story_context=story_context,
                paragraph_text=paragraph_text,
                format_instructions=format_instructions
            )
            validated_prompt = self._validate_prompt(prompt)
            self.cache.update(cache_key, validated_prompt)
            return validated_prompt
        except Exception as e:
            logger.error(f"Error formatting image prompt: {str(e)}")
            return self._validate_prompt(paragraph_text)
            
    def format_story_prompt(self, genre: str, mood: str, target_audience: str, 
                          prompt: str, paragraphs: int) -> str:
        """Format a story generation prompt using the template with validation and caching"""
        cache_key = f"{genre}:{mood}:{target_audience}:{prompt}:{paragraphs}"
        
        try:
            cached_result = self.cache.lookup(cache_key)
            if cached_result:
                return cached_result
                
            prompt = self.story_prompt_template.format(
                genre=genre,
                mood=mood,
                target_audience=target_audience,
                prompt=prompt,
                paragraphs=paragraphs
            )
            validated_prompt = self._validate_prompt(prompt)
            self.cache.update(cache_key, validated_prompt)
            return validated_prompt
        except Exception as e:
            logger.error(f"Error formatting story prompt: {str(e)}")
            return self._validate_prompt(prompt)
            
    def _validate_prompt(self, prompt: str) -> str:
        """Validate and clean the generated prompt with enhanced checks"""
        if not prompt or len(prompt.strip()) < 10:
            raise ValueError("Generated prompt is too short or empty")
            
        # Remove excessive whitespace
        prompt = " ".join(prompt.split())
        
        # Check for common formatting issues
        if prompt.count('{') != prompt.count('}'):
            raise ValueError("Mismatched template brackets in prompt")
            
        # Ensure proper sentence structure
        sentences = prompt.split('. ')
        if any(len(s.split()) < 3 for s in sentences if s):
            logger.warning("Some sentences may be too short")
            
        # Ensure prompt ends with proper punctuation
        if not prompt.strip()[-1] in ".!?":
            prompt = prompt.strip() + "."
            
        return prompt
        
    def get_prompt_feedback(self) -> Dict[str, List[str]]:
        """Get statistics and feedback about prompt usage"""
        return {
            "cache_hits": self.cache.get_stats() if hasattr(self.cache, 'get_stats') else {},
            "common_errors": logger.getEffectiveLevel()
        }
