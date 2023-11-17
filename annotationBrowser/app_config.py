import dash
from dash.long_callback import (
    CeleryLongCallbackManager,
)
import dash_bootstrap_components as dbc

# from settings import REDIS_URL

# Use Redis & Celery if REDIS_URL set as an env variable
# from celery import Celery

# print("Trying to connect to", REDIS_URL)
# celery_app = Celery(
#     __name__,
#     broker=REDIS_URL + "/0",
#     backend=REDIS_URL + "/1",
# )

# background_callback_manager = CeleryLongCallbackManager(celery_app)

# # else:
# #     # Diskcache for non-production apps when developing locally
# #     import diskcache

# #     cache = diskcache.Cache("./cache")
# #     background_callback_manager = DiskcacheManager(cache)

# print(background_callback_manager)


## This creates a single dash instance that I can access from multiple modules
class SingletonDashApp:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(SingletonDashApp, cls).__new__(cls)

            # Initialize your Dash app here
            cls._instance.app = dash.Dash(
                __name__,
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP,
                    dbc.icons.FONT_AWESOME,
                ],
                title="NeuroTK Dashboard",
            )
        return cls._instance


app = SingletonDashApp().app
