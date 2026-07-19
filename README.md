# Enhanced MCP Server & Client Setup in Python

An advanced demonstration of Anthropic's **Model Context Protocol (MCP)**, bridging LLMs (specifically Claude 3.7 Sonnet) with local workspace environments safely and interactively. 

This project implements a custom **FastMCP Server** with resource routing, progress reporting, and interactive elicitation, paired with a custom **Command Line Client** that manages agentic tool-use loops.

---

## 🚀 Project Presentation Showcase

This project includes a pre-packaged 7-slide presentation designed for student profile showcases (e.g., LinkedIn posts, portfolios) to catch the attention of recruiters and hiring managers.

The slides and PDF compilation can be found in the [slideshow/](slideshow) directory.

### Swipe Through the Slides:

| Slide 1: Cover | Slide 2: Why MCP? |
| :---: | :---: |
| ![Slide 1 - Cover](slideshow/slide_1.png) | ![Slide 2 - Why MCP?](slideshow/slide_2.png) |

| Slide 3: Architecture | Slide 4: Real-Time Progress |
| :---: | :---: |
| ![Slide 3 - Architecture](slideshow/slide_3.png) | ![Slide 4 - Progress-Tracked Async Writing](slideshow/slide_4.png) |

| Slide 5: Interactive Elicitation | Slide 6: Resources & Prompts |
| :---: | :---: |
| ![Slide 5 - Interactive Elicitation](slideshow/slide_5.png) | ![Slide 6 - Resources & Prompts](slideshow/slide_6.png) |

| Slide 7: Technical Highlights & CTA |
| :---: |
| ![Slide 7 - Engineering Highlights](slideshow/slide_7.png) |

*(Download the compiled presentation directly as a PDF: [slideshow/mcp_project_presentation.pdf](slideshow/mcp_project_presentation.pdf))*

---

## 🛠️ Key Features

### 1. FastMCP Server (`server.py`)
* **Progress-Tracked Async File Writing:** Writes file contents in chunks, reporting progress dynamically back to the client (`ctx.report_progress`).
* **Safe Filesystem Tooling:** Exposes `write_file` and `delete_file` with strict path resolution to prevent directory traversal attacks (keeps operations inside `BASE_DIR`).
* **Dynamic Resource Schemas:** Exposes workspace files (`file:///`) and directory listings (`dir://.`) with node metadata (size, modified, type).
* **Interactive Prompts:** Expert prompts for automated code reviews and technical documentation generation.

### 2. Interactive MCP Client (`client.py`)
* **Agentic Tool-Use Loop:** Orchestrates conversations with the Anthropic Claude API, automatically executing server tools requested by the model and returning results to Claude mid-flight.
* **Input Elicitation Handler:** Resolves LLM requests for human input dynamically using Pydantic models (e.g., collecting filenames interactively).
* **Console Dashboard:** A CLI menu system allowing users to select tasks, review code, generate documentation, browse files, or converse with Claude.

---

## 💻 Tech Stack

* **Language:** Python 3.11+
* **Framework:** Anthropic FastMCP V2
* **SDK:** Anthropic Python SDK (Model: `claude-3-7-sonnet-20250219`)
* **Schema Validation:** Pydantic V2
* **Asynchrony:** Python standard `asyncio` & `AsyncExitStack`

---

## ⚙️ Getting Started

### 1. Clone & Install Dependencies
First, install the required packages:
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Create a `.env` file in the root directory and add your Anthropic API Key:
```env
ANTHROPIC_API_KEY=your_api_key_here
```

### 3. Run the Client and Server
Run the client, passing the server script path as an argument. The client starts the server via standard I/O (Stdio):
```bash
python client.py server.py
```

---

## 🎮 CLI Client Menu Options

Upon running the client, you will see the interactive terminal menu:

```text
Select from the Menu
1. Generate Documentation
2. Review Code
3. Read File
4. Read Current Directory
5. Converse with Agent
q. Quit
> 
```

1. **Generate Documentation:** Elicits the source file and documentation names, reads the source file content, and elicits Claude to write a comprehensive markdown document.
2. **Review Code:** Prompts Claude to do a structured, multi-dimensional code review of any workspace file.
3. **Read File:** Accesses files dynamically through the server's resource URI scheme.
4. **Read Current Directory:** Retrieves a structured directory listing with modified timestamps and sizes.
5. **Converse with Agent:** Opens an open-ended conversation with Claude, where Claude can leverage all server tools to assist you.