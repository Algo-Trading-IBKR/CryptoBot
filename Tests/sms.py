from clickatell.rest import Rest
# private static string Url = "https://platform.clickatell.com/v1/message";
# private static string ApiKey = "VmGMIQOQRryF3X8Yg-iUZw==";
phone_numbers = ["32470579542"]

 
clickatell = Rest("VmGMIQOQRryF3X8Yg-iUZw==")
# balls = "balls"
# response = clickatell.sendMessage(to=['32470579542'], message=f"dab")

# try:
#     response = clickatell.sendMessage(to=['32476067619','32470579542'], message=f"dab")
# except Exception as e:
#     pass
response = clickatell.sendMessage(to=phone_numbers, message=f"test")


print("didnt crash dab")
# for entry in response: 
#     print(entry['error']) 
#     # entry['id'] 
#     # entry['destination'] 
#     # entry['error'] 
#     # entry['errorCode']