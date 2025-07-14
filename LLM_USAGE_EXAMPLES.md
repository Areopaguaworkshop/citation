# LLM Model Usage Examples

The citation extraction tool now supports flexible LLM model selection through the `--llm` parameter.

## Supported Providers

### Ollama (Local Models)
- **Format**: `ollama/model-name`
- **Base URL**: `http://localhost:11434`
- **Examples**: 
  - `ollama/qwen3` (default)
  - `ollama/llama3`
  - `ollama/llama3.1`
  - `ollama/mixtral`
  - `ollama/codellama`

### Google Gemini (API Models)
- **Format**: `gemini/model-name`
- **API Base**: `https://generativelanguage.googleapis.com`
- **Examples**:
  - `gemini/gemini-1.5-flash`
  - `gemini/gemini-1.5-pro`
  - `gemini/gemini-2.0-flash-exp`
  - `gemini/gemini-2.5-flash`
  - Any other valid Gemini model name

## Usage Examples

### Basic Usage (Default Ollama)
```bash
python -m citation.cli document.pdf
```

### Using Gemini 2.5 Flash
```bash
python -m citation.cli --llm gemini/gemini-2.5-flash document.pdf
```

### Using Gemini 2.0 Flash Experimental
```bash
python -m citation.cli --llm gemini/gemini-2.0-flash-exp document.pdf
```

### Using Different Ollama Models
```bash
python -m citation.cli --llm ollama/llama3 document.pdf
python -m citation.cli --llm ollama/mixtral document.pdf
```

### With Verbose Output
```bash
python -m citation.cli --llm gemini/gemini-2.5-flash --verbose document.pdf
```

### Complete Example with All Options
```bash
python -m citation.cli \
  --llm gemini/gemini-2.5-flash \
  --type book \
  --output-dir my_citations \
  --verbose \
  document.pdf
```

## Notes

- The system automatically detects the provider based on the prefix (`ollama/` or `gemini/`)
- DSPy handles the actual model validation and API calls
- No need to hardcode model names - any valid model for the provider should work
- For Gemini models, make sure you have the appropriate API credentials configured
- For Ollama models, ensure Ollama is running locally on port 11434
