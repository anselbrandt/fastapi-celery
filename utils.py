import logging
import shutil
from stat import S_ISDIR, S_ISREG
import os

from pydantic import BaseModel
import paramiko
from transmission_rpc import Client

from constants import (
    REMOTE_HOST,
    TRANSMISSION_USERNAME,
    TRANSMISSION_PASSWORD,
    REMOTE_ROOT_PATH,
    LOCAL_ROOT_PATH,
    SSH_USERNAME,
    SSH_PASSWORD,
)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.FileHandler("logs.txt"), stream_handler],
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


def printTotals(transferred, toBeTransferred):
    if transferred == toBeTransferred:
        logging.info(f"done")


def copy_files(torrent: PartialTorrent):
    torrentClient = Client(
        host=REMOTE_HOST,
        port=9091,
        username=TRANSMISSION_USERNAME,
        password=TRANSMISSION_PASSWORD,
    )
    transport = paramiko.Transport((REMOTE_HOST, 22))
    inpath = f"{REMOTE_ROOT_PATH}/{torrent.name}"
    outpath = inToOut(REMOTE_ROOT_PATH, LOCAL_ROOT_PATH, inpath)
    transport.connect(None, SSH_USERNAME, SSH_PASSWORD)
    sftp = paramiko.SFTPClient.from_transport(transport)
    isFile, isDir = fileOrDir(sftp, inpath)
    if isDir:
        paths = listdir_r(sftp, inpath)
        for remotepath in paths:
            logging.info(f"{os.path.basename(remotepath)}")
            localpath = inToOut(REMOTE_ROOT_PATH, LOCAL_ROOT_PATH, remotepath)
            basedir = os.path.dirname(localpath)
            os.makedirs(basedir, exist_ok=True)
            sftp.get(
                remotepath,
                localpath,
                callback=printTotals,
            )
        sftp.close()
        transport.close()
        torrentClient.remove_torrent(torrent.id, delete_data=True)
    if isFile:
        logging.info(f"{os.path.basename(inpath)}")
        sftp.get(
            inpath,
            outpath,
            callback=printTotals,
        )
        sftp.close()
        transport.close()
        torrentClient.remove_torrent(torrent.id, delete_data=True)


def formatsize(num):
    if num < 1000000000:
        return f"{round(num / 1000000, 1)} MB"
    else:
        return f"{round(num / 1000000000, 2)} GB"


def getFree():
    total, used, free = shutil.disk_usage("/")
    return free
