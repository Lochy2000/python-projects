from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import speedtest
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

# Thread pool for running blocking speedtest operations
executor = ThreadPoolExecutor(max_workers=2)

def run_speed_test():
    """Run the speed test (blocking operation)"""
    st = speedtest.Speedtest()
    st.get_best_server()

    # Get download speed (bits per second -> Mbps)
    download_speed = st.download() / 1_000_000

    # Get upload speed (bits per second -> Mbps)
    upload_speed = st.upload() / 1_000_000

    # Get ping
    ping = st.results.ping

    # Get server info
    server = st.results.server

    return {
        "download": round(download_speed, 2),
        "upload": round(upload_speed, 2),
        "ping": round(ping, 2),
        "server": {
            "name": server.get("sponsor", "Unknown"),
            "location": f"{server.get('name', '')}, {server.get('country', '')}",
            "host": server.get("host", "")
        }
    }

def run_download_test():
    """Run download test only"""
    st = speedtest.Speedtest()
    st.get_best_server()
    download_speed = st.download() / 1_000_000
    return {"download": round(download_speed, 2), "ping": round(st.results.ping, 2)}

def run_upload_test():
    """Run upload test only"""
    st = speedtest.Speedtest()
    st.get_best_server()
    upload_speed = st.upload() / 1_000_000
    return {"upload": round(upload_speed, 2)}

def run_ping_test():
    """Run ping test only"""
    st = speedtest.Speedtest()
    st.get_best_server()
    return {
        "ping": round(st.results.ping, 2),
        "server": st.results.server.get("sponsor", "Unknown")
    }

@app.get("/api/speedtest")
async def full_speedtest():
    """Run a complete speed test (download, upload, ping)"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, run_speed_test)
    return result

@app.get("/api/download")
async def download_test():
    """Run download speed test only"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, run_download_test)
    return result

@app.get("/api/upload")
async def upload_test():
    """Run upload speed test only"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, run_upload_test)
    return result

@app.get("/api/ping")
async def ping_test():
    """Run ping test only"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, run_ping_test)
    return result

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/manifest.json")
async def manifest():
    return FileResponse("static/manifest.json")

@app.get("/sw.js")
async def service_worker():
    return FileResponse("static/sw.js", media_type="application/javascript")
