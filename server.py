# Copyright 2024 Chris Pearson
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import asyncio
import subprocess

import websockets

import vars

"""
Populate vars.py before you run this file!
"""

print("Server starting...")

def run_k_code(client_msg):
    with open(vars.PATH_TEMP_SHEET, "w") as f:
        
        s = client_msg

        with open("mesh.ngnk", "r") as mesh_source:
            s = [*s, *mesh_source.readlines()]
        
        s = "".join(s)
        
        f.write(s)
    
    # return subprocess.check_output([PATH_NGN_K_BINARY, "tempsheet.ngnk"])
    return subprocess.run([vars.PATH_NGN_K_BINARY, vars.PATH_TEMP_SHEET],
                          capture_output=True, text=True).stdout
    # stderr=subprocess.DEVNULL, text=True).stdout

async def looper(ws, path):
    print("In loop. Loading sheet...")
    print("Sheet loaded. Entering loop to listen to client actions...")
    while True:
        msg = await ws.recv()
        print(f"< {msg}")
        
        # TODO: supress ngnk binary stdout, or redirect but still capture
        response = run_k_code(msg)
        # TODO: send bytes directly instead of converting bytes to unicode
        # then decoding on client side?
        # response = response.decode('utf-8') # or use text=True in subprocess.run
        print(f"> {response}")
        
        await ws.send(response)

start_server = websockets.serve(looper, '', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
