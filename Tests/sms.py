from clickatell.rest import Rest
from clickatell.http import Http
# private static string Url = "https://platform.clickatell.com/v1/message";
# private static string ApiKey = "VmGMIQOQRryF3X8Yg-iUZw==";


 
clickatell = Rest("VmGMIQOQRryF3X8Yg-iUZw==");
balls = "balls"
 

try:
    response = clickatell.sendMessage(to=['32470579542'], message=f"")
except Exception as e:
    pass

print("didnt crash dab")
# for entry in response: 
#     print(entry['error']) 
#     # entry['id'] 
#     # entry['destination'] 
#     # entry['error'] 
#     # entry['errorCode']