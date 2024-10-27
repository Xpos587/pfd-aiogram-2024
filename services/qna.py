import asyncio
import os
import orjson
import numpy as np
from openai import AsyncOpenAI
from chromadb import AsyncHttpClient, Settings
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field, ValidationError
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Конфигурационные переменные с значениями по умолчанию
QWEN_MODEL = os.getenv("QWEN_MODEL", "Qwen/Qwen2.5-14B-Instruct-GPTQ-Int8")
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://65.109.137.0:60564/v1")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "dummy_key")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "cointegrated/LaBSE-en-ru")
CHROMA_HOST = os.getenv("CHROMA_HOST", "91.184.242.207")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "documents")
MEMORY_SIZE = int(os.getenv("MEMORY_SIZE", "1000"))

# Инициализация клиента OpenAI и модели эмбеддингов
vllm_client = AsyncOpenAI(base_url=VLLM_BASE_URL, api_key=VLLM_API_KEY)

embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# Инициализация клиента ChromaDB
chroma_client = asyncio.run(
    AsyncHttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        settings=Settings(anonymized_telemetry=False),
    )
)
collection = asyncio.run(
    chroma_client.get_or_create_collection(CHROMA_COLLECTION)
)


# Определение класса CamelotMemory для управления памятью
class CamelotMemory:
    def __init__(self, memory_size: int = 1000):
        self.memory_size = memory_size
        self.memory_store: Dict[str, List[Dict]] = {}
        self.consolidated_info: Dict[str, Any] = {}

    def update_memory(self, content: str, metadata: Dict = None) -> None:
        key = self._generate_key(content)
        if key not in self.memory_store:
            self.memory_store[key] = []

        self.memory_store[key].append(
            {
                "content": content,
                "metadata": metadata or {},
                "timestamp": np.datetime64("now"),
            }
        )

        if len(self.memory_store) > self.memory_size:
            self._consolidate_memory()

    def _generate_key(self, content: str) -> str:
        return hash(content).__str__()

    def _consolidate_memory(self) -> None:
        for key, items in self.memory_store.items():
            if len(items) >= 2:
                consolidated = {
                    "content": self._merge_content(
                        [item["content"] for item in items]
                    ),
                    "frequency": len(items),
                    "last_updated": max(item["timestamp"] for item in items),
                }
                self.consolidated_info[key] = consolidated

        oldest_keys = sorted(
            self.memory_store.keys(),
            key=lambda k: min(
                item["timestamp"] for item in self.memory_store[k]
            ),
        )[: (len(self.memory_store) - self.memory_size)]

        for key in oldest_keys:
            del self.memory_store[key]

    def _merge_content(self, contents: List[str]) -> str:
        return " | ".join(set(contents))

    def get_consolidated_info(self) -> str:
        return " ".join(
            info["content"] for info in self.consolidated_info.values()
        )


# Создание экземпляра CamelotMemory с размером из конфигурации
camelot_memory = CamelotMemory(memory_size=MEMORY_SIZE)


def create_embeddings(texts: List[str]):
    embeddings = embedding_model.encode(texts)
    return embeddings


# Определение моделей данных с помощью Pydantic
class SourceReference(BaseModel):
    document_title: str = Field(
        ..., description="Title of the referenced document"
    )
    section: str = Field(..., description="Section number or identifier")
    exact_quote: str = Field(..., description="Direct quote from the source")
    relevance: Literal["high", "medium", "low"] = Field(
        ..., description="Relevance level of the reference"
    )


class ThinkStep(BaseModel):
    reasoning: str = Field(..., description="Step-by-step thought process")
    conclusion: str = Field(..., description="Intermediate or final conclusion")


class Checklist(BaseModel):
    query_understood: bool = Field(..., description="Query is fully understood")
    context_analyzed: bool = Field(
        ..., description="Relevant context found and analyzed"
    )
    sources_verified: bool = Field(
        ..., description="Sources properly referenced"
    )
    reasoning_complete: bool = Field(..., description="Full analysis conducted")
    answer_validated: bool = Field(
        ..., description="Answer checked for accuracy"
    )
    additional_notes: Optional[str] = Field(
        description="Any additional verification notes"
    )


