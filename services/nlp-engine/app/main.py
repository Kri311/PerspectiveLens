from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import glob
import os
from app.models import nlp_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PerspectiveLens NLP Engine")

@app.on_event("startup")
async def startup_event():
    logger.info("Cleaning up HuggingFace cache locks...")
    for lock_file in glob.glob("/root/.cache/huggingface/hub/**/*.lock", recursive=True):
        try:
            os.remove(lock_file)
            logger.info(f"Removed ghost lock: {lock_file}")
        except Exception as e:
            logger.error(f"Failed to remove lock {lock_file}: {e}")
            
    logger.info("Starting up NLP Engine...")
    # Models are now strictly lazy-loaded to prevent OOM
    pass

class TextRequest(BaseModel):
    text: str

@app.post("/embed")
def get_embedding(request: TextRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    try:
        embedding = nlp_models.get_embedding(request.text)
        return {"embedding": embedding, "dimensions": len(embedding)}
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ner")
def get_ner(request: TextRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    try:
        entities = nlp_models.get_entities(request.text)
        return {"entities": entities}
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sentiment")
def get_sentiment(request: TextRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    try:
        labels = ["Positive", "Negative", "Neutral"]
        result = nlp_models.get_classification(request.text, labels)
        
        # Determine top sentiment
        top_sentiment = result["labels"][0]
        confidence = result["scores"][0]
        
        return {
            "sentiment": top_sentiment.upper(),
            "confidence": confidence,
            "raw": result
        }
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/framing")
def get_framing(request: TextRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    try:
        # Define the set of media frames
        labels = [
            "Economic", 
            "Political Strategy", 
            "Policy/Achievement", 
            "Social Justice", 
            "Law and Order",
            "Controversy/Scandal"
        ]
        result = nlp_models.get_classification(request.text, labels)
        
        # Return probability distribution across frames
        distribution = {label: score for label, score in zip(result["labels"], result["scores"])}
        
        return {
            "top_frame": result["labels"][0],
            "distribution": distribution
        }
    except Exception as e:
        logger.error(f"Error analyzing framing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class StanceRequest(BaseModel):
    text: str
    target_entity: str

@app.post("/stance")
def get_stance(request: StanceRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    if not request.target_entity or not request.target_entity.strip():
        raise HTTPException(status_code=400, detail="Target entity cannot be empty")
        
    try:
        # Construct the premise for zero-shot classification
        premise = f"The stance of this text towards {request.target_entity} is"
        labels = ["Support", "Oppose", "Neutral"]
        
        # We append the premise to the text to give context to the model
        contextualized_text = f"{request.text}. {premise}"
        
        result = nlp_models.get_classification(contextualized_text, labels)
        
        top_stance = result["labels"][0]
        confidence = result["scores"][0]
        
        return {
            "stance": top_stance.upper(),
            "confidence": confidence,
            "target_entity": request.target_entity,
            "raw": result
        }
    except Exception as e:
        logger.error(f"Error analyzing stance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class NLIRequest(BaseModel):
    premise: str
    hypothesis: str

@app.post("/nli")
def get_nli(request: NLIRequest):
    if not request.premise or not request.premise.strip():
        raise HTTPException(status_code=400, detail="Premise cannot be empty")
    if not request.hypothesis or not request.hypothesis.strip():
        raise HTTPException(status_code=400, detail="Hypothesis cannot be empty")
        
    try:
        result = nlp_models.get_nli(request.premise, request.hypothesis)
        return result
    except Exception as e:
        logger.error(f"Error analyzing NLI: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize")
async def generate_summary(payload: dict):
    """
    Generates an abstractive summary in Tamil using mT5.
    Expects structured evidence concatenated into a prompt.
    """
    text = payload.get("text", "")
    max_length = payload.get("max_length", 150)
    
    if not text:
        raise HTTPException(status_code=400, detail="Missing text")
        
    try:
        from app.summarization.mt5_summarizer import summarizer_instance
        summary = summarizer_instance.summarize(text, max_length=max_length)
        return {"summary": summary}
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
