import gradio as gr
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# Set your local ollama model name
OLLAMA_MODEL = "llama2"  # Change to your local model name (e.g., llama2, llama3.1:8b)

# Build the prompt
prompt = ChatPromptTemplate.from_template(
    "You are an AI agent. User input: {user_input}"
)

# Create Ollama LLM
llm = ChatOllama(model=OLLAMA_MODEL)

# Build the LCEL pipeline
chain = prompt | llm

# Gradio callback function
def agent_answer(user_input):
    result = chain.invoke({"user_input": user_input})
    return result.content if hasattr(result, "content") else str(result)

# Build the Gradio interface
demo = gr.Interface(
    fn=agent_answer,
    inputs=gr.Textbox(lines=2, label="User Input"),
    outputs=gr.Textbox(lines=6, label="Agent Output"),
    title="Ollama + LangChain AI Agent Proxy Demo",
    description="Local LLM powered by Ollama, orchestrated by LangChain, with customizable prompts."
)

if __name__ == "__main__":
    demo.launch()
