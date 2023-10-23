import dash
from dash.long_callback import (
    DiskcacheLongCallbackManager,
    CeleryLongCallbackManager,
    DiskcacheManager,
    CeleryManager,
)
import dash_bootstrap_components as dbc
import diskcache

## Could/should check if redis is avialable

REDIS_URL = "redis://redis:6379"
# REDIS_URL = None

if REDIS_URL:
    # Use Redis & Celery if REDIS_URL set as an env variable
    from celery import Celery

    celery_app = Celery(__name__, broker=REDIS_URL, backend=REDIS_URL, include=["app"])
    background_callback_manager = CeleryManager(celery_app)
    print("Loading redis background")

else:
    # Diskcache for non-production apps when developing locally
    import diskcache

    cache = diskcache.Cache("./cache")
    background_callback_manager = DiskcacheManager(cache)

print(background_callback_manager)


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


# cache = diskcache.Cache("./neurotk-cache", timeout=5)
# lcm = DiskcacheLongCallbackManager(cache)

# cache = diskcache.Cache("./neurotk-cache-directory")
# background_callback_manager = dash.DiskcacheManager(cache)


app = SingletonDashApp().app
