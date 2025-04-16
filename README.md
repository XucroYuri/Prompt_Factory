English | [简体中文](docs/locale/README_zh.md)

# Prompt Factory
Highly efficient prompt engineering tool supporting batch optimization for multiple files with automated environment setup.

## Features
- Support for multiple AI service providers (DeepSeek, OpenAI, Anthropic, OpenRouter)
- Automated environment detection, dependency installation, and self-checks
- Recursive processing of all files in directories
- Secure in-memory API key management, auto-cleared on exit
- Interactive command-line interface
- Modular design for easy extension and integration

## Installation Guide
### Requirements
- Python 3.8+
- pip 20.0+

### Steps

#### For All Platforms
1. Clone the repository
   ```bash
   git clone https://github.com/XucroYuri/Prompt_Factory.git
   cd Prompt_Factory
   ```

#### macOS/Linux
```bash
python3 -m src.enhanced_cli
```

#### Windows
```cmd
python -m src.enhanced_cli
```

The program auto-detects the environment, installs dependencies, and guides you through configuration.

## Usage Process

### Common Steps
1. Run the program:
   - **macOS/Linux**: `python3 -m src.enhanced_cli`
   - **Windows**: `python -m src.enhanced_cli`
2. Enter your API key as prompted (supports DeepSeek, OpenAI, OpenRouter)
3. Connection to API is tested automatically
4. Select service provider and model
5. Choose prompt template
6. Input the target file or directory
   - On Windows, use backslashes for paths (e.g., `C:\folder\file.txt`)
   - On macOS/Linux, use forward slashes (e.g., `/folder/file.txt`)
7. Results are automatically saved in the output directory

## Advanced Usage
### CLI Arguments

#### macOS/Linux
```bash
python3 -m src.enhanced_cli --force-install  # Force reinstall dependencies
python3 -m src.enhanced_cli --debug          # Enable debug mode
```

#### Windows
```cmd
python -m src.enhanced_cli --force-install  # Force reinstall dependencies
python -m src.enhanced_cli --debug          # Enable debug mode
```

### Developer API
```python
from src.core.prompt_processor import PromptProcessor

# Create a processor instance
processor = PromptProcessor(
    api_key="your_api_key",
    template_name="standard",
    model="deepseek/deepseek-chat",
    temperature=0.7,
    timeout=30,
    max_retries=2
)

# Process a single file
processor.process_file("path/to/file.md")

# Process an entire directory
stats = processor.process_directory(
    "path/to/directory",
    file_extensions=[".md", ".txt"],
    recursive=True
)
```

## Supported Model Providers
- DeepSeek
- OpenAI
- Anthropic
- OpenRouter

## Directory Structure
```
Prompt_Factory/
├── docs/            # Documentation
├── output/          # Output Results
├── logs/            # Log Files
├── src/             # Source Code
│   ├── api/         # API Server
│   ├── core/        # Core Modules
│   │   ├── model_manager.py     # Model Management
│   │   ├── prompt_processor.py  # Prompt Processing
│   │   └── template_manager.py  # Template Management
│   ├── utils/       # Utilities
│   │   ├── environment.py       # Environment Manager
│   │   └── cli_interface.py     # CLI Interface
│   ├── enhanced_cli.py          # Enhanced CLI Entry
│   └── main.py                  # Main Entry
└── templates/       # Prompt Templates
```

## Notes
- API keys are only used in memory and are cleared when the program exits
- Outputs are saved in the output directory, organized by date and batch
- Log files contain no sensitive information, ensuring API key security
- It is recommended to use Python 3.8 or higher for best compatibility

## Roadmap
- More model provider integrations: support for Google Gemini, Grok, etc.
- Rate limiting mechanism for API communications
- Time-zone-driven runtime scheduling
- Frontend UI development: intuitive and efficient user interface design

## System Architecture
### Core Modules and Relationships
```
+-------------------+      +------------------+
| PromptProcessor   |----->| TemplateManager  |
| (Main Processor)  |      | (Template Mgmt)  |
+-------------------+      +------------------+
         |                          |
         | Calls                    | Loads templates
         v                          v
+-------------------+      +------------------+
| ModelManager      |      | Templates        |
| (Model Mgmt)      |      | (Template Files) |
+-------------------+      +------------------+
         |
         | Accesses config
         v
+-------------------+
| Config            |
| (Configuration)   |
+-------------------+
```

### Data Flow
1. User provides parameters via CLI or config file
2. `prompt_processor.py` loads configuration and initializes processor
3. Processor loads the specified template using `template_manager.py`
4. Processor reads prompt files from the given directory
5. Processor embeds prompts into templates for processing
6. Calls `model_manager.py` to access the model and send requests
7. Handles responses and stores optimized prompts

## Frontend-Backend Separation Guide
The backend provides RESTful API interfaces, for details refer to [API Reference](docs/api_reference.md). For frontend development suggestions and component design, refer to [Frontend Integration](docs/frontend_integration.md).

## Contribution Guide
Contributions, bug reports, and suggestions are welcome. Please follow these steps:
1. Fork the project
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Submit a Pull Request

Make sure your code follows project standards and passes all tests.

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for more information.

## Environment Preparation

- Python 3.8 or above is required; development and testing on macOS/Linux is recommended.
- Install dependencies:
  ```bash
  pip3 install -r requirements.txt
  ```

## Locale Configuration
If you need to customize the interface and output language, refer to [Chinese README](docs/locale/README_zh.md).

## Usage Example
```python
from src.core.prompt_processor import PromptProcessor
processor = PromptProcessor(api_key="your_api_key")
result = processor.process_content("Please optimize this prompt.")
```

## Dependency Notes
- Internet connection required for using models like DeepSeek/OpenAI/OpenRouter.
- If you encounter a requests-related error, run `pip3 install requests`.
- Model and template configuration details: see docs/prompt_processor.md and docs/template_manager.md.

## FAQ
- Invalid API key / request timeout: Ensure network is available and your API key is valid.
- File or directory not found: Make sure data paths and directories are correct.
- For other issues, run `python3 -m src.main` to see detailed error messages.