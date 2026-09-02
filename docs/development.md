# Local development

Use Python 3.11.x and create a virtual environment in the project root:

```powershell
python -m venv venv
venv\Scripts\activate
```

Install dependencies from `requirements.txt`.

VS Code is configured to use `venv\\Scripts\\python.exe` through `.vscode/settings.json`. If imports are still underlined, select the same interpreter with **Python: Select Interpreter**.

The application uses the modern LangChain package layout (`langchain_core`, `langchain_chroma`, `langchain_huggingface`, and `langchain_text_splitters`). It does not use deprecated `langchain.chains` or `langchain_classic.chains` imports.
