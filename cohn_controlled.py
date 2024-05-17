import networkscan
from tutorial_modules import logger
import requests
import time
import sys
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from requests.exceptions import HTTPError
from datetime import datetime


global timestamp
global gopro_ip_list
global master

def get_password(ip_address):
    file_path = r"C:\Users\GoPro\OpenGoPro\demos\python\sdk_wireless_camera_control\open_gopro\demos\cohn_info.json"
    with open(file_path, 'r') as f:
        data = json.load(f)
    for item in data:
        if item["ip_address"] == ip_address:
            return item["password"]
    return None

def shutter_start(ip_address):
    url = "https://" + ip_address + ":443/gopro/camera/shutter/start"
    logger.info(f"starting shutter {url}")
    response = requests.get(url, auth=('gopro', get_password(ip_address)), timeout=10, verify=False)
    logger.info(f"Response: {response.text}")
    
def shutter_stop(ip_address): 
    url = "https://" + ip_address + ":443/gopro/camera/shutter/stop"
    logger.info(f"stopping shutter {url}")
    response = requests.get(url, auth=('gopro', get_password(ip_address)), timeout=10, verify=False)
    logger.info(f"Response: {response.text}")

def apply_state(pairs):
    settings,ip_address=pairs
    ext_settings(ip_address)
    for setting_id, value in settings.items():
        safe_setting_id = requests.utils.quote(setting_id, safe='')
        safe_value = requests.utils.quote(str(value), safe='')
        setting_url = f"https://{ip_address}:443/gopro/camera/setting?setting={safe_setting_id}&option={safe_value}"
        logger.info(setting_url)
        response = requests.post(setting_url, auth=('gopro', get_password(ip_address)), timeout=10, verify=False)
        logger.info(f"Response: {response.text}")


