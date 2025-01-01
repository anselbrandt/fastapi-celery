import shutil
from stat import S_ISDIR, S_ISREG

from pydantic import BaseModel
import paramiko
from transmission_rpc import Client

from constants import (
    REMOTE_HOST,
    TRANSMISSION_USERNAME,
    TRANSMISSION_PASSWORD,
)

torrentClient = Client(
    host=REMOTE_HOST,
    port=9091,
    username=TRANSMISSION_USERNAME,
    password=TRANSMISSION_PASSWORD,
)
transport = paramiko.Transport((REMOTE_HOST, 22))


def indicatorStyle(status):
    if status == "seeding":
        return "flex w-3 h-3 me-3 bg-green-500 rounded-full"
    if status == "downloading":
        return "flex w-3 h-3 me-3 bg-blue-600 rounded-full"
    else:
        return "flex w-3 h-3 me-3 bg-gray-200 rounded-full"


class MagnetLink(BaseModel):
    url: str


class PartialTorrent(BaseModel):
    name: str
    id: str


def listdir_r(sftp, remotedir, paths=[]):
    all_paths = paths
    for entry in sftp.listdir_attr(remotedir):
        remotepath = remotedir + "/" + entry.filename
        mode = entry.st_mode
        if S_ISDIR(mode):
            listdir_r(sftp, remotepath)
        elif S_ISREG(mode):
            all_paths.append(remotepath)
    return all_paths


def fileOrDir(sftp, inpath):
    stat = sftp.stat(inpath)
    isFile = S_ISREG(stat.st_mode)
    isDir = S_ISDIR(stat.st_mode)
    return (isFile, isDir)


def inToOut(remote_root, local_root, path):
    outpath = path.replace(remote_root, local_root)
    return outpath


def formatsize(num):
    if num < 1000000000:
        return f"{round(num / 1000000, 1)} MB"
    else:
        return f"{round(num / 1000000000, 2)} GB"


def getFree():
    total, used, free = shutil.disk_usage("/")
    return free
