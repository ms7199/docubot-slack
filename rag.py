from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
import os

def create_chat_chain():
    llm = ChatGroq(api_key=os.environ.get("GROQ_API_KEY"), model="llama-3.3-70b-versatile", temperature=0.1)

    rag_template = """You are an AI assistant that helps answer questions based on provided context.

{input}

Instructions:
1. Use the provided context to answer the question accurately.
2. If the context doesn't contain relevant information, say so clearly.
3. Be concise but comprehensive.

Assistant:"""

    prompt = PromptTemplate(input_variables=["input"], template=rag_template)

    chain = LLMChain(llm=llm, prompt=prompt, verbose=True, memory=ConversationBufferWindowMemory(k=3))
    return chain
