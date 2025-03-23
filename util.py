#import chromadb
import requests
from bs4 import BeautifulSoup


from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain_community.vectorstores import Chroma
import os
from langchain_community.vectorstores import Chroma

from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader

from langchain.text_splitter import CharacterTextSplitter

import re




import cohere
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import CohereEmbeddings
from langchain.vectorstores import Chroma
api_key = 'WbTLzQDGKfv3rtYzptfh9XR4mpQrTjTsewkputI8'






#obtained data using wikipedia api
#prsed using beautiful soup

def get_full_wikipedia_content(url):

    try:
        # Make the request
        response = requests.get(url)
        response.raise_for_status()
        #return response.text

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the main content div
        content_div = soup.find(id="mw-content-text")

        # Extract all paragraphs
        paragraphs = content_div.find_all('p')

        # Combine all paragraph texts
        full_text = '\n\n'.join([para.get_text() for para in paragraphs])

        # Remove citations [1], [2], etc.
        import re
        full_text = re.sub(r'\[\d+\]', '', full_text)

        return full_text.strip()

    except requests.RequestException as e:
        return f"Error fetching page: {str(e)}"


#preprocessing
def combine_strings(original_list, chunk_size=3):
    return [''.join(original_list[i:i + chunk_size])
            for i in range(0, len(original_list), chunk_size)]


def preprocess(text):
    text = text.replace('\n', '')

    lis = text.split(".")

    combined = combine_strings(lis)
    text = """ """
    for i in combined:
        text += i+"\n\n\n"
    return text

#chunking
from langchain.text_splitter import CharacterTextSplitter

def create_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator = '\n\n\n',
        chunk_size = 200,
    )

   
    documents = text_splitter.create_documents([text])
    
    return documents

def documented(documents):
    document_texts = [doc.page_content for doc in documents]
    return document_texts

def retriever(documents,document_texts,query):
    co = cohere.Client(api_key)
    model="rerank-english-v2.0"
    rerank_results = co.rerank(model=model, query=query, documents=document_texts, top_n=2)
    CONTEXT = """"""
    for result in rerank_results.results:
        CONTEXT +=document_texts[result.index]+"\n=======================\n"
        #print(f"Relevance Score: {result.relevance_score:.2f}, Text: {document_texts[result.index]}")
    return CONTEXT


import requests

def generator(CONTEXT,query):
    API_KEY = "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"
    URL = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    template= f"""
        Use the following CONTEXT to answer the QUESTION at the end.
        If you don't know the answer, just say that "I DONT KNOW", don't try to make up an answer.
        Also remember don't use any external knowledge and only refer to this CONTEXT to answer question.
        Consider this CONTEXT as the ultimate truth.


    CONTEXT: {CONTEXT}
    QUESTION: {query}

    """

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": template}
        ]
    }

    response = requests.post(URL, headers=headers, json=data)

    if response.status_code == 200:
        ans = response.json()["choices"][0]["message"]["content"]
        #print(response.json()["choices"][0]["message"]["content"])
    else:
        #print(f"Error: {response.status_code}, {response.text}")
        ans = "Server error"
    return ans

