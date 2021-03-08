# import requests


# phone_numbers = ["32470579542"]



# response = clickatell.sendMessage(to=phone_numbers, message=f"{name} sold with a profit. money left: {symbol.money}.")



from clickatell.rest import Rest

clickatell = Rest("VmGMIQOQRryF3X8Yg-iUZw==")
clickatell.sendMessage(['32470579542'], "My Message rest-PI")

# print(response) #Returns the headers with all the messages

# for entry in response['messages']:
#     print(entry) #Returns all the message details per message
#     print(entry['apiMessageId'])
#     print(entry['to'])
#     print(entry['accepted'])
#     print(entry['error'])


