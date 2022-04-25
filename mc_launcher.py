"""
    usage: fill the `mc_launcher.json` with the following arguments:
        - minecraft_path: the path of `.minecraft` floder
        - platform: the operating system of the machine (windows, linux, osx)
        - version: the version of the minecraft (see .minecraft/versions/ floder)
"""

import asyncio
import aiohttp
import os
import platform
from io import BytesIO
from requests import get
from icecream import ic
from json import loads
from hashlib import sha1
from zipfile import ZipFile

DEBUG = False
USE_ABS_PATH = False
DOWNLOAD_NATIVE = False
ASYNC_DOWNLOADE = True

RED = '\033[91m'
GREEN = '\033[32m'
RESET = '\033[0m'
BLUE = '\033[94m'

# load launcher settings
if os.path.exists('mc_launcher.json'):
    with open('mc_launcher.json', 'r', encoding='utf8') as f:
        settings = loads(f.read())
else:
    settings = {}

minecraft_path = settings['minecraft_path']  if 'minecraft_path' in settings  else '.'
version_name = settings['version_name'] if 'version_name' in settings else '1.12.2'

# get platform
platform = platform.system().lower().replace('darwin', 'osx')  # linux, windows, osx
if platform not in ['linux', 'windows', 'osx']:
    print(f'{RED}platform [{platform}] not supported{RESET}')
    exit(1)

# version path
versions_path = f'{minecraft_path}/versions'
version_path = f'{versions_path}/{version_name}'
version_json_path = f'{version_path}/{version_name}.json'
# lib path
artifacts_path = f'{minecraft_path}/libraries'
# native_path = f'{version_path}/natives-{platform}'
native_path = f'{version_path}/{version_name}-natives'

client_path = f"{version_path}/{version_name}.jar"

class Downloader:
    def __init__(self) -> None:
        self.tasks = []

    def add_task(self, url, path, is_native_, size, exclude=['META-INF/']):
        self.tasks.append((url, path, is_native_, size, exclude))

    @staticmethod
    def parse(content, path, is_native, exclude=['META-INF/']):
        # parse file
        with open(path, 'wb') as f:
            f.write(content)
        if is_native:
            zip_file = ZipFile(BytesIO(content), 'r')
            for file in zip_file.namelist():
                for each in exclude:
                    if each in file:
                        break;
                else:
                    print(f'{BLUE}extracting [{native_path}/{file}]{RESET}')
                    zip_file.extract(file, native_path)

    def download_async(self):
        async def f():
            async with aiohttp.ClientSession() as session:
                ts = []
                for url, path, is_native, size, exclude in self.tasks:
                    async def f2(_url, _path, _is_native, _size, _exclude):
                        async with session.get(_url) as resp:
                            print(f'{BLUE}downloaded [{_url}] to [{_path}] {_size/1024:.2f}KB{RESET}')
                            resp.raise_for_status()
                            content = await resp.read()
                            self.parse(content, _path, _is_native, _exclude)
                    ts.append(asyncio.create_task(f2(url, path, is_native, size, exclude)))
                for each in ts:
                    await each
        asyncio.run(f())
    
    def download(self):
        print("{RED}downloading libs, please wait...{RESET}")
        for url, path, is_native, size, exclude in self.tasks:
            print(f'{BLUE}downloading [{url}] to [{path}] {size/1024:.2f}KB{RESET}')
            resp = get(url)
            resp.raise_for_status()
            self.parse(resp.content, path, is_native, exclude)


# def download_lib(url, path, is_native, size, exclude=['META-INF/']):
#     # download file
#     print(f'{BLUE}downloading [{url}] to [{path}] {size/1024:.2f}KB{RESET}')
#     resp = get(url)
#     resp.raise_for_status()
#     with open(path, 'wb') as f:
#         f.write(resp.content)
#     if is_native:
#         zip_file = ZipFile(BytesIO(resp.content), 'r')
#         for file in zip_file.namelist():
#             for each in exclude:
#                 if each in file:
#                     break;
#             else:
#                 print(f'{BLUE}extracting [{native_path}/{file}]{RESET}')
#                 zip_file.extract(file, native_path)

downloader = Downloader()

artifact_lib_paths = []

with open(version_json_path, encoding='utf8') as f:
    data = loads(f.read())

print(f'{BLUE}total libraries: [{len(data["libraries"])}]{RESET}')

