from string import Template
from typing import Dict

class PromptHandler:
    def process_template(self, template: str, variables: Dict[str, str]) -> str:
        """
        Process a prompt template with given variables.

        Args:
            template: The prompt template string with $name style parameters
                     Example: "Analyze this $object in the image"
            variables: Dictionary of variables to substitute
                      Example: {"object": "cat"}

        Returns:
            Processed prompt string

        Raises:
            KeyError: If a required variable is missing
            ValueError: If the template is invalid
        """
        try:
            # First validate that all required variables are present
            template_obj = Template(template)
            required_vars = [name for _, name, _, _ in template_obj.pattern.findall(template)]
            missing_vars = set(required_vars) - set(variables.keys())

            if missing_vars:
                raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")

            return template_obj.substitute(**variables)
        except KeyError as e:
            raise ValueError(f"Missing required variable: {str(e)}")
        except ValueError as e:
            raise ValueError(f"Invalid template format: {str(e)}")