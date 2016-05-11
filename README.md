# [Audio Recognition](https://www.acrcloud.com/music-recognition) -- File Scan Tool

## Requirements

- Python 2.7
- backports.csv==1.0.1
- eyeD3==0.7.9
- requests==2.10.0

## Installation 
 
 For Windows System, you must install [Python 2](https://www.python.org/downloads/windows/) and [pip](https://pip.pypa.io/en/stable/installing/).
 
 Open your terminal and change to the script directory of <strong>acrcloud_scan_files_python-master</strong>. Then run the command: 
 
 ```
pip install -r requirements.txt
 ```
## Choose your lib
 
 [Library for Linux](https://github.com/acrcloud/acrcloud_sdk_python/blob/master/linux/x86-64/acrcloud/acrcloud_extr_tool.so?raw=true).
 
 
 [Library for Mac OSX](https://github.com/acrcloud/acrcloud_sdk_python/blob/master/mac/x86-64/acrcloud/acrcloud_extr_tool.so?raw=true).
 
 Then, copy "acrcloud_extr_tool.so" to <strong>acrcloudpysdk</strong> directory and replace the original file.
 
 

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
 
 ```
 python acrcloud_scan_files_python.py -d folder path
 python acrcloud_scan_files_python.py -f file path
 python acrcloud_scan_files_python.py -h get usage help
 ```

### Scan Folder Example:
 ```
 python acrcloud_scan_files_python.py -d ~/music
 ```
### Scan File Example: 
 ```
 python acrcloud_scan_files_python.py -f ~/testfiles/test.mp3
 ```
Default is scan folder where this script in.

The results are saved in the folder where this script in.

