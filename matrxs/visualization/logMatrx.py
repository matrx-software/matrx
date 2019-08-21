import logging


def setup_logger(logger_name, log_file, level=logging.INFO, formatType=0):
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    if(formatType==1):
        formatter = logging.Formatter('%(message)s')
    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(formatter)
    l.setLevel(level)
    l.addHandler(fileHandler)

logging.addLevelName(200, "MYVARIABLE")
logging.addLevelName(210, "MYVARIABLE2")
setup_logger('log1', "generalStructure.log", 200, 1)
setup_logger('log2', "logData.log", 210)
logger_1 = logging.getLogger('log1')
logger_2 = logging.getLogger('log2')

def walk_dict(d,depth=0):
    for k,v in d.items():
        if isinstance(v, dict):
            logger_1.log(200,("  ")*depth + ("%s" % k))
            walk_dict(v,depth+1)
        else:
            logger_1.log(200, "%s %s " % (("  ")*depth+k, v))
