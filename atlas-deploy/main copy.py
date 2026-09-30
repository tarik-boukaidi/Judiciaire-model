from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag import LegalRAGPipeline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the pipeline
print("Loading Model... this might take a moment.")
rag_pipeline = LegalRAGPipeline()
print("Model Ready!")

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        reply = rag_pipeline.generate_answer(request.message)
        return {"reply": reply}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Run the API on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
