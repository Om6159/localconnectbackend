from fastapi import APIRouter

from app.api.v1 import (
    auth,
    profiles,
    categories,
    services,
    providers,
    requests,
    matches,
    connections,
    reviews,
    trust,
    recommendations,
    saved_providers,
    search,
    notifications,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(profiles.router)
api_router.include_router(categories.router)
api_router.include_router(services.router)
api_router.include_router(providers.router)
api_router.include_router(requests.router)
api_router.include_router(matches.router)
api_router.include_router(connections.router)
api_router.include_router(reviews.router)
api_router.include_router(trust.router)
api_router.include_router(recommendations.router)
api_router.include_router(saved_providers.router)
api_router.include_router(search.router)
api_router.include_router(notifications.router)
