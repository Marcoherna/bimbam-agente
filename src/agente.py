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
from dotenv import load_dotenv

load_dotenv()

RUTA_PDF = Path(__file__).parent.parent / "data" / "politica_reembolsos_bimbam_buy.pdf"

PROMPT = ChatPromptTemplate.from_template(
    """Eres el asistente virtual oficial de BimBam Buy, un e-commerce latinoamericano.
Respondes preguntas de clientes y colaboradores usando EXCLUSIVAMENTE el contexto
extraído de la Política de Reembolsos y Devoluciones.

Reglas:
- Responde en español, de forma clara, breve y amable.
- Si la respuesta no está en el contexto, di honestamente que la política
  no cubre ese punto y sugiere escribir a soporte@bimbambuy.com.
- Cuando menciones plazos o montos, sé preciso con los valores del documento.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:"""
)


def construir_agente(ruta_pdf: str | Path = RUTA_PDF):
    """Construye y devuelve la cadena RAG lista para responder preguntas."""
    if not os.getenv("GOOGLE_API_KEY"):
        raise EnvironmentError(
            "Falta la variable GOOGLE_API_KEY. Consíguela gratis en "
            "https://aistudio.google.com/apikey y expórtala antes de ejecutar."
        )

    # 1) Leer el documento
    documentos = PyPDFLoader(str(ruta_pdf)).load()

    # 2) Dividir en fragmentos con superposición para no cortar ideas
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    fragmentos = splitter.split_documents(documentos)

    # 3) Vectorizar e indexar
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", output_dimensionality=768)
    indice = FAISS.from_documents(fragmentos, embeddings)
    retriever = indice.as_retriever(search_kwargs={"k": 4})

    # 4) Modelo de lenguaje
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

    # 5) Cadena RAG: pregunta -> recuperar contexto -> prompt -> LLM -> texto
    def formatear(docs):
        return "\n\n".join(d.page_content for d in docs)

    cadena = (
        {"contexto": retriever | formatear, "pregunta": RunnablePassthrough()}
        | PROMPT
        | llm
        | StrOutputParser()
    )
    return cadena


if __name__ == "__main__":
    # Modo consola: python src/agente.py
    print("Construyendo el agente (esto tarda unos segundos)...")
    agente = construir_agente()
    print("Listo. Escribe tu pregunta o 'salir' para terminar.\n")
    while True:
        pregunta = input("Tú: ").strip()
        if pregunta.lower() in {"salir", "exit", "quit"}:
            break
        if pregunta:
            print(f"\nAgente: {agente.invoke(pregunta)}\n")