for library in data['libraries']:
    print(f'{GREEN}parsing library: [{library["name"]}]{RESET}')
    downloads = library['downloads']
    package, nam, ver = library['name'].split(':')

    paths = package.split('.')
    paths.append(nam)
    paths.append(ver)
    save_dir = f'{artifacts_path}'
    for path in paths:
        save_dir = f'{save_dir}/{path}'
        if not os.path.exists(save_dir):
            if DEBUG:
                print(f"{RED}creating dir: {save_dir}{RESET}")
            os.mkdir(save_dir)


    save_path = f'{save_dir}/{nam}-{ver}.jar'
    if DEBUG:
        print(f'{BLUE}save_dir: {save_dir}{RESET}')
        print(f'{BLUE}save_path: {save_path}{RESET}')

    # parse artifact
    if 'artifact' in downloads:
        artifact_lib_paths.append(save_path)
        _download = True
        # compute sha1
        if os.path.exists(save_path):
            sha1obj = sha1()
            with open(save_path, 'rb') as f:
                sha1obj.update(f.read())
            if sha1obj.hexdigest() != downloads['artifact']['sha1']:
                _download = True
                print(f'{RED}[{save_path}] already exists but sha1 is error, Redownload...{RESET}')
            else:
                _download = False
        artifact_url = downloads['artifact']['url']
        if _download:
            downloader.add_task(artifact_url, save_path, False, downloads['artifact']['size'])

    # parse natives
    if 'natives' in library and platform in library['natives']:
        native_name = library['natives'][platform]
        if f'natives-{platform}' in downloads['classifiers']:
            _native_path = f'{save_dir}/{nam}-{ver}-natives-{platform}.jar'
            native_url = downloads['classifiers'][f'natives-{platform}']['url']
            native_size = downloads['classifiers'][f'natives-{platform}']['size']
            if not os.path.exists(_native_path) or DOWNLOAD_NATIVE:
                downloader.add_task(native_url, _native_path, True, native_size)

# launch downloader
if ASYNC_DOWNLOADE:
    downloader.download_async()
else:
    downloader.download()

# jvm setting
prefix = 'prime-run'
jvm = 'java'
# jvm_opts = '-Xmx1024M'
jvm_opts = ''
djava = os.path.abspath(native_path) if USE_ABS_PATH else native_path

# classpath setting
cp = ''
print()
print(f'{BLUE}print classpath: {RESET}')

# generate classpath
for each in [*artifact_lib_paths, client_path]:
    if USE_ABS_PATH:
        temp = os.path.abspath(each)
    else:
        temp = each
    if os.path.exists(temp):
        exsisted = f"{BLUE}Exsisted{RESET}"
    else:
        exsisted = f"{RED}Not Exsisted{RESET}"
    print(f'{GREEN}{temp} {exsisted}{RESET}')
    cp = f'{cp}{temp}' + (';' if platform == 'windows' else ':')

# minecraft setting
auth_player_name = 'notnotype'
version_name = 'python mc launcher'
game_directory = os.path.abspath(minecraft_path) if USE_ABS_PATH else minecraft_path
assets_index_name = data['assetIndex']['id']
assets_root = os.path.abspath(f'{minecraft_path}/assets') if USE_ABS_PATH else f'{minecraft_path}/assets'
auth_uuid = 'd8709223-9e1b-416c-b68b-e33bae70c8b0'
auth_access_token = 'eyJhbGciOiJIUzI1NiJ9.eyJ4dWlkIjoiMjUzNTQ0MzIwMzgyOTI3NyIsImFnZyI6IkFkdWx0Iiwic3ViIjoiODQzN2Q5OTYtNGE0Mi00YmNiLTk0NzItZWQ3YzY3ZjU4OTYzIiwibmJmIjoxNjQ5NzU2OTQzLCJhdXRoIjoiWEJPWCIsInJvbGVzIjpbXSwiaXNzIjoiYXV0aGVudGljYXRpb24iLCJleHAiOjE2NDk4NDMzNDMsImlhdCI6MTY0OTc1Njk0MywicGxhdGZvcm0iOiJVTktOT1dOIiwieXVpZCI6IjI1MTJkOWJmMTE0MjY5MGJhNDQ0NDMzMzU2YmYzNWZkIn0.pk84JYwdSpK8KdMank0F5IFkm1glGj1uu9GGAbKpjH4'
user_properties = '{}'
user_type = 'mojang'
version_type = version_name

game_args = data['minecraftArguments']
game_args = game_args.replace('${auth_player_name}', f'"{auth_player_name}"')
game_args = game_args.replace('${version_name}', f'"{version_name}"')
game_args = game_args.replace('${game_directory}', f'"{game_directory}"')
game_args = game_args.replace('${assets_index_name}', f'"{assets_index_name}"')
game_args = game_args.replace('${assets_root}', f'"{assets_root}"')
game_args = game_args.replace('${auth_uuid}', f'"{auth_uuid}"')
game_args = game_args.replace('${auth_access_token}', f'"{auth_access_token}"')
game_args = game_args.replace('${user_properties}', f'"{user_properties}"')
game_args = game_args.replace('${user_type}', f'"{user_type}"')
game_args = game_args.replace('${version_type}', f'"{version_type}"')

print()
print(f'{BLUE}print game args: {GREEN}{game_args}{RESET}')

launch_command = f'{prefix} {jvm} {jvm_opts} -Djava.library.path="{djava}" -cp "{cp}" net.minecraft.client.main.Main {game_args}'
print()
print(f'{BLUE}print launch command: {GREEN}{launch_command}{RESET}')
os.system(launch_command)
