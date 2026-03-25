from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import logging
from models import InitializeTripRequest, InitializeTripResponse, ChatRequest, ChatResponse, SynthesizeRequest, SynthesizeResponse
from services.trip_service import get_trip_service
from services.chat_service import get_chat_service
from services.synthesis_service import get_synthesis_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Travel App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An internal error occurred. Please try again.",
            "detail": str(exc)
        }
    )

@app.get("/")
def read_root():
    return {"message": "Travel App API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/trip/initialize", response_model=InitializeTripResponse)
def initialize_trip(request: InitializeTripRequest):
    try:
        logger.info(f"Initializing trip: {request.cities}")
        trip_service = get_trip_service()
        result = trip_service.initialize_trip(request)
        
        return InitializeTripResponse(
            success=True,
            message=result["message"],
            trip_id=result["trip_id"]
        )
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error initializing trip: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        logger.info(f"Chat request stream: {request.message[:50]}...")
        chat_service = get_chat_service()
        return StreamingResponse(chat_service.process_message_stream(request), media_type="text/event-stream")
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in chat stream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/itinerary/synthesize", response_model=SynthesizeResponse)
def synthesize_itinerary(request: SynthesizeRequest):
    try:
        logger.info(f"Synthesizing itinerary with {len(request.places)} places")
        synthesis_service = get_synthesis_service()
        itinerary = synthesis_service.synthesize(request)
        
        return SynthesizeResponse(
            success=True,
            message="Itinerary synthesized successfully",
            itinerary=itinerary
        )
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error synthesizing itinerary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
