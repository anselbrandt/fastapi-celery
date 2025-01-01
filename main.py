import json
from typing import Optional

from fastapi import FastAPI, Request, Header, Response, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import redis

from constants import ROOT_PATH
from tasks import copyFile
from utils import (
    formatsize,
    getFree,
    indicatorStyle,
    MagnetLink,
    torrentClient,
)

cache = redis.Redis(decode_responses=True)

app = FastAPI(root_path=ROOT_PATH)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, hx_request: Optional[str] = Header(None)):
    torrents = torrentClient.get_torrents()
    context = {
        "request": request,
        "rootPath": ROOT_PATH,
        "torrents": torrents,
        "indicatorStyle": indicatorStyle,
        "formatsize": formatsize,
    }
    return templates.TemplateResponse("index.html", context)


@app.post("/add")
async def add(magnetlink: MagnetLink):
    try:
        url = magnetlink.url
        res = torrentClient.add_torrent(url)
        return res.name
    except Exception as error:
        print(str(error))
        return str(error)


@app.delete("/delete/{id}")
async def delete(id, response: Response):
    try:
        torrentClient.remove_torrent(id, delete_data=True)
        response.status_code = status.HTTP_200_OK
        return response
    except Exception as error:
        print(str(error))
        return str(error)


@app.post("/copy/")
async def copy(request: Request):
    torrent = await request.json()
    payload = {"id": torrent["id"], "name": torrent["name"]}
    res = copyFile.delay(payload)
    id = res.task_id
    progress = {"transferred": 0, "total": 0}
    cache.set(id, json.dumps(progress))
    context = {"request": request, "rootPath": ROOT_PATH, "id": id, "torrent": torrent}
    return templates.TemplateResponse("copying.html", context)


@app.get("/free")
async def free(request: Request, response: Response):
    freepace = getFree()
    context = {
        "request": request,
        "rootPath": ROOT_PATH,
        "freespace": round(freepace / (2**30), 1),
    }
    return templates.TemplateResponse("freespace.html", context)


@app.get("/task/progress/{id}")
async def task(
    request: Request,
    response: Response,
    id: str,
    hx_request: Optional[str] = Header(None),
):
    result = cache.get(id)
    data = json.loads(result)
    transferred, total = data.values()
    progress = 0 if total == 0 else round((transferred / total) * 100)
    if progress < 100:
        context = {
            "request": request,
            "rootPath": ROOT_PATH,
            "progress": progress,
            "id": id,
        }
        return templates.TemplateResponse("progress.html", context)
    if progress == 100:
        context = {
            "request": request,
            "rootPath": ROOT_PATH,
            "progress": progress,
            "id": id,
        }
        response.headers["HX-Trigger"] = "done"
        return templates.TemplateResponse(
            "progress.html", context, headers=response.headers
        )


@app.get("/task/{id}")
async def task(
    request: Request,
    response: Response,
    id: str,
    hx_request: Optional[str] = Header(None),
):
    context = {"request": request, "rootPath": ROOT_PATH, "id": id}
    return templates.TemplateResponse("copycomplete.html", context)
