import logging 

logging.basicConfig(filename="./Logs/newfile.log", format='%(asctime)s %(message)s', filemode='a') 


logger=logging.getLogger() 


logger.setLevel(logging.INFO) 

test = 103.5

logger.debug("Harmless debufg Message") 
logger.info(f"bought at {test}") 
logger.warning("Its a Warning") 
logger.error("Did you try to divide by zero") 
logger.critical("Internet is down") 