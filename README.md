# ACRCloud Scan Files Tool

## Requirements

- Python 2.7
- backports.csv==1.0.1
- eyeD3==0.7.9
- requests==2.10.0

## Install
 
 If your system is windows you must to download Python 2,and install it.
 
 Open your Terminal then cd to the script directory.
 
 ```
    pip install -r requirements.txt
 ```
## Choose your lib
 This step is very important.
 if your system is linux,please click [here](https://github.com/acrcloud/acrcloud_sdk_python/blob/master/linux/x86-64/acrcloud/acrcloud_extr_tool.so?raw=true) to download lib
 if your system is osx, please click [here](https://github.com/acrcloud/acrcloud_sdk_python/blob/master/mac/x86-64/acrcloud/acrcloud_extr_tool.so?raw=true) to doanload lib
 
 then copy the "acrcloud_extr_tool.so" file to acrcloudpysdk to recover the original file 
 
 

## Usage: 
 
 Before you use this script,you must have acrcloud host,access_key and access_secret.
 If you haven't have these ,you can register one https://console.acrcloud.com/signup
 
 Change the content of config.json,fill in your host,access_key and access_secret
 ```
{
  "host": "ap-southeast-1.api.acrcloud.com",
  "access_key": "xxxxx",
  "access_secret": "xxxxx"
}
 ```

 ```python
    python acrcloud_scan_files_python.py path
 ```
  Example:
 ```python
    python acrcloud_scan_files_python.py ~/music
 ```

Default is scan folder where this script in.

The results are saved in the folder where this script in.

