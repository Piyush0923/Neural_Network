import os
import ollama
import numpy as np
from typing import List, Dict, Any
from ollama import ResponseError
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaLLM:
    """Ollama-based language model implementation"""
    
    def __init__(self, model_name: str = 'mistral'):
        self.model_name = model_name
        self._verify_model_availability()

    def _verify_model_availability(self):
        """Check if the specified model is available locally"""
        try:
            ollama.show(self.model_name)
            logger.info(f"Successfully loaded model: {self.model_name}")
        except ResponseError as e:
            logger.error(f"Model {self.model_name} not found. Please install it first.")
            raise RuntimeError(
                f"Model {self.model_name} not installed. "
                f"Run 'ollama pull {self.model_name}' to install."
            ) from e
        


    def generate(self, prompts: List[str], **kwargs) -> List[str]:
        """
        Generate responses using Ollama
        
        Args:
            prompts: List of input prompts
            **kwargs: Additional generation parameters
            
        Returns:
            List of generated responses
        """
        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=prompts[0],
                options={
                    'temperature': kwargs.get('temperature', 0.7),
                    'top_p': kwargs.get('top_p', 0.9),
                    'max_tokens': kwargs.get('max_tokens', 512)
                }
            )
            return [response['response']]
        except Exception as e:
            logger.error(f"Generation error: {str(e)}")
            return ["Sorry, I'm having trouble generating a response right now."]

    async def generate_async(self, prompts: List[str], **kwargs) -> List[str]:
        """Async version of generate method"""
        try:
            response = await ollama.AsyncClient().generate(
                model=self.model_name,
                prompt=prompts[0],
                options={
                    'temperature': kwargs.get('temperature', 0.7),
                    'top_p': kwargs.get('top_p', 0.9),
                    'max_tokens': kwargs.get('max_tokens', 512)
                }
            )
            return [response['response']]
        except Exception as e:
            logger.error(f"Async generation error: {str(e)}")
            return ["Sorry, I'm having trouble generating a response right now."]

class OllamaEmbeddingModel:
    """Ollama-based text embedding model"""
    
    def __init__(self, model_name: str = 'nomic-embed-text'):
        self.model_name = model_name
        self._verify_model_availability()
        self.dimension = 768  # Default dimension for nomic-embed-text

    def _verify_model_availability(self):
        """Check if embedding model is available"""
        try:
            ollama.show(self.model_name)
            logger.info(f"Successfully loaded embedding model: {self.model_name}")
        except ResponseError as e:
            logger.error(f"Embedding model {self.model_name} not found.")
            raise RuntimeError(
                f"Embedding model {self.model_name} not installed. "
                f"Run 'ollama pull {self.model_name}' to install."
            ) from e

    def encode(self, text: str) -> np.ndarray:
        """
        Generate embeddings for text
        
        Args:
            text: Input text to embed
            
        Returns:
            Numpy array of embeddings
        """
        try:
            response = ollama.embeddings(model=self.model_name, prompt=text)
            return np.array(response['embedding'])
        except Exception as e:
            logger.error(f"Embedding error: {str(e)}")
            return np.zeros(self.dimension)

class FallbackLLM:
    """Fallback LLM for when Ollama is unavailable"""
    
    def generate(self, prompts: List[str], **kwargs) -> List[str]:
        return ["Our AI service is currently unavailable. Please try again later."]
    
    async def generate_async(self, prompts: List[str], **kwargs) -> List[str]:
        return ["Our AI service is currently unavailable. Please try again later."]

def get_llm(model_name: str = 'mistral') -> OllamaLLM:
    """
    Get configured Ollama LLM instance with fallback
    
    Args:
        model_name: Name of Ollama model to use
        
    Returns:
        Configured LLM instance
    """
    try:
        return OllamaLLM(model_name)
    except RuntimeError as e:
        logger.error(f"Failed to load LLM: {str(e)}")
        return FallbackLLM()

def get_embedding_model(model_name: str = 'nomic-embed-text') -> OllamaEmbeddingModel:
    """
    Get configured embedding model
    
    Args:
        model_name: Name of embedding model to use
        
    Returns:
        Configured embedding model instance
    """
    try:
        return OllamaEmbeddingModel(model_name)
    except RuntimeError as e:
        logger.error(f"Failed to load embedding model: {str(e)}")
        return None

def analyze_text(text: str, prompt: str) -> str:
    """
    Analyze text using Ollama
    
    Args:
        text: Text to analyze
        prompt: Analysis prompt/instruction
        
    Returns:
        Analysis result
    """
    try:
        llm = get_llm()
        full_prompt = f"{prompt}\n\nText to analyze:\n{text}"
        return llm.generate([full_prompt])[0]
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return "Unable to perform analysis at this time."

def generate_response(conversation_history: List[Dict[str, str]], query: str) -> str:
    """
    Generate conversational response using Ollama
    
    Args:
        conversation_history: List of previous messages
        query: Current user query
        
    Returns:
        Generated response
    """
    try:
        llm = get_llm()
        
        # Format conversation history
        messages = [
            {"role": "system", "content": "You are a helpful recruitment assistant."}
        ]
        messages += [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in conversation_history[-6:]
        ]
        messages.append({"role": "user", "content": query})
        
        return llm.generate([format_messages(messages)])[0]
    except Exception as e:
        logger.error(f"Response generation error: {str(e)}")
        return "I'm having trouble responding right now. Please try again later."

def format_messages(messages: List[Dict[str, str]]) -> str:
    """Format messages for LLM input"""
    return "\n".join(
        [f"{msg['role'].capitalize()}: {msg['content']}" 
         for msg in messages]
    )