import logging
import jsonpickle

#Definitions

DataFormats={
    "dateTimeMessage" : logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'),
    "message": logging.Formatter('%(message)s')
}

LogFiles={
    "generalStructureLog" : "generalStructure.log",
    "runtimeDataLog" : "logData.log"
}

LogLevels={
    "generalStructure":200,
    "runTimeData":210
}

DataFormat4Log={
    "generalStructureLog" : "message",
    "runtimeDataLog" : "dateTimeMessage"
}

LogLevel4Log={
    "generalStructureLog" : "generalStructure",
    "runtimeDataLog" : "runTimeData"
}

def setup_logger(logger_name, log_file, level=logging.INFO, dataFormat=DataFormats["message"]):
    l = logging.getLogger(logger_name)
    formatter = dataFormat
    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(formatter)
    l.setLevel(level)
    l.addHandler(fileHandler)


#Initializations
for level in LogLevels.keys():
    logging.addLevelName(LogLevels[level], level)
for log in LogFiles.keys():
    setup_logger(log, LogFiles[log],LogLevels[LogLevel4Log[log]], DataFormats[DataFormat4Log[log]])


#Callable functions
def pickleObj(obj):
    jsonobject = jsonpickle.encode(obj, unpicklable=False)
    objAsStructure = jsonpickle.decode(jsonobject)
    return objAsStructure

def log_object_complete(obj, depth=0, logFile="generalStructureLog", msgType=200):
    objAsStructure=pickleObj(obj)
    __log_object_complete(objAsStructure, depth, logFile, msgType)

def log_object_custom(obj, path=[], log_customData={}, logLevel=LogLevels["runTimeData"]):
    objAsStructure=pickleObj(obj)
    __log_object_custom(objAsStructure, path, log_customData, logLevel)

def __log_object_complete(d, depth=0, logFile="generalStructureLog", msgType=LogLevels["generalStructure"]):
    logger = logging.getLogger(logFile)
    if isinstance(d, dict):
        for k,v in d.items():
            if isinstance(v, dict):
                logger.log(msgType,("  ")*depth + ("%s" % k))
                __log_object_complete(v, depth + 1, logFile, msgType)
            else:
                logger.log(msgType, "%s %s " % (("  ")*depth+k, v))
    else:
        logger.log(msgType, "%s " % (("  ") * depth + str(d)))

def __log_object_custom(d, path=[], log_customData={}, msgType=LogLevels["runTimeData"], logFile="runtimeDataLog"):
    logger = logging.getLogger(logFile)
    for k in d.keys():
        pt = list(path)
        pt.append(k)
        if k in log_customData:
            logger.log(msgType, str(pt))
            __log_object_complete(d[k], len(pt), logFile, msgType)
        if isinstance(d[k], dict):
           __log_object_custom(d[k], pt, log_customData)



