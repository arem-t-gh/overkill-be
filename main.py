from api.router_handler import register_routers
from app import app
from exception_handlers import register_exception_handlers

register_routers(app)

register_exception_handlers(app)
