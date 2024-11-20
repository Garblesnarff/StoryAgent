from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.prompts.example_selector import LengthBasedExampleSelector
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_community.cache import SQLAlchemyCache
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from sqlalchemy import create_engine
import logging
from typing import Dict, List, Optional
import json
import os
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class LangChainPromptManager:
    def __init__(self):
        # Initialize Gemini LLM
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                temperature=0.7,
                google_api_key=os.environ.get('GOOGLE_API_KEY')
            )
            logger.info("Successfully initialized Gemini LLM")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini LLM: {str(e)}")
            raise

        # Initialize conversation memory with extended context
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output",
            input_key="input"
        )

        # Initialize style memory
        self.current_style = None
        self.style_elements = {}

        # Initialize caching with SQLAlchemyCache
        try:
            database_url = os.environ.get('DATABASE_URL')
            if database_url:
                engine = create_engine(database_url)
                self.cache = SQLAlchemyCache(engine=engine)
                logger.info("Successfully initialized SQLAlchemyCache")
            else:
                logger.warning("No DATABASE_URL found, proceeding without caching")
                self.cache = None
        except Exception as e:
            logger.warning(f"Failed to initialize SQLAlchemyCache: {str(e)}, proceeding without caching")
            self.cache = None
        
        self.llm_string = "gemini_pro"
        
        # Initialize example data for few-shot learning
        self._init_example_data()
        # Initialize output parser
        self._init_output_parser()
        # Initialize base templates
        self._init_image_prompt_template()

    def _init_output_parser(self):
        """Initialize structured output parser with enhanced schemas"""
        response_schemas = [
            ResponseSchema(
                name="visual_description",
                description="Detailed description of the visual elements, including subjects, environment, and key details"
            ),
            ResponseSchema(
                name="composition",
                description="Guidelines for image composition, including perspective, framing, and focal points"
            ),
            ResponseSchema(
                name="lighting",
                description="Lighting setup details including type, direction, and effects"
            ),
            ResponseSchema(
                name="color_palette",
                description="Specific color choices and their relationships"
            ),
            ResponseSchema(
                name="atmosphere",
                description="Atmospheric elements like weather, time of day, and mood"
            ),
            ResponseSchema(
                name="style",
                description="Artistic style specifications and rendering approach"
            ),
            ResponseSchema(
                name="technical_requirements",
                description="Technical specifications like camera parameters and special effects"
            )
        ]
        
        self.output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

    def _update_style_memory(self, style: str, parsed_response: dict):
        """Update style memory to maintain consistency"""
        self.current_style = style
        self.style_elements.update({
            'color_palette': parsed_response.get('color_palette', ''),
            'lighting': parsed_response.get('lighting', ''),
            'atmosphere': parsed_response.get('atmosphere', ''),
            'style': parsed_response.get('style', '')
        })

    def _get_style_context(self) -> str:
        """Get formatted style context from memory"""
        if not self.current_style:
            return ""
        
        return f"""
Previous Style Elements:
Color Palette: {self.style_elements.get('color_palette', '')}
Lighting: {self.style_elements.get('lighting', '')}
Atmosphere: {self.style_elements.get('atmosphere', '')}
Style: {self.style_elements.get('style', '')}
"""

    def _get_conversation_context(self) -> str:
        """Get formatted conversation history from memory"""
        messages = self.memory.load_memory_variables({})
        history = messages.get("chat_history", [])
        
        if not history:
            return ""
            
        formatted_history = "\n".join([
            f"Previous {'Input' if i % 2 == 0 else 'Output'}: {msg.content}"
            for i, msg in enumerate(history[-4:])  # Keep last 2 interactions (4 messages)
        ])
        
        return f"\nConversation History:\n{formatted_history}"

    def format_image_prompt(self, story_context: str, paragraph_text: str, style: str = None) -> str:
        """Format an image generation prompt using the template with conversation memory"""
        try:
            prompt_key = f"{story_context}:{paragraph_text}:{style}"
            
            # Try to get cached result if cache is available
            if self.cache:
                try:
                    cached_result = self.cache.lookup(prompt_key, self.llm_string)
                    if cached_result:
                        logger.info("Cache hit for image prompt")
                        parsed_cached = self.output_parser.parse(cached_result)
                        self._update_style_memory(style, parsed_cached)
                        
                        # Store the cached result in conversation memory
                        self.memory.save_context(
                            {"input": f"Story Context: {story_context}\nParagraph: {paragraph_text}"},
                            {"output": cached_result}
                        )
                        return cached_result
                except Exception as cache_error:
                    logger.warning(f"Cache lookup failed: {str(cache_error)}")
            
            # Get conversation and style context
            conversation_context = self._get_conversation_context()
            style_context = self._get_style_context()
            
            # Generate new prompt using Gemini LLM
            format_instructions = self.output_parser.get_format_instructions()
            prompt = self.image_prompt_template.format(
                story_context=story_context,
                paragraph_text=paragraph_text,
                style=style or self.current_style or "realistic",
                conversation_history=conversation_context,
                style_context=style_context,
                format_instructions=format_instructions
            )
            
            response = self.llm.invoke(prompt).content
            parsed_response = self.output_parser.parse(response)
            
            # Update style memory with new generation
            self._update_style_memory(style, parsed_response)
            
            # Store the interaction in conversation memory
            self.memory.save_context(
                {"input": f"Story Context: {story_context}\nParagraph: {paragraph_text}"},
                {"output": response}
            )
            
            # Update cache if available
            if self.cache:
                try:
                    self.cache.update(prompt_key, self.llm_string, response)
                    logger.info("Cache updated with new image prompt")
                except Exception as cache_error:
                    logger.warning(f"Cache update failed: {str(cache_error)}")
            
            return self._validate_prompt(response)
            
        except Exception as e:
            logger.error(f"Error in format_image_prompt: {str(e)}")
            return self._validate_prompt(paragraph_text)

    def _init_image_prompt_template(self):
        """Initialize the image prompt template with enhanced instructions"""
        example_prompt = PromptTemplate(
            input_variables=["story_context", "paragraph_text", "image_prompt"],
            template="Story Context: {story_context}\nParagraph: {paragraph_text}\nImage Prompt: {image_prompt}"
        )
        
        self.image_prompt_template = FewShotPromptTemplate(
            example_selector=LengthBasedExampleSelector(
                examples=self.image_prompt_examples,
                example_prompt=example_prompt,
                max_length=2000
            ),
            example_prompt=example_prompt,
            prefix="""Generate a detailed artistic image prompt that captures the essence of a paragraph while maintaining visual consistency with previous generations. Consider:

1. Visual Analysis:
   - Identify primary and secondary subjects
   - Note key environmental elements
   - List important details that establish context

2. Style Consistency:
   - Maintain consistent artistic style
   - Use complementary color palettes
   - Keep lighting and atmosphere coherent

3. Previous Context:
{style_context}

4. Conversation History:
{conversation_history}

Current Request:""",
            suffix="Based on the above context and examples, generate a detailed image prompt following the format instructions:\n{format_instructions}",
            input_variables=["story_context", "paragraph_text", "style", "conversation_history", "style_context", "format_instructions"]
        )

    def _validate_prompt(self, response: str) -> str:
        """Validate and format the generated prompt"""
        try:
            parsed_response = self.output_parser.parse(response)
            
            formatted_prompt = f"""
{parsed_response['visual_description']}

Composition:
{parsed_response['composition']}

Lighting:
{parsed_response['lighting']}

Color Palette:
{parsed_response['color_palette']}

Atmosphere:
{parsed_response['atmosphere']}

Style:
{parsed_response['style']}

Technical Requirements:
{parsed_response['technical_requirements']}
""".strip()
            
            return formatted_prompt
        except Exception as e:
            logger.error(f"Error parsing prompt response: {str(e)}")
            return response

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
                "image_prompt": "A crowded cyberpunk street scene at night. Towering holographic advertisements project through sheets of neon-tinted rain. Chrome cybernetic augmentations reflect colorful light. Multiple layers of depth with foreground crowds and background cityscape. Atmospheric effects include rain droplets, steam, and lens flare. Moody lighting emphasizes the contrast between dark shadows and bright neon. Technical details include precise reflections and particle effects."
            }
        ]

    def validate_media_url(self, url: str, media_type: str = 'image') -> bool:
        """Validate media URL format and accessibility"""
        try:
            if not url:
                return False
                
            parsed_url = urlparse(url)
            
            # Check if URL has proper scheme and path
            if not all([parsed_url.scheme, parsed_url.path]):
                logger.warning(f"Invalid {media_type} URL format: {url}")
                return False
                
            # Validate file extension based on media type
            valid_extensions = {
                'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
                'audio': ['.wav', '.mp3', '.ogg']
            }
            
            file_ext = os.path.splitext(parsed_url.path)[1].lower()
            if file_ext not in valid_extensions.get(media_type, []):
                logger.warning(f"Invalid {media_type} file extension: {file_ext}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating {media_type} URL: {str(e)}")
            return False

    def _process_media_urls(self, response: str) -> Dict:
        """Extract and validate media URLs from response"""
        try:
            # Extract URLs using regex
            image_urls = re.findall(r'https?://[^\s<>"]+?(?:jpg|jpeg|png|gif|webp)', response)
            audio_urls = re.findall(r'https?://[^\s<>"]+?(?:wav|mp3|ogg)', response)
            
            # Validate URLs
            valid_image_urls = [url for url in image_urls if self.validate_media_url(url, 'image')]
            valid_audio_urls = [url for url in audio_urls if self.validate_media_url(url, 'audio')]
            
            if valid_image_urls:
                logger.info(f"Found valid image URLs: {len(valid_image_urls)}")
            if valid_audio_urls:
                logger.info(f"Found valid audio URLs: {len(valid_audio_urls)}")
                
            return {
                'image_urls': valid_image_urls,
                'audio_urls': valid_audio_urls
            }
            
        except Exception as e:
            logger.error(f"Error processing media URLs: {str(e)}")
            return {'image_urls': [], 'audio_urls': []}

    def format_image_prompt(self, story_context: str, paragraph_text: str) -> str:
        """Format an image generation prompt using the template with SQLAlchemy caching"""
        try:
            prompt_key = f"{story_context}:{paragraph_text}"
            
            # Try to get cached result if cache is available
            if self.cache:
                try:
                    cached_result = self.cache.lookup(prompt_key, self.llm_string)
                    if cached_result:
                        logger.info("Cache hit for image prompt")
                        # Validate cached media URLs
                        media_urls = self._process_media_urls(cached_result)
                        if media_urls['image_urls'] or media_urls['audio_urls']:
                            return cached_result
                        else:
                            logger.warning("Cached result contains invalid media URLs")
                except Exception as cache_error:
                    logger.warning(f"Cache lookup failed: {str(cache_error)}")
            
            # Generate new prompt using Gemini LLM
            format_instructions = self.output_parser.get_format_instructions()
            prompt = self.image_prompt_template.format(
                story_context=story_context,
                paragraph_text=paragraph_text,
                format_instructions=format_instructions
            )
            
            # Use invoke instead of predict
            response = self.llm.invoke(prompt).content
            
            # Validate response and media URLs
            validated_prompt = self._validate_prompt(response)
            media_urls = self._process_media_urls(validated_prompt)
            
            if not (media_urls['image_urls'] or media_urls['audio_urls']):
                logger.warning("Generated prompt contains no valid media URLs")
            
            # Update cache if available
            if self.cache and (media_urls['image_urls'] or media_urls['audio_urls']):
                try:
                    self.cache.update(prompt_key, self.llm_string, validated_prompt)
                    logger.info("Cache updated with new image prompt")
                except Exception as cache_error:
                    logger.warning(f"Cache update failed: {str(cache_error)}")
            
            return validated_prompt
            
        except Exception as e:
            logger.error(f"Error in format_image_prompt: {str(e)}")
            return self._validate_prompt(paragraph_text)

    def _init_example_data(self):
        """Initialize example data for few-shot learning with rich descriptions"""
        self.image_prompt_examples = [
            # Existing examples
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
            },
            # New examples with diverse artistic styles
            {
                "story_context": "A martial arts epic set in ancient China",
                "paragraph_text": "The master's brush danced across the scroll, each stroke flowing like water, capturing the essence of movement in eternal ink",
                "image_prompt": "A scene rendered in Dynamic Ink Wash Motion style, with fluid brushstrokes capturing swift movements. Utilize bold black and deep crimson inks to create contrast and dynamism. The composition shows a traditional Chinese study with scrolls and calligraphy materials. Emphasis on the graceful movement of the brush and the way ink flows across rice paper. Atmospheric elements include subtle ink spatters and gradient washes that suggest depth and energy."
            },
            {
                "story_context": "A surreal journey through consciousness",
                "paragraph_text": "Reality rippled and warped as the boundaries between senses blurred, transforming simple sounds into vivid colors and textures into tastes",
                "image_prompt": "A Reverse Polarized Synesthesia Fusion scene, where sensory experiences blend and transform in unexpected ways. Employ solarized purple and electric blue to represent the merging of different perceptual modalities. Abstract forms flow and interweave, suggesting the transformation of sound waves into color patterns. Multiple layers of transparency create depth and dimension. Inclusion of geometric patterns that seem to pulse and shift. Edge effects suggest the boundaries between different sensory experiences."
            },
            {
                "story_context": "A post-apocalyptic survival story",
                "paragraph_text": "Through the radioactive haze, the skeletal remains of the city's techno-organic architecture loomed, its once-pristine surfaces now corrupted by decades of digital decay",
                "image_prompt": "A Halftone Mechanical Blueprint scene, combining technical schematics with halftone textures. Utilize industrial steel blue and corroded copper tones to highlight the mechanical intricacies. Architectural elements show both organic growth patterns and geometric precision. Degraded digital artifacts and glitch effects suggest technological decay. Multiple layers of technical drawings overlap with varying opacity. Inclusion of mathematical formulae and engineering notations as background elements. Perspective emphasizes the massive scale of the deteriorating structures."
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

    def set_llm_string(self, llm_string: str):
        """Update the LLM string used for cache lookups"""
        self.llm_string = llm_string
        
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
        
    def format_story_prompt(self, genre: str, mood: str, target_audience: str, 
                          prompt: str, paragraphs: int) -> str:
        """Format a story generation prompt using the template with SQLAlchemy caching"""
        try:
            prompt_key = f"{genre}:{mood}:{target_audience}:{prompt}:{paragraphs}"
            
            # Try to get cached result if cache is available
            if self.cache:
                try:
                    cached_result = self.cache.lookup(prompt_key, self.llm_string)
                    if cached_result:
                        logger.info("Cache hit for story prompt")
                        return cached_result
                except Exception as cache_error:
                    logger.warning(f"Cache lookup failed: {str(cache_error)}")
            
            # Generate new prompt
            response = self.story_prompt_template.format(
                genre=genre,
                mood=mood,
                target_audience=target_audience,
                prompt=prompt,
                paragraphs=paragraphs
            )
            
            # Update cache if available
            if self.cache:
                try:
                    self.cache.update(prompt_key, self.llm_string, response)
                    logger.info("Cache updated with new story prompt")
                except Exception as cache_error:
                    logger.warning(f"Cache update failed: {str(cache_error)}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in format_story_prompt: {str(e)}")
            return prompt

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
                "cache_hits": len(self.cache._cache) if self.cache and hasattr(self.cache, '_cache') else 0,
                "common_errors": logger.getEffectiveLevel(),
                "cache_size": len(self.cache._cache) if self.cache and hasattr(self.cache, '_cache') else 0
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting prompt feedback: {str(e)}")
            return {
                "cache_hits": 0,
                "common_errors": logger.getEffectiveLevel(),
                "cache_size": 0
            }