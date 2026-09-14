from typing import Annotated

from fastapi import Depends

from app.internal.clients import (
    GozeroClient,
    NestjsClient,
    SpringClient,
    get_gozero_client,
    get_nestjs_client,
    get_spring_client,
)

GozeroClientDep = Annotated[GozeroClient, Depends(get_gozero_client)]
NestjsClientDep = Annotated[NestjsClient, Depends(get_nestjs_client)]
SpringClientDep = Annotated[SpringClient, Depends(get_spring_client)]
