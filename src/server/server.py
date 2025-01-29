from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/test/{profile_name}")
async def run_profile(profile_name: str):
    return {"message": f"Profile {profile_name} is being launched"}


@app.get("/stop/{profile_name}")
async def stop_profile(profile_name: str):
    return {"message": f"Profile {profile_name} stopped"}


def run_fastapi_server(host: str = "0.0.0.0", port: int = 5001):
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_fastapi_server()
