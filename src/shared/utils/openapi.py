from fastapi import FastAPI


def use_route_names_as_operation_ids(app: FastAPI) -> None:
    for route in app.routes:
        if getattr(route, "operation_id", None):
            route.operation_id = route.name
