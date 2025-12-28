from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# from langchain.chains.summarize import load_summarize_chain
# from langchain_text_splitters import TokenTextSplitter
# from langchain.docstore.document import Document
from typing import Optional

def get_llm(provider: str, api_key: str, base_url: str = None, model_name: str = None, max_tokens: int = 4000):
    """
    Factory to create a LangChain Chat Model based on configuration.
    """
    if not model_name:
        if provider == 'openai': model_name = "gpt-3.5-turbo"
        elif provider == 'deepseek': model_name = "deepseek-chat"
        elif provider == 'qwen': model_name = "qwen-plus"
        else: model_name = "gpt-3.5-turbo"

    # Map provider to base_url if not provided
    if not base_url:
        if provider == 'deepseek':
            base_url = "https://api.deepseek.com"
        elif provider == 'qwen':
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        # OpenAI default is fine

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
        max_tokens=max_tokens,
        timeout=600,
        max_retries=3,
    )

def invoke_chain(llm, system_prompt: str, user_prompt_template: str, input_variables: dict) -> str:
    """
    Generic function to invoke a simple chain.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", user_prompt_template)
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    return chain.invoke(input_variables)

# def summarize_large_content(llm, content: str, chunk_size: int = 15000, chunk_overlap: int = 500) -> str:
#     """
#     Summarize large content using Map-Reduce strategy with TokenTextSplitter.
#     Suitable for large documents that exceed the context window.
#     """
#     text_splitter = TokenTextSplitter(
#         chunk_size=chunk_size,
#         chunk_overlap=chunk_overlap
#     )
#     docs = text_splitter.create_documents([content])
#     
#     # Use map_reduce chain
#     # Note: This requires multiple LLM calls
#     chain = load_summarize_chain(llm, chain_type="map_reduce")
#     return chain.invoke(docs)["output_text"]
