from main import app
from fastapi.routing import APIRoute, APIRouter

def find_routes(routes, prefix="", depth=0):
    for route in routes:
        rtype = type(route).__name__
        rpath = getattr(route, 'path', '?')
        rmethods = getattr(route, 'methods', None)
        if depth == 0:
            print(f"  [{rtype}] path={rpath} methods={rmethods}")
        if isinstance(route, APIRoute):
            path = prefix + route.path
            if 'review' in path or 'badge' in path or 'bookmark' in path:
                print(f'  FOUND: {route.methods} {path}')
        if hasattr(route, 'routes'):
            new_prefix = prefix + (getattr(route, 'prefix', '') or '')
            find_routes(route.routes, new_prefix, depth+1)

print(f"Total top-level routes: {len(app.routes)}")
find_routes(app.routes)
print("Done!")