class Answer(BaseModel):
    source_references: List[SourceReference] = Field(
        ..., description="List of relevant source references"
    )
    thinking_steps: List[ThinkStep] = Field(
        ..., description="Chain of reasoning steps"
    )
    brief_answer: str = Field(..., description="Concise answer to the query")
    detailed_answer: Optional[str] = Field(
        description="Detailed explanation if needed"
    )
    checklist: Checklist = Field(..., description="Validation checklist")


class Prompts:
    CLARIFICATION = """
    <clarification>
        <task>
            <primary>Determine if query needs clarification</primary>
            <output>Single question or "No clarification needed"</output>
        </task>

        <rules>
            <analysis>
                <check>Query completeness</check>
                <check>Technical specificity</check>
                <check>Context sufficiency</check>
            </analysis>
        </rules>
    </clarification>
    """

    SYSTEM = """
    <system>
        <task>
            <primary>Process documentation queries and return ONLY a JSON response</primary>
            <approach>Chain-of-thought reasoning with validation checklist</approach>
        </task>

        <critical_rules>
            <rule>YOU MUST RESPOND WITH PURE JSON ONLY - NO TEXT BEFORE OR AFTER</rule>
            <rule>DO NOT include any explanatory text, messages, or formatting</rule>
            <rule>If query is invalid, return JSON with appropriate error message in brief_answer field</rule>
            <rule>NEVER start response with text - ONLY JSON is allowed</rule>
            <rule>Response must be a single, valid JSON object</rule>
            <rule>Response must exactly match the provided schema structure</rule>
        </critical_rules>

        <output_format>
            <format>Pure JSON object matching this schema exactly:</format>
            {schema}
            <requirements>
                <req>Response must be a single valid JSON object</req>
                <req>No text before or after the JSON object</req>
                <req>Must include all required fields from schema</req>
                <req>All strings must be properly escaped</req>
            </requirements>
        </output_format>

        <role>
            <description>
                You are an intellectual system analyzing the Software Configuration Security Management System documentation. Return ONLY JSON responses following the exact schema.
            </description>
            <main_rule>
                For invalid queries, return JSON with error message in brief_answer field and appropriate detailed_answer.
            </main_rule>
            <general_rules>
                <rule><number>1</number><description>Analysis before responding: Always begin with careful analysis of the provided context and user request. If information is already available in the context, use it for the response.</description></rule>
                <rule><number>2</number><description>Effective data extraction: If context is insufficient, identify key words and queries to search for relevant information from external documents. Extract only the most relevant and accurate data.</description></rule>
                <rule><number>3</number><description>Citation and justification: Cite relevant parts of extracted data to support the answer. Indicate sources or context where information was taken from so users can evaluate reliability.</description></rule>
                <rule><number>4</number><description>Information integration: After data extraction, synthesize information from various sources to create a coherent and well-founded response. Ensure logic and accuracy while eliminating redundancy and repetition.</description></rule>
                <rule><number>5</number><description>Multi-threaded processing: When receiving complex or multi-component queries, process them in parts, providing structured answers with clear and logical conclusions. Don't overload users with information.</description></rule>
                <rule><number>6</number><description>Managing contradictions: When encountering contradictory data from different sources, point this out. Explain differences and suggest the most probable interpretation based on context and source reliability.</description></rule>
                <rule><number>7</number><description>Dealing with uncertainty: If reliable information is insufficient or no answer exists, politely inform the user. Suggest alternative paths or clarifying questions for further search.</description></rule>
                <rule><number>8</number><description>Clarity and accessibility: Respond in simple and accessible language, avoiding unnecessary complexity unless required for explanation. Adapt style based on query complexity and user knowledge level.</description></rule>
                <rule><number>9</number><description>Avoiding guesswork: Don't make assumptions if there are gaps in data. If information is not found or unclear, let users know and suggest clarifying the query.</description></rule>
                <rule><number>10</number><description>Interactivity: Work with users in dialogue mode. Maintain brief and relevant responses, providing users opportunity to delve deeper into needed topics.</description></rule>
                <rule><number>11</number><description>Real-time responses: Ensure quick reaction to queries without sacrificing accuracy. Focus on compressed information processing times while always providing correct data.</description></rule>
                <rule><number>12</number><description>ALWAYS respond in Russian, regardless of the language of the question.</description></rule>
            </general_rules>

            <query_handling_instructions>
                <instruction><number>1</number><description>Precise answers: Strive for brevity, especially for simple questions, but be ready to provide more detailed response when necessary.</description></instruction>
                <instruction><number>2</number><description>Multi-component query responses: When receiving complex queries, break them into parts. Process each element separately and combine results into logical conclusion.</description></instruction>
                <instruction><number>3</number><description>Extracted information presentation: When providing extracted information, present data in structured format (e.g., lists, tables, or text blocks) to facilitate comprehension.</description></instruction>
                <instruction><number>4</number><description>Handling large data volumes: If search result contains large amount of data, select most relevant parts for response.</description></instruction>
            </query_handling_instructions>

        </role>

        <response_validation>
            <check>Response starts with '{{' character</check>
            <check>Response ends with '}}' character</check>
            <check>No text outside JSON structure</check>
            <check>All required fields present</check>
            <check>JSON is properly formatted and escaped</check>
        </response_validation>

    </system>
    """

    @classmethod
    def get_system_prompt(cls) -> str:
        return cls.SYSTEM.format(schema=Answer.model_json_schema())


