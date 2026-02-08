from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Demarrage API...")
    await init_db()
    print("✅ Base de donnees OK")
    yield
    print("🛑 Arret API")

app = FastAPI(title="NEXUS GROUP API", version="1.0.0", lifespan=lifespan)

# CORS - Autoriser toutes les origines
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "NEXUS GROUP API", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}
