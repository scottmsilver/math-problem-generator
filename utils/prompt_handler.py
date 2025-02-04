from string import Template
from typing import Dict

class PromptHandler:
    def process_template(self, template: str, variables: Dict[str, str]) -> str:
        """
        Process a prompt template with given variables.
        
        Args:
            template: The prompt template string
            variables: Dictionary of variables to substitute
            
        Returns:
            Processed prompt string
            
        Raises:
            KeyError: If a required variable is missing
            ValueError: If the template is invalid
        """
        try:
            template_obj = Template(template)
            return template_obj.substitute(**variables)
        except KeyError as e:
            raise ValueError(f"Missing required variable: {str(e)}")
        except ValueError as e:
            raise ValueError(f"Invalid template format: {str(e)}")
