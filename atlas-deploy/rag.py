import torch
import os
import json
import hashlib
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

class LegalRAGPipeline:
    def __init__(self):
        # We load the standard unquantized base model for CPU deployment
        self.base_model_name = "Qwen/Qwen2.5-3B-Instruct" 
        
        self.max_seq_length = 2048
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.local_dir = os.path.join(base_dir, 'models', 'lora')
        self.model = None
        self.tokenizer = None
        self.vector_store = None
        
        # 1. Setup Model
        self._load_model()
        # 2. Setup RAG
        self._setup_rag()

    def _load_model(self):
        print(f"Loading base model {self.base_model_name} on CPU...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_name)
        
        # Load base model in float32 for CPU compatibility
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            torch_dtype=torch.float32,
            device_map="cpu"
        )
        
        print(f"Applying LoRA adapter from: {self.local_dir}")
        # Apply LoRA fine-tuning weights onto the base model
        self.model = PeftModel.from_pretrained(base_model, self.local_dir)
        print("Model loaded successfully on CPU.")

    def _setup_rag(self):
        base_dir = Path(__file__).resolve().parent
        local_data_dir = base_dir / "data"
        data_dirs = [local_data_dir if local_data_dir.is_dir() else base_dir.parent / "data"]
        data_dirs = [path.resolve() for path in data_dirs if path.is_dir()]

        pdf_paths = sorted({
            path.resolve()
            for data_dir in data_dirs
            for path in data_dir.rglob("*")
            if path.is_file() and path.suffix.lower() == ".pdf"
        })
        jsonl_paths = [
            data_dir / "final_frensh_arabic_training_dataset.jsonl"
            for data_dir in data_dirs
            if (data_dir / "final_frensh_arabic_training_dataset.jsonl").is_file()
        ]
        source_paths = sorted(set(pdf_paths + [path.resolve() for path in jsonl_paths]))
        if not source_paths:
            print("Warning: no PDFs or JSONL dataset found under the project data directories.")
            return

        documents = []
        for path in source_paths:
            if path.suffix.lower() == ".pdf":
                try:
                    pages = PyPDFLoader(str(path)).load()
                    for page in pages:
                        page_number = int(page.metadata.get("page", 0)) + 1
                        page.page_content = (
                            f"[Source: {path.name}, page {page_number}]\n{page.page_content}"
                        )
                    documents.extend(page for page in pages if page.page_content.strip())
                    print(f"Loaded {len(pages)} pages from {path.name}.")
                except Exception as exc:
                    print(f"Warning: could not extract PDF {path}: {exc}")
            else:
                print(f"Loading JSONL data from: {path}")
                with path.open("r", encoding="utf-8") as file:
                    for line_number, line in enumerate(file, start=1):
                        if not line.strip():
                            continue
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError as exc:
                            print(f"Warning: skipping invalid JSON at {path}:{line_number}: {exc}")
                            continue
                        question = record.get("input", "")
                        answer = record.get("output", "")
                        if question or answer:
                            documents.append(Document(
                                page_content=(
                                    f"[Source: {path.name}]\nQuestion: {question}\nAnswer: {answer}"
                                ),
                                metadata={"source": str(path), "source_type": "jsonl"},
                            ))

        if not documents:
            print("Warning: no readable text was extracted from the PDFs or JSONL dataset.")
            return

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=180)
        docs = splitter.split_documents(documents)
        print(f"Split {len(documents)} source documents into {len(docs)} chunks.")

        embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
        # Multilingual E5 is trained with passage/query prefixes for retrieval.
        for doc in docs:
            doc.page_content = f"passage: {doc.page_content}"

        index_dir = data_dirs[0] / "faiss_index"
        manifest_path = index_dir / "sources.sha256"
        digest = hashlib.sha256()
        digest.update(b"rag-index-v2|multilingual-e5-large|passage-query-prefix|chunk=1000|overlap=180")
        for path in source_paths:
            digest.update(path.name.encode("utf-8"))
            with path.open("rb") as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(block)
        source_hash = digest.hexdigest()

        index_is_current = (
            manifest_path.is_file()
            and manifest_path.read_text(encoding="ascii").strip() == source_hash
            and (index_dir / "index.faiss").is_file()
            and (index_dir / "index.pkl").is_file()
        )
        if index_is_current:
            print("Loading cached FAISS index for current PDF/JSONL files.")
            self.vector_store = FAISS.load_local(
                str(index_dir), embeddings, allow_dangerous_deserialization=True
            )
            return

        print("Building FAISS index from PDFs and JSONL; first startup can take a while.")
        self.vector_store = FAISS.from_documents(docs, embeddings)
        index_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store.save_local(str(index_dir))
        manifest_path.write_text(source_hash, encoding="ascii")

    def generate_answer(self, question: str, max_new_tokens: int = 512):
        if self.vector_store is None:
            return "RAG not initialized."

        retriever = self.vector_store.as_retriever(search_kwargs={"k": 6})
        docs = retriever.invoke(f"query: {question}")

        if not docs:
            return "Information not found in legal context."

        docs = docs[:6]

        context = "\n\nLEGAL CONTEXT:\n"
        context += "\n---\n".join(
            doc.page_content.removeprefix("passage: ") for doc in docs
        )

        print("\n========== RETRIEVED CONTEXT ==========")
        print(context)
        print("=======================================\n")
        
        system_prompt = """You are a Moroccan legal assistant specialized ONLY in Moroccan law.

            STRICT RULES FOR GREETINGS:
            - You are allowed to respond to basic polite greetings (like "hi", "hello", "مرحبا", "bonjour") naturally and politely in the same language the user used.
            - After greeting the user, politely ask them how you can assist them with Moroccan law.

            STRICT RULES FOR LEGAL ANSWERS:
            - Answer ONLY questions related to Moroccan law and legal matters.
            - If the user asks a non-legal question (after the initial greeting), refuse politely.
            - Do NOT invent laws, article numbers, or legal sources.
            - If the legal information is uncertain or missing from the context, say:
            "I do not have enough verified legal information to answer accurately."
            - Use ONLY the provided legal context when available.
            - If the answer is not present in the retrieved context, say so clearly.
            - Always answer in the same language as the user.
            - Keep answers concise, professional, and legally focused.
            - Cite source filenames and PDF page numbers when they appear in the retrieved context.
            - Do not invent a page number or citation that is absent from the context.
            - Mention the law/article ONLY if explicitly present in the context.
            - Never fabricate article numbers.
            - Your responses are for legal information only and do not replace a lawyer.
        """
        messages = [
            {"role": "system", "content": system_prompt + context},
            {"role": "user", "content": question}
        ]
        
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # Removed .to("cuda") so it processes using the CPU
        inputs = self.tokenizer([prompt], return_tensors="pt").to("cpu")
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs, 
                max_new_tokens=max_new_tokens,
                do_sample=False,
                repetition_penalty=1.15,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
            
        generated_tokens = outputs[0][inputs['input_ids'].shape[-1]:]
        return self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
