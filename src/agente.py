"""
Agente de IA para BimBam Buy
----------------------------
Lee la Política de Reembolsos y Devoluciones (PDF) y responde preguntas
en lenguaje natural usando RAG (Retrieval-Augmented Generation):

  1. Carga el PDF y lo divide en fragmentos (chunks).
  2. Convierte cada fragmento en un vector (embeddings de Gemini).
  3. Guarda los vectores en un índice FAISS en memoria.
  4. Ante una pregunta, recupera los fragmentos más relevantes
     y se los pasa al modelo Gemini para redactar la respuesta.
"""

import os
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

RUTA_PDF = Path(__file__).parent.parent / "data" / "politica_reembolsos_bimbam_buy.pdf"

