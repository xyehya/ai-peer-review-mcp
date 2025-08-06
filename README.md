# AI Peer Review MCP Server

> **Enhance your local LLM responses with real-time peer review from Google Gemini**

A Model Context Protocol (MCP) server that enables local language models to request peer review feedback from Google Gemini, dramatically improving response quality through AI collaboration.

## 🌟 Features

- **Real-time peer review** from Google Gemini for any local LLM response
- **Manual trigger system** - user controls when to request peer review  
- **Detailed feedback analysis** - accuracy, completeness, clarity, and improvement suggestions
- **Comprehensive logging** - see exactly what feedback Gemini provides
- **Privacy-conscious** - only shares content when explicitly requested
- **Free to use** - leverages Google Gemini's free tier
- **Easy integration** - works with any MCP-compatible local LLM setup

## 🎯 Use Cases

- **Fact-checking** complex or technical responses
- **Quality improvement** for educational content
- **Writing enhancement** for creative tasks  
- **Technical validation** for coding explanations
- **Research assistance** with multiple AI perspectives

## 📋 Prerequisites

- **Python 3.8+** installed on your system
- **LMStudio** (or another MCP-compatible LLM client)
- **Google AI Studio account** (free) for Gemini API access
- **Local LLM with tool calling support** (e.g., Llama 3.1, Mistral, Qwen)

## 🚀 Quick Start

### 1. Get Google Gemini API Key

1. Visit [Google AI Studio](https://ai.google.dev)
2. Sign in with your Google account
3. Click **"Get API key"** → **"Create API key in new project"**
4. Copy your API key (starts with `AIza...`)

### 2. Install the MCP Server

```bash
# Clone or create project directory
git clone https://github.com/your-repo/ai-peer-review-mcp # Replace with the actual repo URL
cd ai-peer-review-mcp

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Now, edit the .env file and add your API key:
# GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Review Server Files

**requirements.txt:**
```txt
requests
python-dotenv
```

**server.py:** *(See full code in the repository)*

### 4. Configure LMStudio or any other supported MCP Host (e.g Claude Desktop)

Add this configuration to your LMStudio MCP settings:

```json
{
  "mcpServers": {
    "ai-peer-review": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/path/to/your/ai-peer-review-mcp",
      "env": {
        "GEMINI_API_KEY": "your_actual_api_key_here"
      }
    }
  }
}
```

**Finding MCP Settings in LMStudio:**
- Look for: Settings → MCP Servers
- Or: Tools & Integrations → MCP Configuration  
- Or: Program button → Edit MCP JSON

### 5. Test the Setup

1. **Restart LMStudio** after adding the MCP configuration
2. **Start a new chat** in LMStudio
3. **Ask any question:** "What is quantum computing?"
4. **Request peer review:** "Use the ai_peer_review tool to check and improve your answer"

## 📚 Usage Examples

### Basic Usage
```
User: What causes climate change?

LLM: [Provides initial response about greenhouse gases...]

User: Use AI Peer Review to verify and improve that answer

LLM: [Calls ai_peer_review tool, receives feedback, provides enhanced response]
```

### Technical Questions
```
User: Explain how neural networks work

LLM: [Initial technical explanation...]

User: Can you use ai_peer_review to make sure the explanation is accurate?

LLM: [Enhanced response with better technical details and examples]
```

### Creative Tasks
```
User: Write a short story about AI

LLM: [Initial creative writing...]

User: Use peer review to improve the story structure and clarity

LLM: [Improved story with better narrative flow and character development]
```

## 🔧 Configuration Options

### Environment Variables

- `GEMINI_API_KEY` - Your Google Gemini API key (required)

### Customization

You can modify the peer review prompt in `server.py` to focus on specific aspects:

```python
review_prompt = f"""PEER REVIEW REQUEST:
# Customize this section for your specific needs
# Examples:
# - Focus on technical accuracy for coding questions
# - Emphasize creativity for writing tasks
# - Prioritize safety for medical/legal topics
...
"""
```

## 📊 Monitoring and Logs

The server creates detailed logs in `mcp-server.log`:

```bash
# Watch logs in real-time
tail -f mcp-server.log

# View recent activity
cat mcp-server.log | tail -50
```

**Log Information Includes:**
- Tool calls from LMStudio
- Requests sent to Gemini
- Raw Gemini responses
- Parsed feedback
- Error details

## 🐛 Troubleshooting

### Common Issues

**"Tool not available"**
- Verify MCP server configuration in LMStudio
- Ensure your local model supports tool calling
- Restart LMStudio after configuration changes

**"GEMINI_API_KEY not found"**
- Check your `.env` file exists and has the correct key
- Verify API key is valid in Google AI Studio
- Ensure environment variable is properly set in LMStudio config

**"Rate limit exceeded"**
- Google Gemini free tier has generous limits
- Wait a moment and try again
- Check Google AI Studio quota usage

**"Model not found"**
- API model names change over time
- Update `GEMINI_API_URL` in server.js if needed
- Check Google's latest API documentation

### Debug Mode

Run the server manually to see detailed output. Make sure your virtual environment is active.

```bash
export GEMINI_API_KEY=your_api_key_here
python server.py
```

## 🔒 Privacy and Security

- **Data sharing only on request** - content is only sent to Gemini when explicitly triggered
- **No persistent storage** - conversations are not stored or logged beyond current session
- **API key security** - keep your Gemini API key private and secure
- **Local processing** - MCP runs entirely on your machine

## 🚧 Limitations

- **Requires tool-calling models** - basic instruction-following models won't work
- **Internet connection required** - needs access to Google Gemini API
- **Rate limits** - subject to Google Gemini API quotas (free tier is generous)
- **Language support** - optimized for English, other languages may work but aren't tested

## 🛣️ Roadmap

- [ ] **Multi-provider support** - Add Groq, DeepSeek, and other AI APIs
- [ ] **Smart routing** - Automatic provider selection based on question type
- [ ] **Confidence thresholds** - Auto-trigger peer review for uncertain responses
- [ ] **Custom review templates** - Domain-specific review criteria
- [ ] **Usage analytics** - Track improvement metrics and API usage
- [ ] **Batch processing** - Review multiple responses at once

## 🤝 Contributing

We welcome contributions! Here's how to help:

### Development Setup

```bash
git clone https://github.com/your-repo/ai-peer-review-mcp # Replace with your repo URL
cd ai-peer-review-mcp

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up your environment
cp .env.example .env
# --> Add your GEMINI_API_KEY to the .env file

echo "Development environment ready. Run with 'python server.py'"
```

### Ways to Contribute

- **🐛 Bug reports** - Open issues for any problems you encounter
- **💡 Feature requests** - Suggest new capabilities or improvements  
- **📖 Documentation** - Improve setup guides, add examples
- **🔧 Code contributions** - Submit pull requests for fixes or features
- **🧪 Testing** - Try with different models and report compatibility
- **🌍 Localization** - Help support more languages

### Contribution Guidelines

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** with clear, descriptive commits
4. **Add tests** if applicable
5. **Update documentation** for any new features
6. **Submit a pull request** with a clear description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic** - For creating the Model Context Protocol standard
- **Google** - For providing the Gemini API
- **LMStudio** - For excellent MCP integration
- **Community contributors** - Everyone who helps improve this project

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/xyehya/ai-peer-review-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/xyehya/ai-peer-review-mcp/discussions)  


## 🌟 Star History

If this project helps you, please consider giving it a star on GitHub! ⭐

---

**Made with ❤️ for the AI community**
