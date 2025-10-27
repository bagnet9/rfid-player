from mfrc522 import MFRC522

reader = MFRC522()
def read(trailer_block, key, block_addrs):
    (status, TagType) = reader.Request(reader.PICC_REQIDL)
    if status != reader.MI_OK:
        return None, None
    (status, uid) = reader.Anticoll()
    if status != reader.MI_OK:
        return None, None
    id = uid
    reader.SelectTag(uid)
    status = reader.Authenticate(
        reader.PICC_AUTHENT1A, trailer_block , key, uid)
    data = []
    text_read = ''
    if status == reader.MI_OK:
        for block_num in block_addrs:
            block = reader.ReadTag(block_num)
            if block:
                data += block
        if data:
            text_read = ''.join(chr(i) for i in data)
    reader.StopAuth()
    return id, text_read

trailer_block = 11
key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
block_addrs = [8,9,10]
id, text = read(trailer_block, key, block_addrs)
while not id:
    id, text = read(trailer_block, key, block_addrs)

print(id)
print(text)