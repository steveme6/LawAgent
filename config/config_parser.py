import configparser
def get_config(section, option):
    config = configparser.ConfigParser()
    #是相对于调用该函数的文件的路径
    config.read("../config/config.ini")
    return config.get(section, option)