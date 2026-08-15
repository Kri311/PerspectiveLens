from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from app.models import nlp_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PerspectiveLens NLP Engine")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up NLP Engine...")
    # Preload models during startup to prevent first-request latency
    nlp_models.load_models()

class TextRequest(BaseModel):
    text: str

@app.post("/embed")
async def get_embedding(request: TextRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    try:
        embedding = nlp_models.get_embedding(request.text)
        return {"embedding": embedding, "dimensions": len(embedding)}
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ner")
async def get_ner(request: TextRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    try:
        entities = nlp_models.get_entities(request.text)
        return {"entities": entities}
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sentiment")
async def get_sentiment(request: TextRequest):
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
async def get_framing(request: TextRequest):
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
async def get_stance(request: StanceRequest):
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
async def get_nli(request: NLIRequest):
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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
