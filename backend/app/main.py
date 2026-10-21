import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.deps import get_current_user
from app.mqtt_service import is_mqtt_connected, start_mqtt, stop_mqtt
from app.routers import actions, auth, devices, sensors

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_mqtt()
    yield
    stop_mqtt()


app = FastAPI(
    title="Smart House IoT API",
    version="1.0.0",
    description="Backend điều khiển LED và giám sát cảm biến cho ESP32 qua MQTT.",
    lifespan=lifespan,
)

protected = [Depends(get_current_user)]

# Công khai: đăng nhập và kiểm tra sức khỏe server
app.include_router(auth.router)

# Yêu cầu token
app.include_router(devices.router, dependencies=protected)
app.include_router(sensors.router, dependencies=protected)
app.include_router(actions.router, dependencies=protected)


@app.get("/api/health", tags=["System"], summary="Kiểm tra server và kết nối MQTT")
def health():
    return {"status": "ok", "mqtt_connected": is_mqtt_connected()}