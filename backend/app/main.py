import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.mqtt_service import is_mqtt_connected, start_mqtt, stop_mqtt
from app.routers import actions, devices, sensors

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Chạy khi server khởi động: bật MQTT
    start_mqtt()
    yield
    # Chạy khi server tắt: ngắt MQTT
    stop_mqtt()


app = FastAPI(
    title="Smart House IoT API",
    version="1.0.0",
    description="Backend điều khiển LED và giám sát cảm biến cho ESP32 qua MQTT.",
    lifespan=lifespan,
)

app.include_router(devices.router)
app.include_router(sensors.router)
app.include_router(actions.router)


@app.get("/api/health", tags=["System"], summary="Kiểm tra server và kết nối MQTT")
def health():
    return {
        "status": "ok",
        "mqtt_connected": is_mqtt_connected()
    }