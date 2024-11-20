from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.prompts.example_selector import LengthBasedExampleSelector
from datetime import datetime
import logging
import json
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class LangChainPromptManager:
    def __init__(self):
        self.performance_metrics = []
        self._init_example_prompts()
        self._init_templates()
        
    def _init_example_prompts(self):
        """Initialize example prompts for few-shot learning"""
        self.image_examples = [
            {
                "story_context": "A fantasy tale about a young wizard discovering their powers",
                "paragraph_text": "The ancient spell book glowed with an ethereal blue light, casting dancing shadows on the library walls.",
                "image_prompt": "A dimly lit medieval library interior, an ornate spell book emanating ethereal blue light, creating dynamic shadows on ancient stone walls. Dust particles visible in the magical glow, leather-bound books lining wooden shelves. Atmospheric, mystical, detailed lighting effects."
            },
            {
                "story_context": "A sci-fi story about space exploration",
                "paragraph_text": "The massive starship engines hummed to life, their plasma cores pulsing with barely contained energy.",
                "image_prompt": "Close-up of futuristic starship engines with glowing blue-white plasma cores, industrial sci-fi aesthetic, metallic surfaces reflecting pulsing energy, steam vents, and power conduits. Dynamic lighting, deep shadows, high technical detail."
            }
        ]
        
    def _init_templates(self):
        """Initialize enhanced prompt templates with few-shot learning"""
        example_selector = LengthBasedExampleSelector(
            examples=self.image_examples,
            example_prompt=PromptTemplate(
                input_variables=["story_context", "paragraph_text", "image_prompt"],
                template="Story Context: {story_context}\nParagraph: {paragraph_text}\nImage Prompt: {image_prompt}"
            ),
            max_length=2
        )
        
        self.image_prompt_template = FewShotPromptTemplate(
            example_selector=example_selector,
            example_prompt=PromptTemplate(
                input_variables=["story_context", "paragraph_text", "image_prompt"],
                template="Story Context: {story_context}\nParagraph: {paragraph_text}\nImage Prompt: {image_prompt}"
            ),
            prefix="""Generate detailed image prompts that capture the essence of story paragraphs while maintaining consistency with the overall narrative. Study these examples:""",
            suffix="""Now, generate a similar detailed image prompt for:
Story Context: {story_context}
Paragraph: {paragraph_text}

The prompt should:
1. Capture key visual elements
2. Maintain story atmosphere
3. Include lighting and perspective details
4. Use artistic, descriptive language""",
            input_variables=["story_context", "paragraph_text"]
        )
        
        self.story_prompt_template = PromptTemplate(
            input_variables=["genre", "mood", "target_audience", "prompt", "paragraphs", "style_guide"],
            template="""
            Write a {genre} story with a {mood} mood for a {target_audience} audience based on this prompt: {prompt}.
            Create {paragraphs} distinct paragraphs following this style guide:
            {style_guide}
            
            Requirements:
            1. Each paragraph should be 2-3 sentences
            2. Maintain consistent tone and pacing
            3. Follow proper story arc (setup, conflict, resolution)
            4. Include vivid sensory details
            5. Ensure natural paragraph transitions
            """
        )
        
    def format_image_prompt(self, story_context: str, paragraph_text: str, track_performance: bool = True) -> str:
        """Format an image generation prompt using few-shot learning template"""
        try:
            start_time = datetime.now()
            prompt = self.image_prompt_template.format(
                story_context=story_context,
                paragraph_text=paragraph_text
            )
            
            if track_performance:
                self._track_performance("image_prompt", start_time, len(prompt))
                
            return prompt
        except Exception as e:
            logger.error(f"Error formatting image prompt: {str(e)}")
            self._track_error("image_prompt", str(e))
            return paragraph_text
            
    def format_story_prompt(self, genre: str, mood: str, target_audience: str, 
                          prompt: str, paragraphs: int, style_guide: Optional[str] = None) -> str:
        """Format a story generation prompt with enhanced styling"""
        try:
            start_time = datetime.now()
            formatted_prompt = self.story_prompt_template.format(
                genre=genre,
                mood=mood,
                target_audience=target_audience,
                prompt=prompt,
                paragraphs=paragraphs,
                style_guide=style_guide or "Follow standard narrative structure"
            )
            
            self._track_performance("story_prompt", start_time, len(formatted_prompt))
            return formatted_prompt
        except Exception as e:
            logger.error(f"Error formatting story prompt: {str(e)}")
            self._track_error("story_prompt", str(e))
            return prompt
            
    def _track_performance(self, prompt_type: str, start_time: datetime, prompt_length: int):
        """Track prompt generation performance metrics"""
        duration = (datetime.now() - start_time).total_seconds()
        self.performance_metrics.append({
            "type": prompt_type,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "prompt_length": prompt_length
        })
        
    def _track_error(self, prompt_type: str, error_message: str):
        """Track prompt generation errors"""
        self.performance_metrics.append({
            "type": prompt_type,
            "timestamp": datetime.now().isoformat(),
            "error": error_message
        })
        
    def get_performance_metrics(self) -> List[Dict]:
        """Retrieve prompt generation performance metrics"""
        return self.performance_metrics
