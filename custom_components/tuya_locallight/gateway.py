import tinytuya

class TuyaGateway:
    def __init__(self, gwid, address, local_key, port=6668):
        self.device = tinytuya.Device(gwid, address, local_key)
        self.device.set_version(3.3)
        self.port = port

    def get_bulb(self, did, cid):
        return tinytuya.BulbDevice(did, cid=cid, parent=self.device)
