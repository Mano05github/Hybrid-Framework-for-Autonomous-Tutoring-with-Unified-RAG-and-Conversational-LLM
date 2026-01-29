from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """
    Abstract Base Class for all LLM Providers.
    Enforces a strict contract: You give a prompt, you get text.
    """
    
    @abstractmethod
    def generate_response(self, prompt: str, system_instruction: str = None) -> str:
        """
        Generates text response from the LLM.
        :param prompt: The user input or full context string.
        :param system_instruction: Optional system prompt (e.g. "You are a Tutor").
        :return: string response.
        """
        pass

    @abstractmethod
    def generate_vision_response(self, prompt: str, image_base64: str, system_instruction: str = None) -> str:
        """
        Generates text response from the LLM based on Text + Image.
        :param prompt: The user question.
        :param image_base64: Base64 encoded image string.
        :param system_instruction: Optional system prompt.
        :return: string response.
        """
        pass