####################################################################TEST_FUNCTION################################################################################################
def apply_test(ip_address):
    ext_settings(ip_address)
    #option=3
    url = "https://" + ip_address + ":443/gopro/camera/setting?setting=134&option=3"
    logger.info(f"URL: {url}")
    get_state(ip_address)
    try:
        response = requests.get(url, auth=('gopro', get_password(ip_address)), timeout=10, verify=False)
        #response.raise_for_status() 
        logger.info(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {e}")
#################################################################################################################################################################################
        
def get_state(ip_address):
    url = "https://" + ip_address + ":443/gopro/camera/state"
    logger.info(f"getting preset status {url}")
    response = requests.get(url, auth=('gopro', get_password(ip_address)), timeout=10, verify=False)
    logger.info(f"Response: {json.dumps(response.json(), indent=4)}")
    settings = response.json()['settings']
    pairs = [(settings, x) for x in gopro_ip_list if x.split('.')[-1] != master]
    for i in range(0,1):
        with ThreadPoolExecutor() as executor:
                executor.map(apply_state, pairs)

def ext_settings(ip_address):
    url = "https://" + ip_address + ":443/gopro/camera/control/set_ui_controller?p=2"
    logger.info(f"set ext control {url}")
    response = requests.get(url, auth=('gopro', get_password(ip_address)), timeout=10, verify=False)
    logger.info(f"Response: {json.dumps(response.json(), indent=4)}") 

def gp_update(ip_address):
    url = "https://" + ip_address + ":443/gp/gpSoftUpdate"
    logger.info(f"{url}")
    response = requests.post(url, auth=('gopro', get_password(ip_address)), timeout=10, verify=False)
    logger.info(f"Response: {response.text}")

######################################################################testfunction################################################################################################
def get_setting(ip_address):
    url = "https://" + ip_address + ":443/gopro/camera/state"
    logger.info(f"getting preset status {url}")
    response = requests.get(url, auth=('gopro', get_password(ip_address)), timeout=10, verify=False)
    logger.info(f"Response: {json.dumps(response.json(), indent=4)}")
    #settings = response.json()['settings']
####################################################################################################################################################################################
    
def set_dtime(ip_address):
    now = datetime.now()
    formatted_time = now.strftime('%H_%M_%S')
    url = "https://" + ip_address + f":443/gopro/camera/set_date_time?time={formatted_time}"
    logger.info(f"setting date and time {url}")
    response = requests.get(url, auth=('gopro', get_password(ip_address)), timeout=10, verify=False) 
    logger.info(f"Response: {response.text}") 

def keep_alive(ip_address):
    logger.info("hello")
    while True:
        url = "https://" + ip_address + ":443/gopro/camera/keep_alive"
        logger.info(f"sending keep alive command {url}")
        response = requests.get(url, auth=('gopro', get_password(ip_address)), timeout=10, verify=False)


def set_mode(pairs):
    val,ip_address = pairs
    url = "https://" + ip_address + f":443/gopro/camera/presets/set_group?id={val}"
    logger.info(f"setting mode{url}")
    response = requests.get(url, auth=('gopro', get_password(ip_address)), timeout=10, verify=False)
    logger.info(f"Response: {response.text}")    

def download_lastTake(ip_address):
    url = "https://" + ip_address + ":443/gopro/media/list"
    logger.info(f"last captured details{url}")
    response = requests.get(url, auth=('gopro', get_password(ip_address)), timeout=10, verify=False)
    logger.info(f"Response: {json.dumps(response.json(), indent=4)}")
    media_list=response.json()
    url_tt="https://"+ip_address+":443/gopro/media/turbo_transfer?p=1"
    response=requests.get(url_tt,auth=('gopro', get_password(ip_address)), timeout=10, verify=False)
    logger.info(f"response: {json.dumps(response.json(), indent=4)}")
    latest_file = sorted(media_list["media"][0]["fs"], key=lambda x: x.get("dt", 0))[-1]
    url_download="https://"+ip_address+f":443/videos/DCIM/100GOPRO/{latest_file['n']}"
    with requests.get(url_download, stream=True, auth=('gopro', get_password(ip_address)), timeout=10 ,verify=False) as request:
        last_octet = ip_address.split('.')[-1]
        filename = f"{timestamp}/CAM_{last_octet}_{latest_file['n']}"
        logger.info(f"{filename}")
        with open(filename, "wb") as f:
            for chunk in request.iter_content(chunk_size=8192):
              f.write(chunk)
    url_tt="https://"+ip_address+":443/gopro/media/turbo_transfer?p=0"
    response=requests.get(url_tt,auth=('gopro', get_password(ip_address)), timeout=10, verify=False)

def download(pairs):
    x,ip_address=pairs
    url_download="https://"+ip_address+f":443/videos/DCIM/100GOPRO/{x['n']}"
    logger.info(url_download)
    #url_tt="https://"+ip_address+":443/gopro/media/turbo_transfer?p=1"
    #response=requests.get(url_tt,auth=('gopro', get_password(ip_address)), timeout=10, verify=False)
    #logger.info(f"Response: {response.text}")
    with requests.get(url_download, stream=True, auth=('gopro', get_password(ip_address)), timeout=10 ,verify=False) as request:
        last_octet = ip_address.split('.')[-1]
        filename = f"CAM_{last_octet}_{x['n']}"
        logger.info(f"{filename}")
        with open(filename, "wb") as f:
            for chunk in request.iter_content(chunk_size=8192):
                f.write(chunk)

def download_all(ip_address):
    url = "https://" + ip_address + ":443/gopro/media/list"
    logger.info(f"last captured details{url}")
    response = requests.get(url, auth=('gopro', get_password(ip_address)), timeout=10, verify=False)
    logger.info(f"Response: {json.dumps(response.json(), indent=4)}")
    media_list=response.json()
    url_tt="https://"+ip_address+":443/gopro/media/turbo_transfer?p=1"
    response=requests.get(url_tt,auth=('gopro', get_password(ip_address)), timeout=10, verify=False)
    logger.info(f"response: {json.dumps(response.json(), indent=4)}")
    pairs = [(x, ip_address) for x in media_list["media"][0]["fs"]]
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.map(download, pairs)
    url_tt="https://"+ip_address+":443/gopro/media/turbo_transfer?p=0"
    response=requests.get(url_tt,auth=('gopro', get_password(ip_address)), timeout=10, verify=False)
   
my_network = "192.168.51.0/24"
my_scan = networkscan.Networkscan(my_network)
my_scan.run()
gopro_ip_list = my_scan.list_of_hosts_found
logger.info(f"Number of connected devices: {len(gopro_ip_list)}")

while(True):
    my_scan = networkscan.Networkscan(my_network)
    my_scan.run()
    gopro_ip_list = my_scan.list_of_hosts_found
    logger.info(f"Number of connected devices: {len(gopro_ip_list)}")
    user_inp=input("1.shutter start\n2.shutter stop\n3.duplicate settings to camera\n4.download last take\n5.download all\n6.to set mode\n7.exit\n")
    if len(gopro_ip_list)==0:
        print("NO devices connected")
        sys.exit(1)
    if user_inp=='1':
        with ThreadPoolExecutor() as executor:
            executor.map(shutter_start, gopro_ip_list)
    elif user_inp=='2':
         with ThreadPoolExecutor() as executor:
            executor.map(shutter_stop, gopro_ip_list)
    elif user_inp=='3':
        master=input("enter gopro number to fetch settings from: ")
        get_state(f"192.168.51.{master}")
        #apply_test("192.168.3.4")
        # this code works only for a particular ip
    elif user_inp=='4':
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        directory_path = os.path.join(os.getcwd(), timestamp)
        os.makedirs(directory_path, exist_ok=True)
        print(f"Directory '{directory_path}' created.")
        with ThreadPoolExecutor() as executor:
            executor.map(download_lastTake, gopro_ip_list)
    elif user_inp=='5':
        with ThreadPoolExecutor() as executor:
            executor.map(download_all, gopro_ip_list)
    elif user_inp=='6':
        ch=int(input("1.photo mode\n2.video mode\n3. timelapse mode"))
        if ch==1:
            pairs=[(1001,x) for x in gopro_ip_list]
            with ThreadPoolExecutor() as executor:
                executor.map(set_mode, pairs)
        elif ch==2:
            pairs=[(1000,x) for x in gopro_ip_list]
            with ThreadPoolExecutor() as executor:
                executor.map(set_mode, pairs)
        elif ch==3:
            pairs=[(1002,x) for x in gopro_ip_list]
            with ThreadPoolExecutor() as executor:
                executor.map(set_mode, pairs) 
    elif user_inp=='8':
        gp_update("192.168.3.2")  
    elif user_inp=='7':
        sys.exit(1)