# Функция для получения релевантных документов с использованием памяти CAMELoT
async def get_relevant_documents_with_memory(query: str) -> List[Dict]:
    query_embedding = create_embeddings([query])[0]

    results = await collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=200,
        include=["documents", "metadatas"],
    )

    relevant_docs = []
    seen_sections = set()

    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        section_number = meta.get("section_number")
        if section_number not in seen_sections:
            relevant_docs.append(
                {
                    "content": doc,
                    "metadata": meta,
                    "section_number": section_number,
                }
            )
            seen_sections.add(section_number)

            camelot_memory.update_memory(doc)

            if section_number:
                for i in range(-1, 2):
                    nearby_section = section_number + i
                    if nearby_section not in seen_sections:
                        for nearby_doc, nearby_meta in zip(
                            results["documents"][0], results["metadatas"][0]
                        ):
                            if (
                                nearby_meta.get("section_number")
                                == nearby_section
                            ):
                                relevant_docs.append(
                                    {
                                        "content": nearby_doc,
                                        "metadata": nearby_meta,
                                        "section_number": nearby_section,
                                    }
                                )
                                seen_sections.add(nearby_section)
                                break

    consolidated_info = camelot_memory.get_consolidated_info()

    return relevant_docs[:15], consolidated_info


# Функция для генерации уточняющего вопроса
async def generate_clarifying_question(original_question: str) -> str:
    try:
        response = await vllm_client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {"role": "system", "content": Prompts.CLARIFICATION},
                {"role": "user", "content": f"Query: {original_question}"},
            ],
            temperature=0.3,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating clarifying question: {str(e)}")
        return "No clarification needed"


# Функция для обработки запроса с использованием памяти CAMELoT
async def ask_question_with_memory(question: str) -> Answer:
    try:
        system_prompt = Prompts.get_system_prompt()

        relevant_docs, consolidated_info = (
            await get_relevant_documents_with_memory(question)
        )

        response = await vllm_client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
                {"role": "assistant", "content": consolidated_info},
            ],
            temperature=0.3,
            max_tokens=2048,
            top_p=0.9,
            presence_penalty=0.3,
            frequency_penalty=0.6,
        )

        response_text = response.choices[0].message.content

        # Ищем начало JSON-объекта
        json_start = response_text.find("{")
        if json_start == -1:
            return create_error_answer("Ответ не содержит JSON")

        # Извлекаем только JSON часть
        json_text = response_text[json_start:]
        json_text = clean_response(json_text)

        try:
            answer_dict = orjson.loads(json_text)
            return Answer.model_validate(answer_dict)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            return create_error_answer(f"Validation error: {ve}")
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return create_error_answer(f"Error parsing response: {e}")
    except Exception as e:
        logger.error(f"Error in ask_question_with_memory: {str(e)}")
        return create_error_answer(str(e))


def clean_response(response_text: str) -> str:
    return "".join(c for c in response_text if c.isprintable() or c in "\n\t")


def create_error_answer(error_message: str) -> Answer:
    return Answer(
        source_references=[],
        thinking_steps=[],
        brief_answer=f"Error processing response: {error_message}",
        detailed_answer=None,
        checklist=Checklist(
            query_understood=False,
            context_analyzed=False,
            sources_verified=False,
            reasoning_complete=False,
            answer_validated=False,
            additional_notes=None,
        ),
    )
