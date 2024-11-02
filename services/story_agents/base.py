from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from services.text_generator import TextGenerator

class StoryAgent(ABC):
    """
    Base class for all story generation agents.
    Each agent specializes in a specific aspect of story creation.
    """
    
    def __init__(self, text_generator: TextGenerator):
        self.text_generator = text_generator
        
    def _generate_with_retry(
        self, 
        prompt: str, 
        temperature: float = 0.7, 
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Generate text with retry mechanism for reliability
        
        Args:
            prompt: The prompt to send to the text generator
            temperature: Controls randomness in generation
            max_retries: Maximum number of retry attempts
            
        Returns:
            Generated text or None if all retries fail
        """
        try:
            return self.text_generator.generate(
                prompt=prompt,
                temperature=temperature
            )
        except Exception as e:
            if max_retries > 0:
                return self._generate_with_retry(
                    prompt=prompt,
                    temperature=temperature,
                    max_retries=max_retries - 1
                )
            return None
            
    @abstractmethod
    def generate(self, context: Dict[str, Any]) -> Any:
        """
        Generate content specific to the agent's role
        
        Args:
            context: Dictionary containing relevant context for generation
            
        Returns:
            Generated content in the appropriate format
        """
        pass
