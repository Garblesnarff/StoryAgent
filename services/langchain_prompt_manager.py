from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.prompts.example_selector import LengthBasedExampleSelector
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_community.cache import InMemoryCache
import logging
from typing import Dict, List, Optional
import json
import os

logger = logging.getLogger(__name__)

class LangChainPromptManager:
    def __init__(self):
        # Initialize caching with InMemoryCache and llm parameters
        self.cache = InMemoryCache()
        self.llm_string = "default_llm"  # Can be updated based on LLM configuration
        
        # Initialize example data for few-shot learning
        self._init_example_data()
        # Initialize base templates
        self._init_image_prompt_template()
        self._init_story_prompt_template()
        # Initialize structured output parser
        self._init_output_parser()
        
    def set_llm_string(self, llm_string: str):
        """Update the LLM string used for cache lookups"""
        self.llm_string = llm_string
        
    def _init_example_data(self):
        """Initialize example data for few-shot learning with rich descriptions"""
        self.image_prompt_examples = [
            {
                "story_context": "An epic fantasy tale of ancient magic and prophecy",
                "paragraph_text": "The crystal spires of the ancient citadel pierced the clouds, their surfaces reflecting the dawn's golden light while arcane symbols pulsed with ethereal energy",
                "image_prompt": "A majestic fantasy cityscape with towering crystal spires reaching into a dawn sky. Architecture features intricate geometric patterns and flowing organic forms. Glowing arcane symbols float and pulse with blue-white energy around the spires. Dramatic lighting with golden sunlight catching and refracting through the crystal structures. Low-angle perspective emphasizing scale and grandeur. Atmospheric effects include wispy clouds and lens flares. Fine details show the crystalline texture and magical energy patterns."
            },
            {
                "story_context": "A dark cyberpunk thriller in a rain-soaked metropolis",
                "paragraph_text": "Holographic advertisements flickered through the acid rain, casting their neon reflections across the chrome-plated augmentations of the crowd below",
                "image_prompt": "A densely packed cyberpunk street scene at night. Multiple layers of holographic advertisements with visible glitch effects and distortions. Acid rain creates streaks of neon reflections on various metallic surfaces. Crowd of people with visible cybernetic augmentations, chrome plating catching colored lights. Deep atmospheric perspective with multiple light sources. Volumetric lighting effects show rain and steam rising. Technical details include high contrast ratio and subtle chromatic aberration effects."
            },
            {
                "story_context": "A psychological horror set in an abandoned Victorian mansion",
                "paragraph_text": "Shadows danced across the peeling wallpaper as the ancient grandfather clock struck midnight, its chimes echoing through empty corridors lined with portraits whose eyes seemed to follow every movement",
                "image_prompt": "Interior of a decaying Victorian mansion with dramatic shadows and lighting. Detailed textures of peeling wallpaper with visible patterns and aging effects. Ornate grandfather clock with intricate mechanical details and brass accents. Multiple portrait paintings with period-appropriate frames and subtle uncanny valley effects in the eyes. Dust particles visible in light beams. Composition emphasizes depth through a long corridor perspective. Color palette focuses on deep shadows and warm accent lighting."
            }
        ]
        
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
        """Format an image generation prompt using the template with improved caching"""
        cache_key = f"{self.llm_string}:{story_context}:{paragraph_text}"
        
        try:
            # Try to get the cached result with llm_string parameter
            cached_result = self.cache.lookup(key=cache_key, llm_string=self.llm_string)
            if cached_result:
                logger.info(f"Cache hit for image prompt with key: {cache_key}")
                return cached_result
                
            # Generate new prompt if cache miss
            format_instructions = self.output_parser.get_format_instructions()
            prompt = self.image_prompt_template.format(
                story_context=story_context,
                paragraph_text=paragraph_text,
                format_instructions=format_instructions
            )
            validated_prompt = self._validate_prompt(prompt)
            
            # Update cache with the new prompt
            self.cache.update(key=cache_key, value=validated_prompt, llm_string=self.llm_string)
            logger.info(f"Cache updated with new image prompt for key: {cache_key}")
            return validated_prompt
            
        except Exception as e:
            logger.error(f"Error in format_image_prompt: {str(e)}")
            # Fallback to direct prompt generation without caching
            try:
                return self._validate_prompt(paragraph_text)
            except Exception as fallback_error:
                logger.error(f"Fallback error in format_image_prompt: {str(fallback_error)}")
                return paragraph_text
            
    def format_story_prompt(self, genre: str, mood: str, target_audience: str, 
                          prompt: str, paragraphs: int) -> str:
        """Format a story generation prompt using the template with improved caching"""
        cache_key = f"{self.llm_string}:{genre}:{mood}:{target_audience}:{prompt}:{paragraphs}"
        
        try:
            # Try to get the cached result with llm_string parameter
            cached_result = self.cache.lookup(key=cache_key, llm_string=self.llm_string)
            if cached_result:
                logger.info(f"Cache hit for story prompt with key: {cache_key}")
                return cached_result
                
            # Generate new prompt if cache miss
            prompt = self.story_prompt_template.format(
                genre=genre,
                mood=mood,
                target_audience=target_audience,
                prompt=prompt,
                paragraphs=paragraphs
            )
            validated_prompt = self._validate_prompt(prompt)
            
            # Update cache with the new prompt
            self.cache.update(key=cache_key, value=validated_prompt, llm_string=self.llm_string)
            logger.info(f"Cache updated with new story prompt for key: {cache_key}")
            return validated_prompt
            
        except Exception as e:
            logger.error(f"Error in format_story_prompt: {str(e)}")
            # Fallback to direct prompt generation without caching
            try:
                return self._validate_prompt(prompt)
            except Exception as fallback_error:
                logger.error(f"Fallback error in format_story_prompt: {str(fallback_error)}")
                return prompt

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
        try:
            stats = {
                "cache_hits": len([k for k in self.cache._cache.keys()]),
                "common_errors": logger.getEffectiveLevel(),
                "cache_size": len(self.cache._cache)
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting prompt feedback: {str(e)}")
            return {
                "cache_hits": 0,
                "common_errors": logger.getEffectiveLevel(),
                "cache_size": 0
            }