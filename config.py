environment = "server"  # local / server

ip_config = {'server': "18.144.92.141", # this is server URL
             'local': "127.0.0.1"}

config = {"BotApplication": {
    "Backend": 5003,   # port needs to be public - 8001
    "Frontend": 5004,  # port needs to be public - 8002
    }
}
