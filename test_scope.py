import os

class Config:
    IS_WINDOWS = True
    
    PRINTER = {
        "type": "windows" if IS_WINDOWS else "network"
    }

print(Config.PRINTER)
