from rcon.source import Client

# def handler(inp):
#     print(inp)

with Client("59.127.95.47", 36105, passwd="zxcv38994820", timeout=20) as cnt:
    cnt.run("")