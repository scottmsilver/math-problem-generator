# LaTeX Problem Generator

This project provides a tool for generating LaTeX-formatted math problems based on user-defined templates and criteria.

## Features

   
- Generate math problems using LaTeX syntax
- Customize problem difficulty
- Specify number of problems to generate
- Support for multiple AI providers

## Usage

1. Define your LaTeX template in the `template_content` field
2. Set the desired `difficulty` level
3. Specify the `num_problems` to generate
4. Choose an AI `provider`
5. Run the generator to create new problems

## Example

```python
request = GenerateProblemsRequest(
    template_content="\\begin{problem}\n  $2x + 3 = 7$\n\\end{problem}",
    difficulty=Difficulty.MEDIUM,
    num_problems=5,
    provider=Provider.CLAUDE
)
```

```
cd /Users/ssilver/development/math/AIInteractionTool
curl -X POST http://localhost:8080/generate \
  -F "file=@limits.pdf" \
  -F "provider=claude" \
  -F "difficulty=challenge" \
  -F "num_problems=3" \
  --output generated_problems.zip
```

## Requirements

- Python 3.7+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the main script: `python main.py`

## Contributing

Contributions are welcome! Please submit a pull request or create an issue for any bugs or feature requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
