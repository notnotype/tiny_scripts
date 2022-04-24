from io import BytesIO
import os
from requests import get
from icecream import ic
from json import loads
from hashlib import sha1
from zipfile import ZipFile

DEBUG = False

temp_path = '/tmp'

version_path = 'versions'
version_name = '1.12.2'
version_json_path = f'{version_path}/{version_name}/{version_name}.json'
platform = 'linux'  # linux, windows, osx

artifacts_path = 'libraries'
native_path = f'{version_path}/{version_name}/{version_name}-{platform}'

{
    "extract": {
        "exclude": [
            "META-INF/"
        ]
    },
    "name": "com.mojang:text2speech:1.10.3",
            "natives": {
                "linux": "natives-linux",
                "windows": "natives-windows"
    },
    "downloads": {
                "classifiers": {
                    "natives-linux": {
                        "size": 7833,
                        "sha1": "ab7896aec3b3dd272b06194357f2d98f832c0cfc",
                        "path": "com/mojang/text2speech/1.10.3/text2speech-1.10.3-natives-linux.jar",
                        "url": "https://libraries.minecraft.net/com/mojang/text2speech/1.10.3/text2speech-1.10.3-natives-linux.jar"
                    },
                    "natives-windows": {
                        "size": 81217,
                        "sha1": "84a4b856389cc4f485275b1f63497a95a857a443",
                        "path": "com/mojang/text2speech/1.10.3/text2speech-1.10.3-natives-windows.jar",
                        "url": "https://libraries.minecraft.net/com/mojang/text2speech/1.10.3/text2speech-1.10.3-natives-windows.jar"
                    }
                },
                "artifact": {
                    "sha1": "48fd510879dff266c3815947de66e3d4809f8668",
                    "url": "https://libraries.minecraft.net/com/mojang/text2speech/1.10.3/text2speech-1.10.3.jar"
                }
    }
}

RED = '\033[91m'
GREEN = '\033[32m'
RESET = '\033[0m'
BLUE = '\033[94m'


def download_lib(name, url, is_native, _sha1, _size, suffix='.jar'):
    print(f'{GREEN}checkout library [{name}]{RESET}')
    if not is_native:
        package, nam, ver = name.split(':')
        filename = f'{nam}-{ver}{suffix}' 
        paths = package.split('.')
        paths.append(nam)
        paths.append(ver)

        # ic(paths)

        save_path = f'./{artifacts_path}'
        for path in paths:
            save_path = f'{save_path}/{path}'
            if not os.path.exists(save_path):
                print(f"{RED}creating path: {save_path}{RESET}")
                os.mkdir(save_path)
        save_path = f'{save_path}/{filename}'

        if DEBUG:
            ic(save_path)

        # compute sha1
        if os.path.exists(save_path):
            sha1obj = sha1()
            with open(save_path, 'rb') as f:
                sha1obj.update(f.read())
            if sha1obj.hexdigest() == _sha1:
                if DEBUG:
                    print(f'{BLUE}[{name}]{RESET} already exists')
                return save_path
            else:
                print(f'{RED}[{name}]{RESET} already exists but is different')

        # download file
        print(
            f'{BLUE}downloading [{url}] to [{save_path}] {_size/1024}KB{RESET}')
        resp = get(url)
        resp.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(resp.content)
        return save_path
    else:
        print(f'{BLUE}downloading [{url}] {_size/1024}KB{RESET}')
        resp = get(url)
        resp.raise_for_status()
        zip_file = ZipFile(BytesIO(resp.content), 'r')
        for file in zip_file.namelist():
            if file.startswith('META-INF/'):
                continue
            print(f'{BLUE}extracting [{native_path}/{file}]{RESET}')
            zip_file.extract(file, native_path)


artifact_lib_names = []
native_lib_names = []

artifact_lib_urls = []
artifact_lib_sha1 = []
artifact_lib_size = []

native_lib_urls = []
native_lib_sha1 = []
native_lib_size = []

artifact_lib_paths = []

with open(version_json_path) as f:
    data = loads(f.read())

print(f'{BLUE}total libraries: [{len(data["libraries"])}]{RESET}')

for librarie in data['libraries']:
    # print(f'parsing library: [{librarie["name"]}]')

    downloads = librarie['downloads']

    if 'classifiers' in downloads:
        if f'natives-{platform}' in downloads['classifiers']:
            _name = (librarie['name'])
            _url = downloads["classifiers"][f"natives-{platform}"]["url"]
            _sha1 = downloads["classifiers"][f"natives-{platform}"]["sha1"]
            _size = downloads["classifiers"][f"natives-{platform}"]["size"]
            download_lib(_name, _url, True, _sha1, _size)
        if 'artifact' in downloads:
            _name = librarie['name']
            _url = downloads['artifact']['url']
            _sha1 = downloads['artifact']['sha1']
            _size = downloads['artifact']['size']
            temp = download_lib(_name, _url, False, _sha1,
                                _size, '-natives-linux.jar')
            artifact_lib_paths.append(temp)
            # print(f'found artifact [{downloads["artifact"]["url"]}]')

    elif 'artifact' in downloads:
        _name = librarie['name']
        _url = downloads['artifact']['url']
        _sha1 = downloads['artifact']['sha1']
        _size = downloads['artifact']['size']
        temp = download_lib(_name, _url, False, _sha1, _size)
        artifact_lib_paths.append(temp)
        # print(f'found artifact [{downloads["artifact"]["url"]}]')
    else:
        raise RuntimeError('no artifact or classifiers')

# ic(
#     len(artifact_lib_names),
#     len(artifact_lib_urls),
#     len(artifact_lib_sha1),
#     len(artifact_lib_size),
#     len(native_lib_names),
#     len(native_lib_urls),
#     len(native_lib_sha1),
#     len(native_lib_size),
# )
# for name, url, _sha1, _size in zip(artifact_lib_names, artifact_lib_urls, artifact_lib_sha1, artifact_lib_size):
#     temp = download_lib(name, url, False, _sha1, _size)
#     artifact_lib_paths.append(temp)

# for name, url, _sha1, _size in zip(native_lib_names, native_lib_urls, native_lib_sha1, native_lib_size):
#     download_lib(name, url, True, _sha1, _size)

USE_ABS_PATH = True

jvm = 'java'
# jvm_opts = '-Xmx1024M'
jvm_opts = ''

if USE_ABS_PATH:
    djava = os.path.abspath(native_path)
else:
    djava = native_path


cp = ''
print()
print(f'{BLUE}print classpath: {RESET}')
client_path = f"./{version_path}/{version_name}/{version_name}.jar"

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
    cp = f'{cp}{temp}:'

auth_player_name = 'notnotype'
version_name = 'python mc launcher'
game_directory = os.path.abspath('.')
assets_index_name = data['assetIndex']['id']
assets_root = os.path.abspath('./assets')
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

launch_command = f'{jvm} {jvm_opts} -Djava.library.path="{djava}" -cp "{cp}" net.minecraft.client.main.Main {game_args}'
print()
print(f'{BLUE}print launch command: {GREEN}{launch_command}{RESET}')
os.popen(launch_command)
