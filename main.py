from fastapi import FastAPI, Request, Header, Response, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional

from constants import ROOT_PATH
from utils import (
    formatsize,
    getFree,
    indicatorStyle,
    MagnetLink,
    PartialTorrent,
    torrentClient,
)

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
async def copy(request: Request, torrent: PartialTorrent, response: Response):
    id = torrent.id
    context = {"request": request, "rootPath": ROOT_PATH, "torrent": torrent}
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
